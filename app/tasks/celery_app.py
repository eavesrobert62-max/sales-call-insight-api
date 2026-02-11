from celery import Celery
import os
from app.core.config import settings

# Use Railway's Redis URL or fallback to settings
redis_url = os.getenv("REDIS_URL") or getattr(settings, 'redis_url', None) or getattr(settings, 'celery_broker_url', 'redis://localhost:6379/0')

celery_app = Celery(
    "sales_insights",
    broker=redis_url,
    backend=redis_url,
    include=["app.tasks.celery_tasks"]
)

# Get timeout from settings or default
timeout = getattr(settings, 'processing_timeout_seconds', 120)

# Configure Celery for Railway
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=timeout,
    task_soft_time_limit=timeout - 10,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    result_expires=3600,
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    task_acks_late=True,
    worker_cancel_long_running_tasks_on_connection_close=True,
)
