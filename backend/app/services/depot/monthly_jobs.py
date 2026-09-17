import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
from types import SimpleNamespace
from backend.app.database.db_handling import DBHandler
from backend.app.services.depot.daily_jobs import refresh_depotstand
from backend.app.services.apis.market_api import fetch_high_on_or_after
from backend.app.services.jobs.monthly_and_depot_posting import (
    _insert_monthlycost_execution,
    _next_due_date,
    _to_date,
)

log = logging.getLogger(__name__)


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
            if not sec or not sec["ticker"] or not mc["eingangs_konto_id"]:
                skipped += 1
                continue

            due = datetime.combine(_to_date(mc["next_due"]), datetime.min.time())
            while due <= last_exec:
                due_iso = due.strftime("%Y-%m-%d")

                konto_id = mc["eingangs_konto_id"]
                existing = db.cursor.execute("""
                    SELECT d.* FROM depot_sparplan_execution e
                    JOIN depotbewegung d ON d.id=e.depotbewegung_id
                    WHERE e.monthlycost_id=? AND e.datum=?
                """, (mc["id"], due_iso)).fetchone()
                if existing:
                    amount = Decimal(str(existing["betrag"]))
                    shares = Decimal(str(existing["anteile"]))
                    skipped += 1
                else:
                    high = Decimal(str(fetch_high_on_or_after(sec["ticker"], due)))
                    if not high.is_finite() or high <= 0:
                        raise ValueError("Ungueltiger Kaufkurs fuer " + sec["ticker"])
                    if mc["anteil"] is not None:
                        shares = Decimal(str(mc["anteil"]))
                        amount = shares * high
                    else:
                        amount = Decimal(str(mc["betrag"]))
                        shares = (amount / high).quantize(
                            Decimal("0.00001"), rounding=ROUND_DOWN
                        )
                    if shares <= 0 or amount <= 0:
                        raise ValueError("Sparplanbetrag und Anteile muessen positiv sein.")
                    # Adopt a legacy execution once; equal plans remain independent.
                    legacy = db.cursor.execute("""
                        SELECT d.id FROM depotbewegung d
                        WHERE user_id IS ? AND konto_id=? AND securities_id=?
                          AND DATE(datum)=? AND LOWER(type)='sparplan'
                          AND ABS(betrag-?)<0.0001
                          AND NOT EXISTS (
                              SELECT 1 FROM depot_sparplan_execution e
                              WHERE e.depotbewegung_id=d.id
                          )
                        ORDER BY d.id LIMIT 1
                    """, (mc["user_id"], konto_id, mc["securities_id"], due_iso,
                          float(amount))).fetchone()
                    if legacy:
                        movement_id = legacy["id"]
                        skipped += 1
                    else:
                        db.insert_depotbewegung(SimpleNamespace(
                            user_id=mc["user_id"], konto_id=konto_id,
                            ausgangs_konto_id=mc["ausgangs_konto_id"],
                            eingangs_konto_id=mc["eingangs_konto_id"],
                            securities_id=mc["securities_id"],
                            kategorie_id=mc["kategorie_id"], type="Sparplan",
                            betrag=amount, anteile=shares, datum=due_iso,
                        ))
                        movement_id = db.cursor.lastrowid
                        created += 1
                    db.cursor.execute("""
                        INSERT INTO depot_sparplan_execution
                            (monthlycost_id, datum, depotbewegung_id) VALUES (?,?,?)
                    """, (mc["id"], due_iso, movement_id))

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

                db.cursor.execute("""
                    UPDATE monthlycosts_execution
                    SET status='EXECUTED', betrag=?, anteil=?
                    WHERE monthlycost_id=? AND DATE(execution_datum)=?
                """, (float(amount), float(shares), mc["id"], due_iso))

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
    except Exception:
        db.conn.rollback()
        raise
    finally:
        db.close()

    if created:
        refresh_depotstand(run_date)
    return {"created": created, "skipped": skipped}


def refresh_monthly_securities(run_date):
    """Execute due purchases after saving a plan, without failing its response."""
    try:
        return run_monthly_securities_jobs(run_date)
    except Exception:
        log.exception("Wertpapier-Sparplaene konnten nicht ausgefuehrt werden.")
        return None
