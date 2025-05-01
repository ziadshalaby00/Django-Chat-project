# chat/consumers.py
import time, json, os, subprocess, tempfile
from django.core.files.base import ContentFile
import magic

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chat, Message
from .serializers import *
from django.core.files.base import ContentFile

class ChatConsumerMes(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.user = self.scope["user"]
        self.type = None
        self.file_name = None
        
        if self.user is None or self.user.is_anonymous:
            await self.close()
            return

        # تحقق أن المستخدم جزء من المحادثة
        if not await self.is_user_in_chat(self.chat_id, self.user):
            await self.close()
            return

        self.room_group_name = f'chat_{self.chat_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['data']))

    @database_sync_to_async
    def is_user_in_chat(self, chat_id, user):
        try:
            chat = Chat.objects.get(id=chat_id)
            return user == chat.user1 or user == chat.user2
        except Chat.DoesNotExist:
            return False
            
    @database_sync_to_async
    def save_message(self, chat_id, user, content):
        chat = Chat.objects.get(id=chat_id)
        return Message.objects.create(
            chat=chat, 
            sender=user, 
            content=content, 
            type='message'
        )
        
    def reset(self):
        self.type = None
        self.file_name = None
        
    async def receive(self, text_data=None, bytes_data=None):
        obj = None

        if text_data:
            data = json.loads(text_data)
            type = data.get('type', None)
            print(type)
            
            if type == 'message':
                message = data.get('message', None)
                if message:
                    obj = await self.save_message(self.chat_id, self.user, message)
                    
            elif type == 'audio':
                self.type = 'audio'

            elif type == 'file':
                self.type = 'file'
                self.file_name = data.get('file_name', None)
                
        elif bytes_data and self.type == 'audio':
            print('inside audio', self.type)
            try:
                obj = await self.save_audio(self.chat_id, self.user, bytes_data)
            except Exception as e:
                self.reset()
                return

        elif bytes_data and self.type == 'file' and self.file_name:
            print('inside file', self.file_name)
            error = validate_file_upload(bytes_data)
            if error:
                print(error)
                self.reset()
                return
            
            obj = await self.save_file(self.chat_id, self.user, bytes_data, self.file_name)
            
        if obj:
            serialized_data = MessageSerializer(obj).data
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'data': serialized_data,
                }
            )
            
            self.reset()
        
    @database_sync_to_async
    def save_audio(self, chat_id, user, raw_audio):
        try:
            # فحص نوع الملف باستخدام python-magic
            mime_type = magic.from_buffer(raw_audio, mime=True)
            if mime_type != "video/webm":
                raise ValueError("Invalid file type. Only webm audio is accepted.")
        
            # إنشاء ملف مؤقت بصيغة webm
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_input:
                temp_input.write(raw_audio)
                temp_input.flush()
                input_path = temp_input.name

            # إعداد مسار ملف الإخراج المؤقت بصيغة mp3
            output_path = input_path.replace(".webm", ".mp3")

            # استخدام ffmpeg لتحويل الملف إلى mp3
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", input_path,
                    "-codec:a", "libmp3lame",
                    "-qscale:a", "5",  # جودة متوسطة (من 0 إلى 9، 0 أفضل جودة)
                    output_path
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # قراءة محتوى ملف mp3
            with open(output_path, "rb") as f:
                mp3_data = f.read()

            # إنشاء اسم الملف النهائي
            filename = f"{user.id}_{chat_id}_{int(time.time())}.mp3"

            # حفظ الرسالة والملف
            message = Message.objects.create(
                chat_id=chat_id,
                sender=user,
                type='audio'
            )
            message.audio_file.save(filename, ContentFile(mp3_data))

            return message

        finally:
            # تنظيف الملفات المؤقتة
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
                
    @database_sync_to_async
    def save_file(self, chat_id, user, raw_file, filename):
        print('inside save file', filename)
        # تحديد اسم الملف الكامل (مثلاً: 123_5_1714300000_document.pdf)
        base, ext = os.path.splitext(filename)
        final_filename = f"{user.id}_{chat_id}_{int(time.time())}_{base}{ext}"

        # إنشاء الرسالة في قاعدة البيانات
        message = Message.objects.create(
            chat_id=chat_id,
            sender=user,
            type='file',
        )

        # حفظ الملف نفسه
        message.file.save(final_filename, ContentFile(raw_file))
        return message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.group_name = 'chat_updates'

        if self.user is None or self.user.is_anonymous:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.group_name, 
            self.channel_name
        )
        
        await self.accept()

        # إرسال المحادثات الخاصة بالمستخدم
        chats = await self.get_user_chats()
        await self.send(text_data=json.dumps({
            'type': 'initial_chats',
            'chats': chats
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name, 
            self.channel_name
        )

    async def receive(self, text_data):
        pass

    async def chat_created(self, event):
        chat = event['chat']

        # تحقق هل المستخدم ضمن هذه المحادثة
        if chat['user1'] == self.user.id or chat['user2'] == self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'chat_created',
                'chat': chat
            }))

    @database_sync_to_async
    def get_user_chats(self):
        chats = (Chat.objects.filter(user1=self.user) | Chat.objects.filter(user2=self.user)).order_by('-created_at')
        serializer = ChatSerializer(chats, many=True)
        print(serializer.data)
        return serializer.data



MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# قائمة MIME types المقبولة
ALLOWED_MIME_TYPES = [
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml", "image/bmp",
    "application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint", "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain", "application/vnd.oasis.opendocument.text",
    "audio/mpeg", "audio/wav", "audio/ogg", "audio/x-m4a", "audio/aac", "audio/flac",
    "video/mp4", "video/x-matroska", "video/quicktime", "video/x-msvideo", "video/webm", "video/x-flv",
    "application/zip", "application/x-rar-compressed", "application/x-7z-compressed", "application/x-tar", "application/gzip",
    "text/x-python", "application/javascript", "text/html", "text/css", "application/json", "application/xml", "text/csv"
]

def validate_file_upload(bytes_data: bytes) -> str | None:
    if len(bytes_data) > MAX_FILE_SIZE:
        return "File too large (max 50MB)"
    
    # تحقق من نوع الملف الحقيقي
    mime = magic.Magic(mime=True)
    file_mime_type = mime.from_buffer(bytes_data)

    if file_mime_type not in ALLOWED_MIME_TYPES:
        return f"File MIME type '{file_mime_type}' is not allowed"
    
    return None