from celery import Celery
from core.config import settings

# Initialize Celery app with Redis broker and backend
celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

# Auto-discover tasks from the tasks module
celery_app.autodiscover_tasks(["app.tasks"], force=True)
