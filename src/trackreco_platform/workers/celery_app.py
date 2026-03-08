from celery import Celery

from trackreco_platform.config import settings

celery_app = Celery("trackreco", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_track_started = True
