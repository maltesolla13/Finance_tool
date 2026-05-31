# backend/app/services/jobs/monthly_and_depot_posting.py
from datetime import datetime, date, timedelta
from decimal import Decimal
import calendar
import re

from backend.app.database.db_handling import DBHandler
from backend.app.models.schema import (
    SchemaKontobewegung,
    SchemaMonthlyCosts,
    SchemaMonthlyCostsExecution,
)

# ----------------------------- Helpers ---------------------------------


def _to_date(d) -> date:
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        return datetime.fromisoformat(d[:10]).date()
    return d


def _add_months(d: date, months: int, anchor_day: int | None = None) -> date:
    """Monatsweise weiterschalten (31->Monatsende korrekt)."""
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    last_day = calendar.monthrange(y, m)[1]
    return date(y, m, min(anchor_day or d.day, last_day))


def _next_due_date(
        d: date,
        repeat_type: str | None,
        custom_interval: int | None,
        custom_unit: str | None,
        anchor_day: int | None = None) -> date:
    repeat = (repeat_type or "MONTHLY").upper()
    if repeat == "WEEKLY":
        return d + timedelta(days=7)
    if repeat == "QUARTERLY":
        return _add_months(d, 3, anchor_day)
    if repeat == "YEARLY":
        return _add_months(d, 12, anchor_day)
    if repeat == "CUSTOM":
        count = max(1, int(custom_interval or 1))
        unit = (custom_unit or "MONTHS").upper()
        if unit == "DAYS":
            return d + timedelta(days=count)
        if unit == "WEEKS":
            return d + timedelta(days=count * 7)
        if unit == "YEARS":
            return _add_months(d, count * 12, anchor_day)
        return _add_months(d, count, anchor_day)
    return _add_months(d, 1, anchor_day)


def _normalize_non_depot_name(name: str) -> str:
    """
    Entfernt einen Depot-Zusatz am Ende, z.B.:
    'Giro (Depot)', 'Broker Depot', 'Cash - Depot' -> 'Giro', 'Broker', 'Cash'
    """
    if not name:
        return name
    # nur am Ende entfernen
    return re.sub(r'\s*[-(]?\s*depot\s*[)]?\s*$', '', name,
                  flags=re.IGNORECASE).strip()


def _map_depotkonto_to_cash_konto_id(
        db: DBHandler, depot_konto_id: int) -> int:
    """
    Findet das Konto mit gleichem Namen *ohne* Depot-Zusatz.
    Wenn kein Match gefunden: fallback = depot_konto_id.
    """
    konten = db.load_konten()  # [(id, name), ...]
    id_to_name = {k_id: name for (k_id, name) in konten}
    name_to_id = {name: k_id for (k_id, name) in konten}
    src_name = id_to_name.get(depot_konto_id)
    if not src_name:
        return depot_konto_id
    base = _normalize_non_depot_name(src_name)
    return name_to_id.get(base, depot_konto_id)


def _kontobewegung_exists(
        db: DBHandler, *, name: str, datum: datetime | date,
        konto_id: int) -> bool:
    d = datum if isinstance(datum, datetime) else datetime.combine(
        datum, datetime.min.time())
    db.cursor.execute(
        "SELECT 1 FROM kontobewegung WHERE name = ? AND konto_id = ?"
        "AND DATE(datum) = DATE(?) LIMIT 1",
        (name, konto_id, d.isoformat()),
    )
    return db.cursor.fetchone() is not None


def _insert_kontobewegung(
    db: DBHandler,
    *,
    user_id: int,
    name: str,
    betrag: Decimal,
    kategorie_id: int | None,
    konto_id: int,
    type_: str,
    datum: datetime | date,
):
    if _kontobewegung_exists(db, name=name, datum=datum, konto_id=konto_id):
        return  # idempotent
    payload = SchemaKontobewegung(
        user_id=user_id,
        name=name,
        betrag=Decimal(betrag),
        kategorie_id=kategorie_id,
        konto_id=konto_id,
        type=type_,
        datum=datum if isinstance(datum, datetime) else datetime.combine(
            datum, datetime.min.time()),
    )
    db.insert_kontobewegung(payload)
    # nutzt dein existing INSERT. :contentReference[oaicite:2]{index=2}


