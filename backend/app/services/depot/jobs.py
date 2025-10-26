from backend.app.services.depot.monthly_jobs import run_monthly_securities_jobs
from backend.app.services.depot.daily_jobs import ensure_depotstand_from_last
from datetime import datetime
from zoneinfo import ZoneInfo
tz = ZoneInfo("Europe/Berlin")


def run_depotstand(date: str | None = None):
    run_date = datetime.fromisoformat(date) if date else datetime.now(tz)
    return ensure_depotstand_from_last(run_date)


def run_monthly_securities(date: str | None = None):
    run_date = datetime.fromisoformat(date) if date else datetime.now(tz)
    return run_monthly_securities_jobs(run_date)
