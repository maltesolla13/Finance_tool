from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo
from backend.app.services.jobs.registry import all_jobs

tz = ZoneInfo("Europe/Berlin")


def install_jobs(app):
    scheduler = AsyncIOScheduler(timezone=tz)

    # Wichtig: Dieses Import triggert die Registrierungen.
    import backend.app.services.jobs.register_job  # noqa: F401

    for job in all_jobs().values():
        if job.cron:
            minute, hour, day, month, dow = job.cron.split()
            trigger = CronTrigger(minute=minute, hour=hour, day=day,
                                  month=month, day_of_week=dow, timezone=tz)
            scheduler.add_job(lambda j=job: j.fn(None),
                              trigger, id=job.name, name=job.description,
                              max_instances=1, coalesce=True,
                              misfire_grace_time=3600)

    @app.on_event("startup")
    async def _start():
        scheduler.start()

    @app.on_event("shutdown")
    async def _stop():
        scheduler.shutdown()