def _monthlycost_execution_exists(
        db: DBHandler, *, monthlycost_id: int, execution_datum: date) -> bool:
    db.cursor.execute(
        """
        SELECT 1
        FROM monthlycosts_execution
        WHERE monthlycost_id = ?
          AND DATE(execution_datum) = DATE(?)
        LIMIT 1
        """,
        (monthlycost_id, execution_datum.isoformat()),
    )
    return db.cursor.fetchone() is not None


def _insert_monthlycost_execution(
    db: DBHandler,
    *,
    monthlycost_id: int,
    user_id: int,
    name: str,
    betrag,
    anteil,
    securities_id: int | None,
    kategorie_id: int | None,
    ausgangs_konto_id: int | None,
    eingangs_konto_id: int | None,
    execution_datum: date,
    status: str = "EXECUTED",
):
    if _monthlycost_execution_exists(
            db, monthlycost_id=monthlycost_id,
            execution_datum=execution_datum):
        return
    db.insert_monthlycosts_execution(
        SchemaMonthlyCostsExecution(
            monthlycost_id=monthlycost_id,
            user_id=user_id,
            name=name,
            betrag=Decimal(str(betrag)) if betrag is not None else None,
            anteil=Decimal(str(anteil)) if anteil is not None else None,
            securities_id=securities_id,
            kategorie_id=kategorie_id,
            ausgangs_konto_id=ausgangs_konto_id,
            eingangs_konto_id=eingangs_konto_id,
            execution_datum=datetime.combine(
                execution_datum, datetime.min.time()),
            status=status,
        )
    )


def _backfill_monthlycost_executions_until(
    db: DBHandler,
    *,
    monthlycost_id: int,
    user_id: int,
    name: str,
    betrag,
    anteil,
    securities_id: int | None,
    kategorie_id: int | None,
    ausgangs_konto_id: int | None,
    eingangs_konto_id: int | None,
    start_datum,
    repeat_type: str | None,
    custom_interval: int | None,
    custom_unit: str | None,
    until_date: date,
):
    due = _to_date(start_datum)
    if not due:
        return

    anchor_day = due.day
    guard = 0
    while due <= until_date and guard < 1000:
        _insert_monthlycost_execution(
            db,
            monthlycost_id=monthlycost_id,
            user_id=user_id,
            name=name,
            betrag=betrag,
            anteil=anteil,
            securities_id=securities_id,
            kategorie_id=kategorie_id,
            ausgangs_konto_id=ausgangs_konto_id,
            eingangs_konto_id=eingangs_konto_id,
            execution_datum=due,
        )
        due = _next_due_date(
            due, repeat_type, custom_interval, custom_unit, anchor_day)
        guard += 1


def _first_due_after(
        start_datum,
        after_date: date,
        repeat_type: str | None,
        custom_interval: int | None,
        custom_unit: str | None) -> date | None:
    due = _to_date(start_datum)
    if not due:
        return None

    anchor_day = due.day
    guard = 0
    while due <= after_date and guard < 1000:
        due = _next_due_date(
            due, repeat_type, custom_interval, custom_unit, anchor_day)
        guard += 1
    return due


