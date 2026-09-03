# 📱 Proton — Real-Time Chat & Video Calling

A real-time messaging web application built with Django and WebSockets. Users can create chats, exchange text/audio/file messages, reply to messages, calling system, and receive instant notifications.

## 📌 Features

### 🔐 Authentication & Security
- **JWT cookie-based authentication** with refresh token rotation
- **Google OAuth 2.0** login support
- **Secure cookies** with HttpOnly, Secure, and SameSite attributes
- **CSRF protection** middleware with exempt URL patterns
- **Email verification** for new accounts and email changes
- **Password reset** via email with secure tokens
- **Soft delete** for user accounts (anonymized & deactivated)
- **Session management** with token blacklisting

### 💬 Messaging System
- **Real-time messaging** via WebSockets (Django Channels)
- **Three message types**: Text, Audio, File
- **Reply to messages** with threaded context
- **Read receipts** with unread counters
- **Message pagination** (15 messages per page)
- **Message editing** for text messages
- **Message deletion** with real-time updates

### 📞 Video & Voice Calling
- **WebRTC signaling** via WebSockets (Django Channels)
- Events: `call.offer`, `call.answer`, `call.ice_candidate`, `call.reject`, `call.end`
- Real‑time relay to the target user using dedicated user groups
- Backend ready for both one‑to‑one audio and video calls
- Frontend implementation required to handle peer‑connection and media streams

### 📁 File Handling
- **Audio messages**: WebM to MP3 conversion via FFmpeg
- **Audio validation**: MIME type check, 5MB limit, duration limits
- **File messages**: MIME-based validation, 5MB limit, extensive allowed types
- **Image upload** for user profiles
- **Automatic media cleanup** with django-cleanup

### 👥 Chat Management
- **Direct chats** between two users
- **Chat creation** with duplicate detection
- **Soft delete** for chats (per-user basis)
- **Unread count** calculation per chat
- **Recent chats** sorting by latest message

### 🔔 Notifications
- **WebSocket events** for new messages, chat creation, message updates
- **Typing indicators** support (infrastructure ready)
- **Call signaling** support (WebRTC ready)
- **Real-time chat list updates**

### 👤 Profile Management
- User profile with image upload
- Bio, full name, username editing
- Email change with verification flow
- Account deletion with anonymization

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Django 5.2, Django REST Framework |
| **Real-time** | Django Channels, Daphne, WebSockets |
| **Authentication** | SimpleJWT (cookie-based), Google OAuth2 |
| **Database** | SQLite (PostgreSQL ready) |
| **Task Queue** | Celery, Redis |
| **Media Processing** | Pillow, python-magic, mutagen, FFmpeg |
| **Email** | SMTP (Gmail) |
| **Admin** | django-unfold (modern UI) |
| **Security** | CORS headers, CSRF middleware |
| **Documentation** | drf-spectacular (OpenAPI) |

---

## 📁 Project Structure

```
ziadshalaby00-django-chat-project/
├── auth_app/                 # Authentication, users, JWT, OAuth
│   ├── views/
│   │   ├── auth.py          # Login, register, logout, token refresh
│   │   ├── google.py        # Google OAuth 2.0
│   │   ├── password.py      # Password reset
│   │   ├── email.py         # Email verification
│   │   ├── profile.py       # Profile management
│   │   ├── account.py       # Account deletion
│   │   └── csrf.py          # CSRF token endpoint
│   ├── models.py            # Custom User model
│   ├── serializers.py       # User serializers
│   ├── authentication.py    # Cookie-based JWT + CSRF middleware
│   ├── send_email.py        # Email templating
│   ├── tasks.py             # Celery tasks (email, image download, cleanup)
│   └── validators.py        # Strong password validation
│
├── chat/                    # Chat rooms and participants
│   ├── models.py            # Chat, ChatParticipant models
│   ├── serializers.py       # Chat serializers with unread counts
│   ├── views.py             # CRUD operations, mark read, user search
│   ├── chat_consumers.py    # WebSocket consumer for chat events
│   └── utils.py             # Helper functions
│
├── message/                  # Base message model
│   ├── models.py            # Message model (polymorphic)
│   ├── serializers.py       # Message serializers with replies
│   ├── views.py             # List messages with pagination, delete
│   ├── chat_message_consumers.py  # WebSocket consumer for messages
│   └── utils.py             # Broadcast helpers
│
├── text_message/             # Text message implementation
│   ├── models.py            # TextMessage model (1:1 with Message)
│   ├── views.py             # Create, update text messages
│   └── serializers.py       # Text message serializer
│
├── audio_message/            # Audio message implementation
│   ├── models.py            # AudioMessage model
│   ├── views.py             # Upload, FFmpeg conversion to MP3
│   ├── serializers.py       # Audio message serializer
│   └── validators.py        # Audio validation
│
├── file_message/             # File message implementation
│   ├── models.py            # FileMessage model
│   ├── views.py             # Upload with MIME validation
│   ├── serializers.py       # File message serializer
│   └── validators.py        # File type/size validation
│
├── core/                     # Project configuration
│   ├── settings.py          # Django settings
│   ├── asgi.py              # ASGI configuration (WebSocket)
│   ├── wsgi.py              # WSGI configuration
│   ├── urls.py              # URL routing
│   ├── celery.py            # Celery configuration
│   └── websocke_auth.py     # WebSocket authentication middleware
│
├── static/                   # Static files (admin customization)
│   └── unfold/              # Django-unfold custom CSS/JS
│
├── templates/
│   └── welcome.html         # Welcome page (admin/visitor roles)
│
├── manage.py
├── requirements.txt
├── populate_messages.py      # Script to populate test messages
└── .env                     # Environment variables
```

