# Proton Chat

A real-time messaging web application built with Django and WebSockets. Users can create chats, exchange text/audio/file messages, reply to messages, and receive instant notifications.

## Features

- **Real-time messaging** via WebSockets (Django Channels)
- **JWT cookie-based authentication** with refresh token rotation
- **Google OAuth 2.0** login
- **Message types**: Text, Audio (auto-converted to MP3), Files (validated types, 5MB limit)
- **Reply to messages** with threaded context
- **Soft delete**: Chats and user accounts are hidden, not destroyed
- **Read receipts** & unread counters
- **Email-based password reset**
- **Profile management** with image upload

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.2, Django REST Framework |
| Real-time | Django Channels, Daphne, WebSockets |
| Auth | SimpleJWT (cookie-based), Google OAuth2 |
| Database | SQLite |
| Media | Pillow, python-magic, mutagen, ffmpeg |
| Security | CORS headers, CSRF middleware, django-cleanup |

## Project Structure

```
├── auth_app/        # Users, JWT auth, Google login, password reset
├── chat/            # Chat rooms, participants, unread counts
├── message/         # Base message model, WebSocket consumers, pagination
├── text_message/    # Text content CRUD
├── audio_message/   # Audio upload & MP3 conversion
├── file_message/    # File upload with MIME validation
└── core/            # Settings, ASGI/WSGI, WebSocket auth middleware
```
