from backend.app.services.jobs.registry import register, JobDef
from backend.app.services.depot.jobs import (
    run_depotstand,
    run_monthly_securities
)

register(JobDef(
    name="depot.depotstand.run",
    fn=run_depotstand,
    cron="30 23 * * *",
    description="Täglicher Depotstand"
))

register(JobDef(
    name="depot.monthly_securities.run",
    fn=run_monthly_securities,
    cron="0 8 1 * *",
    description="Monatliche Wertpapier-Käufe aus MonthlyCosts"
))
