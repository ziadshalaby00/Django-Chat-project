import magic

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

ALLOWED_MIME_TYPES = [
    # الصور
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml", "image/bmp",

    # مستندات
    "application/pdf", "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain", "application/vnd.oasis.opendocument.text",

    # الصوتيات
    "audio/mpeg", "audio/wav", "audio/ogg", "audio/x-m4a", "audio/aac", "audio/flac",

    # الفيديوهات
    "video/mp4", "video/x-matroska", "video/quicktime",
    "video/x-msvideo", "video/webm", "video/x-flv",

    # مضغوط
    "application/zip", "application/x-rar", "application/x-rar-compressed",
    "application/x-7z-compressed", "application/x-tar", "application/gzip",

    # كود
    "text/x-python", "application/javascript", "text/html",
    "text/css", "application/json", "application/xml", "text/csv",

    # EXE
    "application/vnd.microsoft.portable-executable",
    "application/x-msdownload",
    "application/x-dosexec",
]


def validate_file_upload(file) -> str | None:
    """  
    file: Django UploadedFile object  
    """
    if file.size > MAX_FILE_SIZE:
        return "File too large (max 50MB)"

    try:
        header = file.read(2048)
        file.seek(0)
    except Exception:
        return "Could not read file"

    try:
        mime = magic.Magic(mime=True)
        detected_mime = mime.from_buffer(header)
    except Exception:
        return "Unable to detect file type"

    if detected_mime not in ALLOWED_MIME_TYPES:
        return f"File MIME type '{detected_mime}' is not allowed"

    if detected_mime == "application/zip":
        if file.size > 30 * 1024 * 1024:  # 30MB
            return "Zip file too large and may be unsafe"

    return None
