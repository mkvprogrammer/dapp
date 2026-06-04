"""Celery worker для фоновых задач."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery("unidapp", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
celery_app.autodiscover_tasks(["app.tasks"])

celery_app.conf.beat_schedule = {
    "cleanup-stale-auctions-hourly": {
        "task": "app.tasks.maintenance.mark_expired_auctions_closed",
        "schedule": crontab(minute=0),
    },
}
