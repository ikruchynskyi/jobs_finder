"""
Celery Worker Configuration
"""
from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    'job_automation',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_max_tasks_per_child=50,
    worker_prefetch_multiplier=1,
)

# Import tasks
from app.services.crawler import start_crawler_job
from app.services.applicator import apply_to_job_task

# Register tasks
@celery_app.task(name='crawl_jobs')
def crawl_jobs_task(crawler_job_id, search_query, location, source):
    """Celery task for crawling jobs"""
    return start_crawler_job(crawler_job_id, search_query, location, source)


@celery_app.task(name='apply_to_job')
def apply_to_job_celery_task(application_id, user_id, job_id):
    """Celery task for applying to jobs"""
    return apply_to_job_task(application_id, user_id, job_id)
