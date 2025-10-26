from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from collections import defaultdict
from backend.app.database.db_handling import DBHandler
from backend.app.services.apis.market_api import fetch_low_on_or_before


def ensure_depotstand_from_last(run_date: datetime) -> dict:
    """
    Füllt depotstand inkrementell:
    - Für jede (user,konto,security) ab dem Tag NACH dem letzten Depotstand-
      Eintrag, bis einschließlich run_date (Datumsteil).
    - Falls es noch keinen Depotstand gibt, ab dem ersten Bewegungsdatum.
    - Kumuliert Anteile/Beträge und schreibt pro Tag genau eine Zeile.
    """
    end_date = datetime(run_date.year, run_date.month, run_date.day).date()
    db = DBHandler()
    written = 0
    try:
        # 1) Bewegungen pro Tag (damit wir pro Tag kumulierte Zuwächse kennen)
        tx = db.cursor.execute("""
            SELECT user_id, konto_id, securities_id,
                   date(datum) AS d,
                   SUM(betrag)  AS betrag,
                   SUM(anteile) AS anteile
            FROM depotbewegung
            GROUP BY user_id, konto_id, securities_id, date(datum)
            ORDER BY user_id, konto_id, securities_id, d
        """).fetchall()
        if not tx:
            return {"written": 0, "from": None, "to": end_date.isoformat()}

        # 2) Letzten Depotstand je Gruppe holen (Datum + Summen als Startwerte)
        last_rows = db.cursor.execute("""
            SELECT ds.user_id, ds.konto_id, ds.securities_id,
                   date(ds.datum) AS last_d,
                   ds.summe_betrag, ds.summe_anteil
            FROM depotstand ds
            JOIN (
                SELECT user_id, konto_id, securities_id, MAX(date(datum)) AS
                maxd FROM depotstand
                GROUP BY user_id, konto_id, securities_id
            ) m
            ON m.user_id = ds.user_id
           AND m.konto_id = ds.konto_id
           AND m.securities_id = ds.securities_id
           AND date(ds.datum) = m.maxd
        """).fetchall()
        last_map = {
            (r["user_id"], r["konto_id"], r["securities_id"]): (
                datetime.fromisoformat(r["last_d"]).date(),
                Decimal(str(r["summe_betrag"])),
                Decimal(str(r["summe_anteil"])),
            )
            for r in last_rows
        }

        # 3) Bewegungen in Speicher gruppieren
        groups = defaultdict(list)  # key -> [(date, betrag, anteile), ...]
        sec_ids = set()
        min_date_global = None
        for r in tx:
            key = (r["user_id"], r["konto_id"], r["securities_id"])
            d = datetime.fromisoformat(r["d"]).date()
            betrag = Decimal(str(r["betrag"] or 0))
            anteile = Decimal(str(r["anteile"] or 0))
            groups[key].append((d, betrag, anteile))
            sec_ids.add(r["securities_id"])
            if min_date_global is None or d < min_date_global:
                min_date_global = d

        # 4) Ticker-Lookup
        tickers = {}
        if sec_ids:
            qmarks = ",".join("?" * len(sec_ids))
            for r in db.cursor.execute(
                f"SELECT id, ticker FROM securities WHERE id IN ({qmarks})",
                tuple(sec_ids)
            ).fetchall():
                tickers[r["id"]] = r["ticker"]

        # 5) Kurs-Cache
        price_cache: dict[tuple[str, str], Decimal] = {}

        # 6) Pro Gruppe von "start" bis end_date auffüllen
        for key, moves in groups.items():
            user_id, konto_id, sec_id = key
            if not tickers.get(sec_id):
                continue

            # Startbedingungen: ab Tag nach letztem Depotstand oder ab Kauf
            if key in last_map:
                last_d, sum_betrag, sum_anteil = last_map[key]
                start_date = (last_d + timedelta(days=1))
            else:
                sum_betrag = Decimal("0")
                sum_anteil = Decimal("0")
                start_date = moves[0][0]  # erstes Bewegungsdatum

            if start_date > end_date:
                continue

            # Bewegungsindex auf den ersten Tag >= start_date vorspulen
            i = 0
            while i < len(moves) and moves[i][0] < start_date:
                # Diese Tage sind bereits in last_map enthalten
                # (oder irrelevant), daher nicht nochmal addieren.
                i += 1

            d = start_date
            ticker = tickers[sec_id]
            while d <= end_date:
                # Bewegungen des Tages d addieren (falls vorhanden)
                while i < len(moves) and moves[i][0] == d:
                    sum_betrag += moves[i][1]
                    sum_anteil += moves[i][2]
                    i += 1

                # Wenn noch keine Position vorhanden, heute nichts schreiben
                if sum_anteil == 0:
                    d += timedelta(days=1)
                    continue

                day_iso = d.isoformat()
                pc_key = (ticker, day_iso)
                if pc_key in price_cache:
                    low = price_cache[pc_key]
                else:
                    low = Decimal(str(fetch_low_on_or_before(
                        ticker, datetime(d.year, d.month, d.day))))
                    price_cache[pc_key] = low

                wert = sum_anteil * low
                entwicklung = wert - sum_betrag

                # Optional: bei Unique-Index reicht INSERT OR REPLACE,
                # sonst DELETE + INSERT
                db.cursor.execute("""
                    DELETE FROM depotstand
                    WHERE user_id=? AND konto_id=? AND securities_id=?
                                  AND DATE(datum)=DATE(?)
                """, (user_id, konto_id, sec_id, day_iso))

                db.insert_depotstand(SimpleNamespace(
                    user_id=user_id,
                    konto_id=konto_id,
                    securities_id=sec_id,
                    summe_betrag=sum_betrag,
                    summe_anteil=sum_anteil,
                    wert=wert,
                    entwicklung=entwicklung,
                    datum=day_iso,
                ))
                written += 1
                d += timedelta(days=1)

        db.conn.commit()
        return {
            "written": written,
            "from": (min_date_global or end_date).isoformat(),
            "to": end_date.isoformat(),
            "mode": "from_last",
        }
    finally:
        db.close()