def _set_monthlycost_next_due(
    db: DBHandler,
    *,
    mc_id: int,
    user_id: int,
    name: str,
    betrag,
    anteil,
    securities_id: int | None,
    kategorie_id: int | None,
    ausgangs_konto_id: int | None,
    eingangs_konto_id: int | None,
    start_datum,
    next_due: date,
    repeat_type: str | None,
    custom_interval: int | None,
    custom_unit: str | None,
    active,
):
    db.update_monthlycosts(
        SchemaMonthlyCosts(
            id=mc_id,
            user_id=user_id,
            name=name,
            betrag=Decimal(str(betrag)) if betrag is not None else None,
            anteil=Decimal(str(anteil)) if anteil is not None else None,
            securities_id=securities_id,
            kategorie_id=kategorie_id,
            ausgangs_konto_id=ausgangs_konto_id,
            eingangs_konto_id=eingangs_konto_id,
            start_datum=start_datum,
            next_due=datetime.combine(next_due, datetime.min.time()),
            repeat_type=repeat_type,
            custom_interval=custom_interval,
            custom_unit=custom_unit,
            active=active,
        )
    )

# ----------------------- 1) MonthlyCosts ausführen ----------------------


def run_monthlycosts_for_date(run_date: date):
    """
    Bucht alle monthlycosts, deren next_due == run_date.
    - Kein Wertpapier: + auf Eingang, - auf Ausgang; bei beiden -> 2 Buchungen.
    - Mit Wertpapier:  nur - auf Ausgang (Cash-Abfluss).
    Danach wird next_due um +1 Monat erhöht (ggf. mehrfach, falls überfällig).
    """
    run_date = _to_date(run_date)
    db = DBHandler()
    try:
        rows = db.load_monthlycosts()
        # [(id, user_id, name, betrag, anteil, securities_id, kategorie_id,
        # ausgangs_konto_id, eingangs_konto_id, start_datum, next_due,
        # repeat_type, custom_interval, custom_unit, active)]
        for (mc_id, user_id, name, betrag, anteil, securities_id, kategorie_id,
             ausgangs_konto_id, eingangs_konto_id, start_datum,
             next_due, repeat_type, custom_interval, custom_unit, active) in rows:

            if not active:
                continue
            _backfill_monthlycost_executions_until(
                db,
                monthlycost_id=mc_id,
                user_id=user_id,
                name=name,
                betrag=betrag,
                anteil=anteil,
                securities_id=securities_id,
                kategorie_id=kategorie_id,
                ausgangs_konto_id=ausgangs_konto_id,
                eingangs_konto_id=eingangs_konto_id,
                start_datum=start_datum,
                repeat_type=repeat_type,
                custom_interval=custom_interval,
                custom_unit=custom_unit,
                until_date=run_date,
            )
            if next_due is None:
                continue
            due = _to_date(next_due)
            if due < run_date:
                new_due = _first_due_after(
                    start_datum, run_date, repeat_type, custom_interval,
                    custom_unit)
                if new_due:
                    _set_monthlycost_next_due(
                        db,
                        mc_id=mc_id,
                        user_id=user_id,
                        name=name,
                        betrag=betrag,
                        anteil=anteil,
                        securities_id=securities_id,
                        kategorie_id=kategorie_id,
                        ausgangs_konto_id=ausgangs_konto_id,
                        eingangs_konto_id=eingangs_konto_id,
                        start_datum=start_datum,
                        next_due=new_due,
                        repeat_type=repeat_type,
                        custom_interval=custom_interval,
                        custom_unit=custom_unit,
                        active=active,
                    )
                continue
            # nur exakter Fälligkeitstag ausführen
            if due != run_date:
                continue

            if betrag is None:
                # anteil-Logik nicht Teil deiner Anforderung -> überspringen
                continue

            amount = Decimal(str(betrag))

            # Buchungsnamen mit Marker, damit idempotent
            base_label = f"AUTO: monthlycost#{mc_id} ({name})"

            if securities_id:
                # Nur Ausgangskonto, negativ
                if ausgangs_konto_id:
                    _insert_kontobewegung(
                        db,
                        user_id=user_id,
                        name=f"{base_label} - Aktie (Ausgang)",
                        betrag=Decimal(-abs(amount)),
                        kategorie_id=kategorie_id,
                        konto_id=ausgangs_konto_id,
                        type_="MonthlyCosts",
                        datum=run_date,
                    )
            else:
                # Kein Wertpapier
                if eingangs_konto_id:
                    _insert_kontobewegung(
                        db,
                        user_id=user_id,
                        name=f"{base_label} - Eingang",
                        betrag=Decimal(abs(amount)),
                        kategorie_id=kategorie_id,
                        konto_id=eingangs_konto_id,
                        type_="MonthlyCosts",
                        datum=run_date,
                    )
                if ausgangs_konto_id:
                    _insert_kontobewegung(
                        db,
                        user_id=user_id,
                        name=f"{base_label} - Ausgang",
                        betrag=Decimal(-abs(amount)),
                        kategorie_id=kategorie_id,
                        konto_id=ausgangs_konto_id,
                        type_="MonthlyCosts",
                        datum=run_date,
                    )

            _insert_monthlycost_execution(
                db,
                monthlycost_id=mc_id,
                user_id=user_id,
                name=name,
                betrag=betrag,
                anteil=anteil,
                securities_id=securities_id,
                kategorie_id=kategorie_id,
                ausgangs_konto_id=ausgangs_konto_id,
                eingangs_konto_id=eingangs_konto_id,
                execution_datum=run_date,
            )

            # next_due auf den naechsten Termin weiterdrehen
            new_due = _next_due_date(
                due, repeat_type, custom_interval, custom_unit,
                _to_date(start_datum).day)
            _set_monthlycost_next_due(
                db,
                mc_id=mc_id,
                user_id=user_id,
                name=name,
                betrag=betrag,
                anteil=anteil,
                securities_id=securities_id,
                kategorie_id=kategorie_id,
                ausgangs_konto_id=ausgangs_konto_id,
                eingangs_konto_id=eingangs_konto_id,
                start_datum=start_datum,
                next_due=new_due,
                repeat_type=repeat_type,
                custom_interval=custom_interval,
                custom_unit=custom_unit,
                active=active,
            )

        db.conn.commit()
    finally:
        db.close()

