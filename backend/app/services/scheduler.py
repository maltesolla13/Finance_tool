from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
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

    @app.on_event("startup")
    async def _start():
        scheduler.start()
        log.info("APScheduler gestartet (%d Jobs).", len(scheduler.get_jobs()))

    @app.on_event("shutdown")
    async def _stop():
        scheduler.shutdown()
        log.info("APScheduler gestoppt.")
