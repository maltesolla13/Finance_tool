from backend.app.services.depot.monthly_jobs import run_monthly_securities_jobs
from backend.app.services.depot.daily_jobs import update_depotstand_for_date
from datetime import datetime
from zoneinfo import ZoneInfo
tz = ZoneInfo("Europe/Berlin")


def run_depotstand(date: str | None = None):
    run_date = datetime.fromisoformat(date) if date else datetime.now(tz)
    return update_depotstand_for_date(run_date)


def run_monthly_securities(date: str | None = None):
    run_date = datetime.fromisoformat(date) if date else datetime.now(tz)
    return run_monthly_securities_jobs(run_date)