# ---------------- 2) Depotbewegung -> Kontobewegung spiegeln ------------


def mirror_depotbewegung_to_kontobewegung(only_for_date: date | None = None):
    """
    Für jede Depotbewegung:
      - type 'Kauf'  -> negativer Betrag auf *Nicht-Depot*-Konto
      - type 'Verkauf' -> positiver Betrag auf *Nicht-Depot*-Konto
    Idempotent anhand (name, konto_id, datum).
    """
    db = DBHandler()
    try:
        rows = db.load_depotbewegung()
        # [(id, user_id, konto_id, securities_id, kategorie_id,
        # type, betrag, anteile, datum)] :contentReference[oaicite:5]
        # {index=5}
        # baue Kontonamen-Map nur 1x
        for (dep_id, user_id, depot_konto_id, securities_id, kategorie_id,
             type_, betrag, anteile, datum) in rows:

            if only_for_date:
                if _to_date(datum) != _to_date(only_for_date):
                    continue

            if betrag is None or type_ is None:
                continue

            cash_konto_id = _map_depotkonto_to_cash_konto_id(
                db, depot_konto_id)

            label = f"AUTO: depot#{dep_id} {type_.lower()}"
            amount = Decimal(str(betrag))

            if type_.lower() == "kauf":
                post_amount = Decimal(-abs(amount))
                post_type = "Depot Kauf"
            elif type_.lower() == "verkauf":
                post_amount = Decimal(abs(amount))
                post_type = "Depot Verkauf"
            else:
                # andere Typen ignorieren (z.B. Dividende o.ä. – falls
                # gewünscht, später erweitern)
                continue

            _insert_kontobewegung(
                db,
                user_id=user_id,
                name=label,
                betrag=post_amount,
                kategorie_id=kategorie_id,
                konto_id=cash_konto_id,
                type_=post_type,
                datum=datum,
            )

        db.conn.commit()
    finally:
        db.close()
