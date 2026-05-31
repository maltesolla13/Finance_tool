from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
import calendar

from backend.app.database.db_handling import DBHandler


INCOME_CATEGORY = "gehalt"


def _to_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(str(value)[:10]).date()


def _month_key(value) -> str:
    d = _to_date(value)
    return f"{d.year:04d}-{d.month:02d}"


def _add_months(d: date, months: int) -> date:
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    last = calendar.monthrange(y, m)[1]
    return date(y, m, min(d.day, last))


def _money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP)


def _load_income_by_month(db: DBHandler, user_id: int | None = None) -> dict:
    sql = """
        SELECT kb.id, kb.user_id, kb.betrag, kb.datum
        FROM kontobewegung kb
        JOIN kategorien k ON k.id = kb.kategorie_id
        WHERE LOWER(k.name) = ?
          AND kb.betrag > 0
    """
    params = [INCOME_CATEGORY]
    if user_id is not None:
        sql += " AND kb.user_id = ?"
        params.append(user_id)
    sql += " ORDER BY kb.datum, kb.id"

    incomes = {}
    for row in db.cursor.execute(sql, params).fetchall():
        key = _month_key(row["datum"])
        current = incomes.setdefault(
            key,
            {
                "income_ids": [],
                "income_amount": Decimal("0"),
                "user_id": row["user_id"],
            },
        )
        current["income_ids"].append(row["id"])
        current["income_amount"] += _money(row["betrag"])
    return incomes


def _month_count(start: date, end: date) -> int:
    return max(1, (end.year - start.year) * 12 + end.month - start.month + 1)


def _derive_missing_fields(saving, incomes: dict) -> dict:
    target = _money(saving["betrag"])
    start = _to_date(saving["start_datum"])
    end = _to_date(saving["end_datum"])
    rate_e = saving["sparrate_e"]
    rate_p = saving["sparrate_p"]
    avg_income = None
    if incomes:
        total = sum((v["income_amount"] for v in incomes.values()),
                    Decimal("0"))
        avg_income = total / Decimal(len(incomes))

    derived = {
        "end_datum": saving["end_datum"],
        "sparrate_e": rate_e,
        "sparrate_p": rate_p,
    }

    if not incomes:
        return derived

    if end and rate_e is None:
        months = _month_count(start, end)
        derived["sparrate_e"] = float((target / Decimal(months)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP))
    if avg_income and derived["sparrate_e"] is not None and rate_p is None:
        derived["sparrate_p"] = float(
            (_money(derived["sparrate_e"]) / avg_income * Decimal("100"))
            .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        )
    if avg_income and rate_p is not None and rate_e is None:
        derived["sparrate_e"] = float(
            (avg_income * _money(rate_p) / Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP)
        )
    if start and derived["sparrate_e"] and end is None:
        months_needed = int(
            (target / _money(derived["sparrate_e"])).to_integral_value(
                rounding=ROUND_HALF_UP)
        )
        months_needed = max(1, months_needed)
        derived["end_datum"] = _add_months(start, months_needed - 1).isoformat()

    return derived


def _execution_amount(saving, income_amount: Decimal) -> Decimal | None:
    if saving["sparrate_p"] is not None:
        return (income_amount * _money(saving["sparrate_p"]) / Decimal("100")) \
            .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if saving["sparrate_e"] is not None:
        return _money(saving["sparrate_e"])
    return None


def recalc_savings(savings_id: int | None = None) -> None:
    db = DBHandler()
    try:
        query = "SELECT * FROM savings"
        params = []
        if savings_id is not None:
            query += " WHERE id = ?"
            params.append(savings_id)

        rows = db.cursor.execute(query, params).fetchall()
        for saving in rows:
            incomes = _load_income_by_month(db, saving["user_id"])
            derived = _derive_missing_fields(saving, incomes)
            db.cursor.execute(
                """
                UPDATE savings
                SET end_datum = ?, sparrate_e = ?, sparrate_p = ?
                WHERE id = ?
                """,
                (
                    derived["end_datum"],
                    derived["sparrate_e"],
                    derived["sparrate_p"],
                    saving["id"],
                ),
            )

            db.cursor.execute(
                "DELETE FROM savings_execution WHERE savings_id = ?",
                (saving["id"],),
            )

            start = _to_date(saving["start_datum"])
            end = _to_date(derived["end_datum"]) or date.today()
            month = date(start.year, start.month, 1)
            end_month = date(end.year, end.month, 1)
            current_saving = dict(saving)
            current_saving.update(derived)

            while month <= end_month:
                income = incomes.get(f"{month.year:04d}-{month.month:02d}")
                if income:
                    amount = _execution_amount(
                        current_saving, income["income_amount"])
                    if amount and amount > 0:
                        db.cursor.execute(
                            """
                            INSERT INTO savings_execution (
                                savings_id, user_id, konto_id, kategorie_id,
                                income_kontobewegung_id, execution_month,
                                income_amount, amount, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'EXECUTED')
                            """,
                            (
                                saving["id"],
                                saving["user_id"],
                                saving["konto_id"],
                                saving["kategorie_id"],
                                income["income_ids"][0],
                                month.isoformat(),
                                float(income["income_amount"]),
                                float(amount),
                            ),
                        )
                month = _add_months(month, 1)

        db.conn.commit()
    finally:
        db.close()


def recalc_all_savings() -> None:
    recalc_savings(None)
