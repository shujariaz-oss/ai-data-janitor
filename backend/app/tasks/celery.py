"""Celery application configuration and task definitions."""
import os

from celery import Celery
from celery.signals import task_prerun, task_postrun

from app.utils import get_correlation_id, get_logger

logger = get_logger(__name__)

broker = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1")
backend = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2")

celery_app = Celery("data_janitor", broker=broker, backend=backend, include=["app.tasks.cleaning"])

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    worker_prefetch_multiplier=1,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
)


@task_prerun.connect
def task_prerun_handler(task_id, task, args, kwargs, **extras):
    get_correlation_id()
    logger.info("task_start", task_name=task.name, task_id=task_id)


@task_postrun.connect
def task_postrun_handler(task_id, task, retval, state, **extras):
    logger.info("task_end", task_name=task.name, task_id=task_id, state=state)
