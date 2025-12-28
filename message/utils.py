def can_send_message(sender, chat):
    """
    Check if the sender can send a message in this chat.

    Returns:
        (True, "") if allowed
        (False, reason) if not allowed
    """
    
    # تحديد المستلم
    receiver = chat.user2 if sender == chat.user1 else chat.user1
    
    if not receiver.is_active:
        return False, "Cannot send message. The recipient's account is deactivated."

    # تحقق من أن المستلم لم يحذف الشات أو حسابه غير مفعل
    if (receiver == chat.user1 and chat.user1_deleted_chat) or \
       (receiver == chat.user2 and chat.user2_deleted_chat):
        return False, "Cannot send message. The recipient has deleted the chat."


    return True, ""

from django.shortcuts import get_object_or_404
from message.models import Message
from chat.models import Chat

def get_reply_to_message(user, chat: Chat, reply_to_id: int):
    if not chat.participants.filter(user=user).exists():
        raise PermissionError("User not a participant in this chat.")
    
    if not reply_to_id:
        return None

    return get_object_or_404(Message, id=reply_to_id, chat=chat)

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from message.serializers import MessageSerializer

def send_new_message_notification(message):
    """
    Send the message data to the chat group and notify the receiver.
    Works for any message type (text, file, audio).
    """
    chat = message.chat
    participants = chat.participants.exclude(user=message.sender)

    # Serialize message
    message_data = MessageSerializer(message).data

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"chat_{chat.id}",
        {
            "type": "send_message",
            "message_data": message_data
        }
    )

    for participant in participants:
        async_to_sync(channel_layer.group_send)(
            f"user_{participant.user.id}",
            {"type": "new_message_notification"}
        )

    return message_data