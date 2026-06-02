from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
from types import SimpleNamespace
from calendar import monthrange
from backend.app.database.db_handling import DBHandler
from backend.app.services.apis.market_api import fetch_high_on_or_after
from backend.app.services.jobs.monthly_and_depot_posting import (
    _insert_monthlycost_execution,
    _next_due_date,
    _to_date,
)


def _add_one_month(d: datetime) -> datetime:
    y, m = d.year, d.month
    y2, m2 = (y + (m // 12), ((m % 12) + 1))
    day = min(d.day, monthrange(y2, m2)[1])
    return d.replace(year=y2, month=m2, day=day)


def _last_executable_day(now: datetime) -> datetime:
    cutoff = now.replace(hour=22, minute=0, second=0, microsecond=0)
    last_day = now.date() if now >= cutoff else (
        now - timedelta(days=1)).date()
    return datetime.combine(last_day, datetime.min.time())


def run_monthly_securities_jobs(run_date: datetime) -> dict:
    run_date_iso = run_date.strftime("%Y-%m-%d")
    last_exec = _last_executable_day(run_date)

    db = DBHandler()
    created, skipped = 0, 0
    try:
        rows = db.cursor.execute("""
            SELECT mc.* FROM monthlycosts mc
            WHERE mc.active = 1
              AND mc.securities_id IS NOT NULL
              AND DATE(mc.next_due) <= DATE(?)
        """, (run_date_iso,)).fetchall()

        for mc in rows:
            sec = db.cursor.execute(
                "SELECT id, ticker FROM securities WHERE id=?",
                (mc["securities_id"],)
            ).fetchone()
            if not sec or not sec["ticker"]:
                skipped += 1
                continue

            due = datetime.fromisoformat(mc["next_due"])
            while due <= last_exec:
                due_iso = due.strftime("%Y-%m-%d")

                # konservativer Kaufpreis = Tageshoch
                high = Decimal(str(fetch_high_on_or_after(sec["ticker"], due)))

                if mc["anteil"] is not None:
                    shares = Decimal(str(mc["anteil"]))
                    amount = shares * high
                else:
                    amount = Decimal(str(mc["betrag"]))
                    shares = (amount / high).quantize(Decimal("0.00001"),
                                                      rounding=ROUND_DOWN)

                konto_id = mc["eingangs_konto_id"]
                if not konto_id:
                    skipped += 1
                    continue

                existed = db.cursor.execute("""
                    SELECT 1 FROM depotbewegung
                    WHERE user_id = ? AND konto_id = ? AND securities_id = ?
                      AND DATE(datum) = DATE(?) AND ABS(betrag - ?) < 0.0001
                """, (mc["user_id"], konto_id, mc["securities_id"], due_iso,
                      float(amount))).fetchone()

                if existed:
                    skipped += 1
                else:
                    db.insert_depotbewegung(SimpleNamespace(
                        user_id=mc["user_id"],
                        konto_id=konto_id,
                        ausgangs_konto_id=mc["ausgangs_konto_id"],
                        eingangs_konto_id=mc["eingangs_konto_id"],
                        securities_id=mc["securities_id"],
                        kategorie_id=mc["kategorie_id"],
                        type="Sparplan",
                        betrag=amount,
                        anteile=shares,
                        datum=due_iso
                    ))
                    created += 1

                _insert_monthlycost_execution(
                    db,
                    monthlycost_id=mc["id"],
                    user_id=mc["user_id"],
                    name=mc["name"],
                    betrag=amount,
                    anteil=shares,
                    securities_id=mc["securities_id"],
                    kategorie_id=mc["kategorie_id"],
                    ausgangs_konto_id=mc["ausgangs_konto_id"],
                    eingangs_konto_id=mc["eingangs_konto_id"],
                    execution_datum=due.date(),
                )

                due = datetime.combine(
                    _next_due_date(
                        due.date(),
                        mc["repeat_type"],
                        mc["custom_interval"],
                        mc["custom_unit"],
                        _to_date(mc["start_datum"]).day,
                    ),
                    datetime.min.time(),
                )

            # next_due auf die erste noch NICHT gebuchte Fälligkeit setzen
            db.cursor.execute(
                "UPDATE monthlycosts SET next_due=? WHERE id=?",
                (due.strftime("%Y-%m-%d"), mc["id"])
            )

        db.conn.commit()
        return {"created": created, "skipped": skipped}
    finally:
        db.close()
