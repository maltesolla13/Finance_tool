"""Trade budgets, execution fees and cash proceeds in EUR."""

from datetime import datetime
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

from fastapi import HTTPException

from backend.app.services.apis.market_api import (
    fetch_high_on_or_after, fetch_low_on_or_after,
)

TRADE_FEE = Decimal("1.00")


def cash_change(row):
    """Buy amounts include fees; sale amounts are gross proceeds."""
    kind = (row["type"] or "").strip().lower()
    amount = abs(Decimal(str(row["betrag"] or 0)))
    fee = Decimal(str(dict(row).get("gebuehr") or 0))
    if kind in {"kauf", "sparplan"}:
        return -amount
    if kind == "verkauf":
        return amount - fee
    return amount


def prepare_trade(conn, data, supplied, previous=None):
    """Derive executions from the entered budget or number of shares.

    Metadata edits preserve the execution. Repeated saves never subtract
    the fee from an already reduced amount or share count.
    """
    kind = (data.get("type") or "").strip().lower()
    if kind not in {"kauf", "verkauf"}:
        data["gebuehr"] = 0
        return data
    fields = ("type", "datum", "securities_id")
    changed = previous is None or any(
        str(data.get(key)) != str(previous[key]) for key in fields
    )
    if previous is not None:
        changed = changed or any(
            Decimal(str(data.get(key) or 0))
            != Decimal(str(previous[key] or 0))
            for key in ("betrag", "anteile")
        )
    if not changed:
        data["gebuehr"] = previous["gebuehr"]
        return data

    by_amount = supplied.get("betrag") is not None
    if not by_amount and supplied.get("anteile") is None:
        by_amount = data.get("betrag") is not None
    entered = data.get("betrag" if by_amount else "anteile")
    if entered is None:
        raise HTTPException(422, "Bitte Betrag oder Anteile angeben.")
    entered = Decimal(str(entered))
    if not entered.is_finite() or entered <= 0:
        raise HTTPException(422, "Betrag und Anteile müssen positiv sein.")
    if not data.get("datum"):
        raise HTTPException(422, "Bitte ein Buchungsdatum angeben.")
    security = conn.execute(
        "SELECT ticker FROM securities WHERE id=?",
        (data.get("securities_id"),),
    ).fetchone()
    if not security or not security["ticker"]:
        raise HTTPException(422, "Für dieses Wertpapier fehlt der Ticker.")
    day = datetime.fromisoformat(str(data["datum"])[:10])
    quote = fetch_low_on_or_after if kind == "kauf" else fetch_high_on_or_after
    try:
        price = Decimal(str(quote(security["ticker"], day)))
        if not price.is_finite() or price <= 0:
            raise ValueError("Invalid quote")
    except Exception as error:
        raise HTTPException(503, "Kurs konnte nicht geladen werden.") from error

    if by_amount:
        amount = entered.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        investment = amount - TRADE_FEE if kind == "kauf" else amount
        shares = (investment / price).quantize(
            Decimal("0.000001"), rounding=ROUND_DOWN
        )
    else:
        shares = entered
        amount = (shares * price).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if kind == "kauf":
            amount += TRADE_FEE
    if shares <= 0 or amount < TRADE_FEE:
        raise HTTPException(422, "Der Betrag reicht nicht für die Gebühr.")
    data.update(betrag=amount, anteile=shares, gebuehr=TRADE_FEE)
    return data
