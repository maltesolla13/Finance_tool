from datetime import datetime
from decimal import Decimal, ROUND_DOWN
from types import SimpleNamespace
from calendar import monthrange
from backend.app.database.db_handling import DBHandler
from backend.app.services.apis.market_api import fetch_high_on_or_after


def _add_one_month(d: datetime) -> datetime:
    y, m = d.year, d.month
    y2, m2 = (y + (m//12), ((m % 12) + 1))
    day = min(d.day, monthrange(y2, m2)[1])
    return d.replace(year=y2, month=m2, day=day)


def run_monthly_securities_jobs(run_date: datetime) -> dict:
    run_date_iso = run_date.strftime("%Y-%m-%d")
    db = DBHandler()
    created = 0
    skipped = 0
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

            high = fetch_high_on_or_after(
                sec["ticker"], datetime.fromisoformat(mc["next_due"])
            )

            if mc["anteil"] is not None:
                shares = Decimal(str(mc["anteil"]))
                amount = shares * high
            else:
                amount = Decimal(str(mc["betrag"]))
                shares = (amount / high).quantize(Decimal("0.00001"),
                                                  rounding=ROUND_DOWN)

            konto_id = mc["eingangs_konto_id"] or mc["ausgangs_konto_id"]

            existed = db.cursor.execute("""
                SELECT 1 FROM depotbewegung
                WHERE user_id = ?
                AND konto_id = ?
                AND securities_id = ?
                AND DATE(datum) = DATE(?)
                AND ABS(betrag - ?) < 0.0001
            """, (mc["user_id"], konto_id, mc["securities_id"],
                  run_date_iso, float(amount))).fetchone()

            if existed:
                skipped += 1
            else:
                db.insert_depotbewegung(SimpleNamespace(
                    user_id=mc["user_id"],
                    konto_id=konto_id,
                    securities_id=mc["securities_id"],
                    kategorie_id=mc["kategorie_id"],
                    type_id=None,
                    betrag=amount,
                    anteile=shares,
                    datum=run_date_iso
                ))
                created += 1

            next_due = _add_one_month(datetime.fromisoformat(mc["next_due"]))
            db.cursor.execute(
                "UPDATE monthlycosts SET next_due=? WHERE id=?",
                (next_due.strftime("%Y-%m-%d"), mc["id"])
            )

        db.conn.commit()
        return {"created": created, "skipped": skipped}
    finally:
        db.close()
