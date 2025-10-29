import magic

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# قائمة MIME types المقبولة
ALLOWED_MIME_TYPES = [
    # الصور
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml", "image/bmp",
    
    # مستندات
    "application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint", "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain", "application/vnd.oasis.opendocument.text",
    
    # الصوتيات
    "audio/mpeg", "audio/wav", "audio/ogg", "audio/x-m4a", "audio/aac", "audio/flac",
    
    # الفيديوهات
    "video/mp4", "video/x-matroska", "video/quicktime", "video/x-msvideo", "video/webm", "video/x-flv",
    
    # ملفات مضغوطة
    "application/zip", "application/x-rar", "application/x-rar-compressed", "application/x-7z-compressed", "application/x-tar", "application/gzip",
    
    # ملفات كود
    "text/x-python", "application/javascript", "text/html", "text/css", "application/json", "application/xml", "text/csv",
    
    # ملفات exe بأنواع مختلفة
    "application/vnd.microsoft.portable-executable",
    "application/x-msdownload",
    "application/x-dosexec"
]

def validate_file_upload(bytes_data: bytes) -> str | None:
    if len(bytes_data) > MAX_FILE_SIZE:
        return "File too large (max 50MB)"
    
    mime = magic.Magic(mime=True)
    file_mime_type = mime.from_buffer(bytes_data)

    if file_mime_type not in ALLOWED_MIME_TYPES:
        return f"File MIME type '{file_mime_type}' is not allowed"
    
    return None