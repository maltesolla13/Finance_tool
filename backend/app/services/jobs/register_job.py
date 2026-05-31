from backend.app.services.jobs.registry import register, JobDef
from backend.app.services.depot.jobs import (
    run_depotstand,
    run_monthly_securities
)
import backend.app.services.jobs.monthly_and_depot_posting_jobs  # noqa: F401

register(JobDef(
    name="depot.depotstand.run",
    fn=run_depotstand,
    cron="30 23 * * *",   # miute Stude Tag Woche Jahr
    description="Täglicher Depotstand"
))

register(JobDef(
    name="depot.monthly_securities.run",
    fn=run_monthly_securities,
    cron="30 23 * * *",
    description="Monatliche Wertpapier-Käufe aus MonthlyCosts"
))
