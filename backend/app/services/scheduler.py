from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from backend.app.services.jobs.registry import all_jobs
import logging

tz = ZoneInfo("Europe/Berlin")
log = logging.getLogger("scheduler")


def install_jobs(app):
    scheduler = AsyncIOScheduler(timezone=tz)

    # Triggert die Registrierungen (services/jobs/register_job.py)
    import backend.app.services.jobs.register_job  # noqa: F401

    for job in all_jobs().values():
        try:
            if job.cron:
                trigger = CronTrigger.from_crontab(job.cron, timezone=tz)
                scheduler.add_job(
                    lambda j=job: j.fn(None),
                    trigger,
                    id=job.name,
                    name=job.description,
                    max_instances=1,
                    coalesce=True,
                    misfire_grace_time=3600,
                )
            else:
                log.warning("Job ohne Cron wird übersprungen: %s", job.name)
        except Exception as e:
            log.exception("Fehler beim Registrieren von %s: %s", job.name, e)

    scheduler.start()
    run_at = datetime.now(tz) + timedelta(seconds=3)
    for job in all_jobs().values():
        scheduler.add_job(
            lambda j=job: j.fn(None),
            DateTrigger(run_date=run_at, timezone=tz),
            id=f"{job.name}:startup",
            name=f"{job.description} (Startup)",
            max_instances=1,
            replace_existing=True,
        )
    app.state.scheduler = scheduler
    log.info("APScheduler gestartet (%d Jobs).", len(scheduler.get_jobs()))
    return scheduler
