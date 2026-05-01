import magic

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

ALLOWED_MIME_TYPES = [
    # Images
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml", "image/bmp",

    # Documents
    "application/pdf", "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain", "application/vnd.oasis.opendocument.text",

    # Audio
    "audio/mpeg", "audio/wav", "audio/ogg", "audio/x-m4a", "audio/aac", "audio/flac",

    # Video
    "video/mp4", "video/x-matroska", "video/quicktime",
    "video/x-msvideo", "video/webm", "video/x-flv",

    # Archives / Compressed
    "application/zip", "application/x-rar", "application/x-rar-compressed",
    "application/x-7z-compressed", "application/x-tar", "application/gzip",

    # Code files
    "text/x-python", "application/javascript", "text/html",
    "text/css", "application/json", "application/xml", "text/csv",

    # EXE (commented out for security)
    # "application/vnd.microsoft.portable-executable",
    # "application/x-msdownload",
    # "application/x-dosexec",

    # ==========================
    # ADDITIONAL ENTRIES
    # ==========================

    # Additional images
    "image/tiff", "image/x-icon", "image/heic", "image/heif",

    # Additional documents
    "application/rtf", "application/vnd.oasis.opendocument.spreadsheet",
    "application/vnd.oasis.opendocument.presentation",
    "application/epub+zip",

    # Additional audio
    "audio/webm", "audio/mp4", "audio/x-wav",

    # Additional video
    "video/ogg", "video/3gpp", "video/3gpp2", "video/x-ms-wmv",

    # Additional archives
    "application/x-bzip2", "application/x-lzip", "application/x-xz",
    "application/x-compressed-tar", "application/x-gzip",

    # Additional code files
    "text/x-java-source", "text/x-c", "text/x-c++", "text/x-shellscript",
    "application/x-php", "text/x-script.python", "text/markdown",
    "application/sql", "text/yaml", "text/x-log",

    # Fonts
    "font/ttf", "font/otf", "font/woff", "font/woff2",

    # 3D Models / CAD
    "model/stl", "application/sla",
]


def validate_file_upload(file) -> str | None:
    """  
    file: Django UploadedFile object  
    """
    if file.size > MAX_FILE_SIZE:
        return f"File too large (max {MAX_FILE_SIZE/(1024 * 1024)}MB)"

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
            return "Zip file too large and may be unsafe (max 30MB)"

    return None
