from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException


def account_overview(conn, account_id, today=None):
    """Read-only cash ledger, including sources not yet mirrored by jobs."""
    today = today or date.today()
    account = conn.execute(
        "SELECT id, name FROM konten WHERE id=?", (account_id,)
    ).fetchone()
    if account is None:
        raise HTTPException(404, "Konto nicht gefunden.")
    users = {
        r["id"]: r["name"] for r in conn.execute("SELECT id, name FROM user")
    }
    categories = {
        r["id"]: r["name"]
        for r in conn.execute("SELECT id, name FROM kategorien")
    }
    securities = {
        r["id"]: r["name"]
        for r in conn.execute("SELECT id, name FROM securities")
    }
    transactions = []

    def add(source, row, amount, name, kind, cash=None):
        transactions.append({
            "id": f"{source}:{row['id']}", "date": str(row["datum"])[:10],
            "name": name, "type": kind, "user_id": row["user_id"],
            "user": users.get(row["user_id"], ""),
            "category": categories.get(row.get("kategorie_id"), ""),
            "amount": Decimal(str(amount or 0)),
            "cash_change": Decimal(str(amount if cash is None else cash)),
        })

    movements = [dict(r) for r in conn.execute(
        "SELECT * FROM kontobewegung WHERE konto_id=?", (account_id,)
    )]
    for row in movements:
        add("movement", row, row["betrag"], row["name"], row["type"])
    for record in conn.execute(
        "SELECT * FROM receipt WHERE konto_id=?", (account_id,)
    ):
        row = dict(record)
        add("receipt", row, -abs(row["betrag"] or 0), row["name"], "Einkauf")

    depot_rows = [dict(r) for r in conn.execute("""
        SELECT * FROM depotbewegung
        WHERE konto_id=? OR ausgangs_konto_id=? OR eingangs_konto_id=?
    """, (account_id, account_id, account_id))]
    for row in depot_rows:
        side = (row["type"] or "").strip().lower()
        if side in {"kauf", "sparplan"}:
            cash_account = row["ausgangs_konto_id"] or row["konto_id"]
            amount = -abs(row["betrag"] or 0)
            label = (
                "Wertpapier Kauf" if side == "kauf" else "Wertpapier Sparplan"
            )
        elif side in {
            "verkauf", "dividende", "ausschüttung", "ertrag", "coupon"
        }:
            cash_account = row["eingangs_konto_id"] or row["konto_id"]
            amount = abs(row["betrag"] or 0)
            label = (
                "Wertpapier Verkauf"
                if side == "verkauf" else "Wertpapier Ertrag"
            )
        else:
            cash_account = (
                row["eingangs_konto_id"]
                or row["ausgangs_konto_id"]
                or row["konto_id"]
            )
            amount = float(row["betrag"] or 0)
            label = "Wertpapier " + (row["type"] or "Bewegung")
        marker = f"AUTO: depot#{row['id']} {side}"
        mirrored = any(
            m["name"] == marker
            and str(m["datum"])[:10] == str(row["datum"])[:10]
            for m in movements
        )
        if cash_account == account_id and mirrored:
            continue
        if cash_account == account_id or row["konto_id"] == account_id:
            security_name = securities.get(
                row["securities_id"], row["securities_id"]
            )
            add("depot", row, amount,
                f"{row['type']}: {security_name}",
                label, amount if cash_account == account_id else 0)

    # Executed transfers may not yet be mirrored.
    # Planned/failed jobs are not bookings.
    for record in conn.execute("""
        SELECT * FROM monthlycosts_execution
        WHERE status='EXECUTED'
          AND (ausgangs_konto_id=? OR eingangs_konto_id=?)
    """, (account_id, account_id)):
        row = dict(record)
        row["datum"] = row["execution_datum"]
        day = str(row["datum"])[:10]
        for direction, field, sign in (("Ausgang", "ausgangs_konto_id", -1),
                                       ("Eingang", "eingangs_konto_id", 1)):
            if (
                row[field] != account_id
                or (row["securities_id"] and sign == 1)
            ):
                continue
            marker = f"AUTO: monthlycost#{row['monthlycost_id']} "
            if any(m["name"].startswith(marker) and direction in m["name"]
                   and str(m["datum"])[:10] == day for m in movements):
                continue
            if row["securities_id"] and any(
                d["securities_id"] == row["securities_id"]
                and d["user_id"] == row["user_id"]
                and str(d["datum"])[:10] == day
                and d["ausgangs_konto_id"] == account_id
                for d in depot_rows
            ):
                continue
            add(
                "monthly-" + direction, row, sign * abs(row["betrag"] or 0),
                row["name"], "Dauerauftrag"
            )

    # Stored balances are end-of-day checkpoints for the corresponding
    # user's share.
    checkpoints = [dict(r) for r in conn.execute(
        "SELECT * FROM kontostand WHERE konto_id=? ORDER BY datum, id",
        (account_id,)
    )]
    events = [(r["date"], 0, index, r) for index, r in enumerate(transactions)]
    events += [(str(r["datum"])[:10], 1, r["id"], r) for r in checkpoints]
    events.sort(key=lambda item: item[:3])
    balances = defaultdict(Decimal)
    history = {}
    current = Decimal(0)
    income = Decimal(0)
    expenses = Decimal(0)
    for day, checkpoint, _, row in events:
        if checkpoint:
            balances[row["user_id"]] = Decimal(str(row["kontostand"]))
        else:
            balances[row["user_id"]] += row["cash_change"]
            row["balance"] = float(sum(balances.values()))
            row["future"] = day > today.isoformat()
            if not row["future"]:
                income += max(Decimal(0), row["cash_change"])
                expenses += min(Decimal(0), row["cash_change"])
        if day <= today.isoformat():
            current = sum(balances.values())
            history[day] = float(current)
    if history:
        first = date.fromisoformat(min(history)) - timedelta(days=1)
        history[first.isoformat()] = 0.0
    history[today.isoformat()] = float(current)
    order = {row["id"]: index for index, row in enumerate(transactions)}
    transactions.sort(
        key=lambda row: (row["date"], order[row["id"]]), reverse=True
    )
    for row in transactions:
        row["amount"] = float(row["amount"])
        row["cash_change"] = float(row["cash_change"])
    portfolio = _portfolio_values(conn, account_id, today, history)
    return {
        "account": dict(account), "balance": float(current),
        "income": float(income), "expenses": float(expenses),
        "as_of": today.isoformat(),
        "has_checkpoints": bool(checkpoints),
        "history": [
            {"date": day, "balance": history[day]} for day in sorted(history)
        ],
        "transactions": transactions,
        **portfolio,
    }


