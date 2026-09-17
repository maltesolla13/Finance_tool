from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException


def account_overview(conn, account_id, today=None):
    """Read-only cash ledger, including sources not yet mirrored by jobs."""
    today = today or date.today()
    account = conn.execute("SELECT id, name FROM konten WHERE id=?", (account_id,)).fetchone()
    if account is None:
        raise HTTPException(404, "Konto nicht gefunden.")
    users = {r["id"]: r["name"] for r in conn.execute("SELECT id, name FROM user")}
    categories = {r["id"]: r["name"] for r in conn.execute("SELECT id, name FROM kategorien")}
    securities = {r["id"]: r["name"] for r in conn.execute("SELECT id, name FROM securities")}
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
    for record in conn.execute("SELECT * FROM receipt WHERE konto_id=?", (account_id,)):
        row = dict(record)
        add("receipt", row, -abs(row["betrag"] or 0), row["name"], "Einkauf")

    depot_rows = [dict(r) for r in conn.execute("""
        SELECT * FROM depotbewegung
        WHERE konto_id=? OR ausgangs_konto_id=? OR eingangs_konto_id=?
    """, (account_id, account_id, account_id))]
    for row in depot_rows:
        side = (row["type"] or "").lower()
        if side not in {"kauf", "verkauf"}:
            continue
        cash_account = row["ausgangs_konto_id"] if side == "kauf" else row["eingangs_konto_id"]
        cash_account = cash_account or row["konto_id"]
        amount = abs(row["betrag"] or 0) * (-1 if side == "kauf" else 1)
        marker = f"AUTO: depot#{row['id']} {side}"
        mirrored = any(m["name"] == marker and str(m["datum"])[:10] == str(row["datum"])[:10]
                       for m in movements)
        if cash_account == account_id and mirrored:
            continue
        if cash_account == account_id or row["konto_id"] == account_id:
            add("depot", row, amount,
                f"{row['type']}: {securities.get(row['securities_id'], row['securities_id'])}",
                "Wertpapier " + row["type"], amount if cash_account == account_id else 0)

    # Executed transfers may not yet be mirrored. Planned/failed jobs are not bookings.
    for record in conn.execute("""
        SELECT * FROM monthlycosts_execution
        WHERE status='EXECUTED' AND (ausgangs_konto_id=? OR eingangs_konto_id=?)
    """, (account_id, account_id)):
        row = dict(record)
        row["datum"] = row["execution_datum"]
        day = str(row["datum"])[:10]
        for direction, field, sign in (("Ausgang", "ausgangs_konto_id", -1),
                                       ("Eingang", "eingangs_konto_id", 1)):
            if row[field] != account_id or (row["securities_id"] and sign == 1):
                continue
            marker = f"AUTO: monthlycost#{row['monthlycost_id']} "
            if any(m["name"].startswith(marker) and direction in m["name"]
                   and str(m["datum"])[:10] == day for m in movements):
                continue
            if row["securities_id"] and any(
                d["securities_id"] == row["securities_id"] and d["user_id"] == row["user_id"]
                and str(d["datum"])[:10] == day and d["ausgangs_konto_id"] == account_id
                for d in depot_rows
            ):
                continue
            add("monthly-" + direction, row, sign * abs(row["betrag"] or 0), row["name"], "Dauerauftrag")

    # Stored balances are end-of-day checkpoints for the corresponding user's share.
    checkpoints = [dict(r) for r in conn.execute(
        "SELECT * FROM kontostand WHERE konto_id=? ORDER BY datum, id", (account_id,)
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
    transactions.sort(key=lambda row: (row["date"], order[row["id"]]), reverse=True)
    for row in transactions:
        row["amount"] = float(row["amount"])
        row["cash_change"] = float(row["cash_change"])
    return {
        "account": dict(account), "balance": float(current),
        "income": float(income), "expenses": float(expenses), "as_of": today.isoformat(),
        "has_checkpoints": bool(checkpoints),
        "history": [{"date": day, "balance": history[day]} for day in sorted(history)],
        "transactions": transactions,
    }
