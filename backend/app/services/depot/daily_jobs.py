"""Build daily positions without locking the database during price requests."""

import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from threading import RLock

from backend.app.database.db_handling import DBHandler
from backend.app.services.apis.market_api import fetch_daily_lows_eur

log = logging.getLogger(__name__)
_rebuild_lock = RLock()
POSITION_TYPES = {"kauf": 1, "sparplan": 1, "verkauf": -1}


def _depot_delta(row):
    sign = POSITION_TYPES.get((row["type"] or "").strip().lower(), 0)
    return (
        sign * abs(Decimal(str(row["anteile"] or 0))),
        sign * abs(Decimal(str(row["betrag"] or 0))),
    )


def _read_transactions(conn):
    return [dict(row) for row in conn.execute("""
        SELECT d.id, d.user_id, d.konto_id, d.securities_id,
               DATE(d.datum) AS day, d.type, d.betrag, d.anteile, s.ticker
        FROM depotbewegung d
        LEFT JOIN securities s ON s.id = d.securities_id
        ORDER BY d.id
    """)]


def _daily_positions(transactions, end_date):
    groups = defaultdict(lambda: defaultdict(lambda: [Decimal(0), Decimal(0)]))
    tickers = {}
    for row in transactions:
        if (row["type"] or "").strip().lower() not in POSITION_TYPES:
            continue
        day = date.fromisoformat(row["day"])
        if day > end_date:
            continue
        key = (row["user_id"], row["konto_id"], row["securities_id"])
        shares, amount = _depot_delta(row)
        groups[key][day][0] += shares
        groups[key][day][1] += amount
        tickers[row["securities_id"]] = row["ticker"]

    positions = []
    price_ranges = {}
    for (user_id, account_id, security_id), events in groups.items():
        shares, invested = Decimal(0), Decimal(0)
        day = min(events)
        while day <= end_date:
            delta_shares, delta_amount = events.get(
                day, (Decimal(0), Decimal(0))
            )
            shares += delta_shares
            invested += delta_amount
            positions.append((
                user_id, account_id, security_id, day, shares, invested
            ))
            if shares:
                ticker = tickers[security_id]
                if not ticker:
                    raise ValueError(
                        f"Kein Ticker fuer Wertpapier {security_id}."
                    )
                first, last = price_ranges.get(ticker, (day, day))
                price_ranges[ticker] = (min(first, day), max(last, day))
            day += timedelta(days=1)

    prices = {
        ticker: fetch_daily_lows_eur(ticker, first, last)
        for ticker, (first, last) in price_ranges.items()
    }
    rows = []
    for user_id, account_id, security_id, day, shares, invested in positions:
        price = Decimal(0)
        if shares:
            price = Decimal(str(prices[tickers[security_id]][day]))
            if not price.is_finite() or price <= 0:
                raise ValueError(
                    f"Ungueltiger Kurs fuer {tickers[security_id]} am {day}."
                )
        value = shares * price
        rows.append((
            user_id, account_id, security_id, float(invested), float(shares),
            float(value), float(value - invested), day.isoformat(),
        ))
    return rows


def ensure_depotstand_from_last(run_date: date | datetime) -> dict:
    """Persist one row per user/account/security/calendar day.

    Include zero holdings.
    Rebuilds repair backdated edits, moved transactions and deleted positions.
    Price errors leave the previous snapshot intact. Concurrent source changes
    trigger a fresh read before the atomic replacement.
    """
    end_date = run_date.date() if isinstance(run_date, datetime) else run_date
    with _rebuild_lock:
        for _ in range(3):
            db = DBHandler()
            try:
                transactions = _read_transactions(db.conn)
            finally:
                db.close()

            rows = _daily_positions(transactions, end_date)
            db = DBHandler()
            try:
                db.conn.execute("BEGIN IMMEDIATE")
                if _read_transactions(db.conn) != transactions:
                    db.conn.rollback()
                    continue
                db.cursor.execute(
                    "DELETE FROM depotstand WHERE DATE(datum) <= ?",
                    (end_date.isoformat(),)
                )
                db.cursor.executemany("""
                    INSERT INTO depotstand (
                        user_id, konto_id, securities_id, summe_betrag,
                        summe_anteil, wert, entwicklung, datum
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, rows)
                db.conn.commit()
                return {
                    "written": len(rows),
                    "from": min((row[-1] for row in rows), default=None),
                    "to": end_date.isoformat(),
                    "mode": "daily-rebuild",
                }
            except Exception:
                db.conn.rollback()
                raise
            finally:
                db.close()
    raise RuntimeError(
        "Depotbewegungen wurden waehrend der Bewertung mehrfach geaendert."
    )


def refresh_depotstand(run_date):
    """Keep saved bookings successful even when their price refresh fails."""
    try:
        return ensure_depotstand_from_last(run_date)
    except Exception:
        log.exception(
            "Depotbewertung fehlgeschlagen; "
            "bisherige Tageswerte bleiben erhalten."
        )
        return None
