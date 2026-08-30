# core/celery.py

import os

from celery import Celery

from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.beat_schedule = {
    "cleanup-expired-blacklisted-tokens-every-hour": {
        "task": "auth_app.tasks.cleanup_expired_blacklisted_tokens_task",
        "schedule": crontab(minute=0),
    },
}