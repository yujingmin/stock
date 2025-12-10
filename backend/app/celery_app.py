"""
Celery 任务队列配置
"""
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "quant_platform",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.backtesting", "app.tasks.notifications"],
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 任务最大执行时间 1小时
    task_soft_time_limit=3300,  # 软限制 55分钟
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)