def _portfolio_values(conn, account_id, today, cash_history):
    """Compose account history from persisted daily valuations.

    No pricing in GET.
    """
    snapshots = conn.execute("""
        SELECT user_id, securities_id, DATE(datum) AS day, wert
        FROM depotstand WHERE konto_id=? AND DATE(datum)<=?
        ORDER BY DATE(datum), id
    """, (account_id, today.isoformat())).fetchall()
    has_portfolio = bool(snapshots) or conn.execute("""
        SELECT 1 FROM depotbewegung WHERE konto_id=?
        AND LOWER(TRIM(type)) IN ('kauf', 'verkauf', 'sparplan') LIMIT 1
    """, (account_id,)).fetchone() is not None
    by_day = defaultdict(list)
    for row in snapshots:
        by_day[row["day"]].append(row)
    current_positions = {}
    cash = 0.0
    value_history = []
    first = min([*cash_history, *by_day], default=today.isoformat())
    day = date.fromisoformat(first)
    while day <= today:
        key = day.isoformat()
        cash = cash_history.get(key, cash)
        for row in by_day.get(key, []):
            current_positions[(row["user_id"], row["securities_id"])] = (
                Decimal(str(row["wert"]))
            )
        portfolio_value = sum(current_positions.values(), Decimal(0))
        value_history.append({
            "date": key,
            "balance": float(Decimal(str(cash)) + portfolio_value)
        })
        day += timedelta(days=1)
    portfolio_value = float(sum(current_positions.values(), Decimal(0)))
    valuation_date = max(by_day, default=None)
    purchases = Decimal(0)
    valued_returns = Decimal(0)
    for row in conn.execute("""
        SELECT LOWER(TRIM(type)) AS kind, betrag, DATE(datum) AS day
        FROM depotbewegung WHERE konto_id=? AND DATE(datum)<=?
    """, (account_id, today.isoformat())):
        amount = abs(Decimal(str(row["betrag"] or 0)))
        if row["kind"] in {"kauf", "sparplan"}:
            purchases += amount
            change = -amount
        elif row["kind"] in {
            "verkauf", "dividende", "ausschüttung", "ertrag", "coupon"
        }:
            change = amount
        else:
            continue
        # Match cash flows to the date of the stored portfolio valuation.
        if valuation_date and row["day"] <= valuation_date:
            valued_returns += change
    return {
        "has_portfolio": has_portfolio,
        "portfolio_value": portfolio_value,
        "purchase_value": float(purchases),
        "portfolio_profit": (
            float(sum(current_positions.values(), valued_returns))
            if valuation_date else None
        ),
        "total_value": cash + portfolio_value,
        "valuation_date": valuation_date,
        "value_history": value_history,
    }
