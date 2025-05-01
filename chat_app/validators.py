import magic

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