from datetime import datetime
from zoneinfo import ZoneInfo
import logging

from backend.app.services.jobs.registry import JobDef, register
from backend.app.services.jobs.monthly_and_depot_posting import (
    mirror_depotbewegung_to_kontobewegung,
    run_monthlycosts_for_date,
)

tz = ZoneInfo("Europe/Berlin")
log = logging.getLogger("jobs")


def job_monthlycosts(_ctx):
    today = datetime.now(tz).date()
    log.info("[monthlycosts:book] Starte fuer %s", today.isoformat())
    run_monthlycosts_for_date(today)
    log.info("[monthlycosts:book] Fertig.")


def job_depot_mirror(_ctx):
    log.info("[depotbewegung:mirror] Starte Spiegelung.")
    mirror_depotbewegung_to_kontobewegung()
    log.info("[depotbewegung:mirror] Fertig.")


register(JobDef(
    name="monthlycosts:book",
    fn=job_monthlycosts,
    cron="0 5 * * *",  # taeglich 05:00 Europa/Berlin
    description="Bucht faellige MonthlyCosts und rotiert next_due",
))

register(JobDef(
    name="depotbewegung:mirror",
    fn=job_depot_mirror,
    cron="15 5 * * *",  # taeglich 05:15 Europa/Berlin
    description="Spiegelt Depotbewegungen in Kontobewegung",
))
