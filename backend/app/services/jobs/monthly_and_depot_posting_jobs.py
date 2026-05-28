from datetime import datetime
from zoneinfo import ZoneInfo
import logging

from backend.app.services.jobs.registry import register  # <- nutzt dein bestehendes Registry-Interface
from backend.app.services.jobs.monthly_and_depot_posting import (
    run_monthlycosts_for_date,
    mirror_depotbewegung_to_kontobewegung,
)

tz = ZoneInfo("Europe/Berlin")
log = logging.getLogger("jobs")

@register(
    name="monthlycosts:book",
    description="Bucht fällige MonthlyCosts in Kontobewegung und rotiert next_due",
    cron="0 5 * * *",  # täglich 05:00 Europa/Berlin
)
def job_monthlycosts(_ctx):
    today = datetime.now(tz).date()
    log.info("[monthlycosts:book] Starte für %s", today.isoformat())
    run_monthlycosts_for_date(today)
    log.info("[monthlycosts:book] Fertig.")

@register(
    name="depotbewegung:mirror",
    description="Spiegelt Depotbewegungen in Kontobewegung (Kauf->-, Verkauf->+ ohne 'Depot'-Addon)",
    cron="15 5 * * *",  # täglich 05:15 Europa/Berlin (kurz nach MonthlyCosts)
)
def job_depot_mirror(_ctx):
    # Idempotent – kann ohne Datum laufen. Wenn du nur 'heute' willst:
    # mirror_depotbewegung_to_kontobewegung(only_for_date=datetime.now(tz).date())
    log.info("[depotbewegung:mirror] Starte Spiegelung.")
    mirror_depotbewegung_to_kontobewegung()
    log.info("[depotbewegung:mirror] Fertig.")