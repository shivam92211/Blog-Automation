"""
Job scheduler using APScheduler
Manages scheduled jobs for topic generation and blog publishing
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import pytz

from config import settings
from config.logging_config import get_logger
from app.jobs import run_topic_generation, run_blog_publishing

logger = get_logger(__name__)


class JobScheduler:
    """Manages scheduled jobs"""

    def __init__(self):
        self.scheduler = BackgroundScheduler(
            timezone=pytz.timezone(settings.TIMEZONE)
        )
        self._setup_event_listeners()

    def _setup_event_listeners(self):
        """Setup listeners for job events"""

        def job_executed(event):
            logger.info(
                f"Job executed successfully: {event.job_id}",
                extra={"job_id": event.job_id}
            )

        def job_error(event):
            logger.error(
                f"Job failed: {event.job_id} - {event.exception}",
                extra={
                    "job_id": event.job_id,
                    "exception": str(event.exception)
                }
            )

        self.scheduler.add_listener(job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(job_error, EVENT_JOB_ERROR)

    def add_topic_generation_job(self):
        """
        Add weekly topic generation job
        Runs every Monday at 6:00 AM
        """
        logger.info("Adding topic generation job...")

        trigger = CronTrigger(
            day_of_week=settings.TOPIC_GENERATION_SCHEDULE["day_of_week"],
            hour=settings.TOPIC_GENERATION_SCHEDULE["hour"],
            minute=settings.TOPIC_GENERATION_SCHEDULE["minute"],
            timezone=settings.TIMEZONE
        )

        self.scheduler.add_job(
            func=run_topic_generation,
            trigger=trigger,
            id="topic_generation",
            name="Weekly Topic Generation",
            replace_existing=True,
            max_instances=1,  # Don't run multiple instances concurrently
            misfire_grace_time=3600  # Allow 1 hour grace period for missed jobs
        )

        logger.info(
            f"✓ Topic generation job scheduled: "
            f"Every {settings.TOPIC_GENERATION_SCHEDULE['day_of_week']} "
            f"at {settings.TOPIC_GENERATION_SCHEDULE['hour']:02d}:"
            f"{settings.TOPIC_GENERATION_SCHEDULE['minute']:02d}"
        )

    def add_blog_publishing_job(self):
        """
        Add daily blog publishing job
        Runs every day at 9:00 AM
        """
        logger.info("Adding blog publishing job...")

        trigger = CronTrigger(
            hour=settings.BLOG_PUBLISHING_SCHEDULE["hour"],
            minute=settings.BLOG_PUBLISHING_SCHEDULE["minute"],
            timezone=settings.TIMEZONE
        )

        self.scheduler.add_job(
            func=run_blog_publishing,
            trigger=trigger,
            id="blog_publishing",
            name="Daily Blog Publishing",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=3600
        )

        logger.info(
            f"✓ Blog publishing job scheduled: "
            f"Every day at {settings.BLOG_PUBLISHING_SCHEDULE['hour']:02d}:"
            f"{settings.BLOG_PUBLISHING_SCHEDULE['minute']:02d}"
        )

    def start(self):
        """Start the scheduler"""
        if settings.ENABLE_SCHEDULER:
            logger.info("Starting job scheduler...")
            self.scheduler.start()
            logger.info("✓ Scheduler started")
            self._print_scheduled_jobs()
        else:
            logger.info("Scheduler disabled by configuration")

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            logger.info("Stopping scheduler...")
            self.scheduler.shutdown(wait=True)
            logger.info("✓ Scheduler stopped")

    def _print_scheduled_jobs(self):
        """Print all scheduled jobs"""
        jobs = self.scheduler.get_jobs()
        logger.info(f"Scheduled jobs ({len(jobs)}):")
        for job in jobs:
            logger.info(f"  - {job.name} (ID: {job.id})")
            logger.info(f"    Next run: {job.next_run_time}")

    def run_job_now(self, job_id: str):
        """
        Manually trigger a job to run immediately

        Args:
            job_id: Job ID ("topic_generation" or "blog_publishing")
        """
        logger.info(f"Manually triggering job: {job_id}")
        job = self.scheduler.get_job(job_id)

        if not job:
            raise ValueError(f"Job not found: {job_id}")

        job.modify(next_run_time=None)  # Run immediately
        logger.info(f"✓ Job {job_id} will run immediately")

    def get_job_info(self, job_id: str):
        """Get information about a scheduled job"""
        job = self.scheduler.get_job(job_id)
        if not job:
            return None

        return {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        }


# Singleton instance
job_scheduler = JobScheduler()


def setup_scheduler():
    """
    Setup and start the scheduler
    Called when application starts
    """
    job_scheduler.add_topic_generation_job()
    job_scheduler.add_blog_publishing_job()
    job_scheduler.start()


def shutdown_scheduler():
    """
    Shutdown the scheduler gracefully
    Called when application stops
    """
    job_scheduler.stop()
