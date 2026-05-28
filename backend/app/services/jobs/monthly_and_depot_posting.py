# backend/app/services/jobs/monthly_and_depot_posting.py
from datetime import datetime, date
from decimal import Decimal
import calendar
import re

from backend.app.database.db_handling import DBHandler
from backend.app.models.schema import (
    SchemaKontobewegung,
    SchemaMonthlyCosts,
)

# ----------------------------- Helpers ---------------------------------


def _to_date(d) -> date:
    return d.date() if isinstance(d, datetime) else d


def _add_months(d: date, months: int) -> date:
    """Monatsweise weiterschalten (31->Monatsende korrekt)."""
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    last_day = calendar.monthrange(y, m)[1]
    return date(y, m, min(d.day, last_day))


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
        # active)]: contentReference[oaicite:3]{index=3}
        for (mc_id, user_id, name, betrag, anteil, securities_id, kategorie_id,
             ausgangs_konto_id, eingangs_konto_id, start_datum,
             next_due, active) in rows:

            if not active:
                continue
            if next_due is None:
                continue
            due = _to_date(next_due)
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

            # next_due um genau 1 Monat weiterdrehen
            new_due = _add_months(due, 1)
            db.update_monthlycosts(
                SchemaMonthlyCosts(
                    id=mc_id,
                    user_id=user_id,
                    name=name,
                    betrag=Decimal(str(
                        betrag)) if betrag is not None else None,
                    anteil=Decimal(str(
                        anteil)) if anteil is not None else None,
                    securities_id=securities_id,
                    kategorie_id=kategorie_id,
                    ausgangs_konto_id=ausgangs_konto_id,
                    eingangs_konto_id=eingangs_konto_id,
                    start_datum=start_datum,
                    next_due=datetime.combine(new_due, datetime.min.time()),
                    active=active,
                )
            )  # nutzt dein UPDATE. :contentReference[oaicite:4]{index=4}

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