---

## 🔌 API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register new user |
| POST | `/api/auth/login/` | Login with JWT (cookies) |
| POST | `/api/auth/google-login/` | Google OAuth login |
| POST | `/api/auth/token/refresh/` | Refresh JWT tokens |
| POST | `/api/auth/token/verify/` | Verify access token |
| POST | `/api/auth/logout/` | Logout and blacklist token |
| GET | `/api/auth/get_csrf/` | Get CSRF token |

### Password Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/password-reset-link/` | Send reset link |
| POST | `/api/auth/password-reset-confirm/` | Confirm password reset |

### Email Verification

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/verify-email/` | Verify email with token |
| POST | `/api/auth/change-email/` | Request email change |
| POST | `/api/auth/resend-verification-email/` | Resend verification |

### Profile

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/auth/me/` | Get current user profile |
| PATCH | `/api/auth/update-profile/` | Update profile |
| DELETE | `/api/auth/delete-user-image/` | Delete profile image |
| POST | `/api/auth/delete-user/` | Delete account |
| GET | `/api/auth/users-profile/<id>/` | Get user by ID |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/chat/chats/` | List chats (latest first) |
| POST | `/api/chat/chats/` | Create new chat |
| DELETE | `/api/chat/chats/delete/<chat_id>/` | Soft delete chat |
| POST | `/api/chat/mark-read/<chat_id>/` | Mark messages as read |
| GET | `/api/chat/get-user-by-username/?username=` | Search user by username |

### Messages

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/message/<chat_id>/messages/` | List messages (paginated) |
| DELETE | `/api/message/delete/<message_id>/` | Delete message |

### Text Messages

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/text_message/<chat_id>/send-text-message/` | Send text message |
| PATCH | `/api/text_message/<text_message_id>/update-text-message/` | Update text message |

### Audio Messages

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/audio_message/<chat_id>/uplode-audio/` | Upload audio (WebM → MP3) |

### File Messages

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/file_message/<chat_id>/uplode-file/` | Upload file |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `ws/chats/` | User-level notifications (chat creation, new message alerts) |
| `ws/chat_messages/<chat_id>/` | Real-time messages, updates, deletions |

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ziadshalaby00-django-chat-project
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create `.env` File

```env
SECRET_KEY=your-django-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

FRONTEND_URL=http://localhost:4200

# Celery (Redis)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Optional: PostgreSQL
# POSTGRES_DB=your_db
# POSTGRES_USER=your_user
# POSTGRES_PASSWORD=your_password
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
```

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Run Development Servers

**Django Server (HTTP):**
```bash
python manage.py runserver
```

**Celery Worker (Background Tasks):**
```bash
celery -A core worker --loglevel=info
```

**Celery Beat (Scheduled Tasks):**
```bash
celery -A core beat --loglevel=info
```

### 8. (Optional) Populate Test Data

```bash
# Set environment variables for test files
export POPULATE_IMAGE_PATH=/path/to/test/image.jpg
export POPULATE_AUDIO_PATH=/path/to/test/audio.webm

python populate_messages.py
```

---

## 📄 License

Developed entirely by [Ziad Shalaby](https://github.com/ziadshalaby00).

This project is licensed under the **MIT License**.

---

## 🙌 Acknowledgements

- [Django](https://www.djangoproject.com/) - Web framework
- [Django Channels](https://channels.readthedocs.io/) - WebSocket support
- [Django REST Framework](https://www.django-rest-framework.org/) - API layer
- [django-unfold](https://github.com/lincolnloop/django-unfold) - Modern admin theme
- [SimpleJWT](https://django-rest-framework-simplejwt.readthedocs.io/) - JWT authentication
- [Celery](https://docs.celeryq.dev/) - Task queue
- [FFmpeg](https://ffmpeg.org/) - Audio conversion
- [python-magic](https://github.com/ahupp/python-magic) - MIME detection
- [Pillow](https://python-pillow.org/) - Image processing
- [Mutagen](https://mutagen.readthedocs.io/) - Audio metadata
