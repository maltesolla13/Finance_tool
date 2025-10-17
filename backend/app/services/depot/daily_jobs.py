from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from backend.app.database.db_handling import DBHandler
from backend.app.services.apis.market_api import fetch_low_on_or_after


def update_depotstand_for_date(run_date: datetime) -> dict:
    run_date_iso = run_date.strftime("%Y-%m-%d")
    db = DBHandler()
    written = 0
    try:
        positions = db.cursor.execute("""
            SELECT db.user_id, db.konto_id, db.securities_id,
                   SUM(db.betrag) AS sum_betrag,
                   SUM(db.anteile) AS sum_anteil
            FROM depotbewegung db
            WHERE DATE(db.datum) <= DATE(?)
            GROUP BY db.user_id, db.konto_id, db.securities_id
        """, (run_date_iso,)).fetchall()

        for pos in positions:
            sec = db.cursor.execute(
                "SELECT ticker FROM securities WHERE id=?",
                (pos["securities_id"],)
            ).fetchone()
            if not sec or not sec["ticker"]:
                continue

            low = fetch_low_on_or_after(sec["ticker"], run_date)

            wert = Decimal(str(pos["sum_anteil"])) * low
            entwicklung = wert - Decimal(str(pos["sum_betrag"]))

            db.cursor.execute("""
                DELETE FROM depotstand
                WHERE user_id = ?
                  AND konto_id = ?
                  AND securities_id = ?
                  AND DATE(datum) = DATE(?)
            """, (pos["user_id"], pos["konto_id"],
                  pos["securities_id"], run_date_iso))

            db.insert_depotstand(SimpleNamespace(
                user_id=pos["user_id"],
                konto_id=pos["konto_id"],
                securities_id=pos["securities_id"],
                summe_betrag=Decimal(str(pos["sum_betrag"])),
                summe_anteil=Decimal(str(pos["sum_anteil"])),
                wert=wert,
                entwicklung=entwicklung,
                datum=run_date_iso
            ))
            written += 1

        db.conn.commit()
        return {"written": written}
    finally:
        db.close()
