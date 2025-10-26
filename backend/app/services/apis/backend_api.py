from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
from typing import List, Callable, Any
from types import SimpleNamespace
from zoneinfo import ZoneInfo
from backend.app.services.depot.daily_jobs import ensure_depotstand_from_last
from backend.app.services.depot.monthly_jobs import run_monthly_securities_jobs
from backend.app.database.db_handling import DBHandler
from backend.app.services.apis.market_api import (
    fetch_high_on_or_after, fetch_low_on_or_after
)
from backend.app.models.schema import SchemaKonto, \
    SchemaUser, SchemaMonthlyCosts, SchemaReceipt, SchemaKategorie, \
    SchemaOption, SchemaSecurities, SchemaLaden, SchemaSparziel, \
    SchemaDepotbewegung, SchemaDepotstand

TZ = ZoneInfo("Europe/Berlin")


def _parse_date_qs(date: str | None) -> datetime:
    if not date:
        return datetime.now(TZ)
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(date, fmt).replace(tzinfo=TZ)
        except ValueError:
            pass
    # falls ISO mit Offset kommt:
    return datetime.fromisoformat(date)


r_market = APIRouter(prefix="/market", tags=["Market"])


@r_market.get("/high")
def market_high(ticker: str = Query(..., examples=["NVDA"]),
                date: str | None = Query(None, examples=["2025-10-21"])):
    dt = _parse_date_qs(date)
    v = float(fetch_high_on_or_after(ticker, dt))
    return {"ticker": ticker, "date_used": dt.strftime("%Y-%m-%d"), "high": v}


@r_market.get("/low")
def market_low(ticker: str = Query(..., examples=["NVDA"]),
               date: str | None = Query(None, examples=["2025-10-21"])):
    dt = _parse_date_qs(date)
    v = float(fetch_low_on_or_after(ticker, dt))
    return {"ticker": ticker, "date_used": dt.strftime("%Y-%m-%d"), "low": v}


class BackendRoutes:

    def __init__(self) -> None:
        self.router = APIRouter()
        self.request_handling()

    # ---- Generic CRUD wiring ----------------------------------------------
    def wire_crud(
            self,
            name: str,
            dto_in: Any,
            dto_out: Any,
            list_fn: Callable[[], List[Any]],
            create_fn: Callable[[Any], None],
            update_fn: Callable[[int, Any], None],
            delete_fn: Callable[[int], None],
            tag: str | None = None,
    ) -> None:
        r = APIRouter(prefix=f"/{name}", tags=[tag or name.title()])

        # GET /{name}
        @r.get("", response_model=List[dto_out])
        def list_items():
            return list_fn()

        # POST /{name}
        @r.post("", status_code=201)
        def create_item(payload: Any):
            create_fn(payload)
            return {"ok": True}
        create_item.__annotations__["payload"] = dto_in

        # PUT /{name}/{item_id}
        @r.put("/{item_id}")
        def update_item(item_id: int, payload: Any):
            update_fn(item_id, payload)
            return {"ok": True}
        update_item.__annotations__["payload"] = dto_in

        # DELETE /{name}/{item_id}
        @r.delete("/{item_id}")
        def delete_item(item_id: int):
            delete_fn(item_id)
            return {"ok": True}

        self.router.include_router(r)

    # ---- Helpers für optionales Update (Merge-Strategie) -----------
    def _dt(self, x):
        return x.isoformat() if isinstance(x, datetime) else x

    def _payload_changes(
            self, payload_obj: object,
            allowed_fields: list[str]) -> dict:
        """
        Extrahiert nur gesetzte Felder aus dem Payload (None wird ignoriert).
        Funktioniert für pydantic BaseModel wie auch pydantic.dataclasses.
        """
        if hasattr(payload_obj, "model_dump"):  # Pydantic v2 Model
            data = payload_obj.model_dump(
                exclude={"id"}, exclude_unset=True, exclude_none=True)
        elif hasattr(payload_obj, "dict"):     # Pydantic v1 Model
            data = payload_obj.dict(
                exclude={"id"}, exclude_unset=True, exclude_none=True)
        else:                # Dataclass (pydantic.dataclasses)
            raw = dict(getattr(payload_obj, "__dict__", {}) or {})
            raw.pop("id", None)
            data = {k: v for k, v in raw.items() if v is not None}
        # Nur erlaubte Felder durchlassen
        return {k: v for k, v in data.items() if k in allowed_fields}

    def _merge_for_update(self, db: DBHandler, table: str, id_col: str,
                          item_id: int, payload_obj: object, fields: list[str],
                          normalizer=None) -> SimpleNamespace:
        """
        Lädt Row, merged Änderungen (exclude None), normalisiert und liefert
        Namespace mit ALLEN von db_handling.* erwarteten Attributen zurück.
        """
        row = db.cursor.execute(
            f"SELECT {', '.join(fields)} FROM {table} WHERE {id_col}=?",
            (item_id,)
        ).fetchone()
        if not row:
            raise HTTPException(
                status_code=404, detail=f"{table} nicht gefunden")

        changes = self._payload_changes(payload_obj, fields)

        # Bestehende DB-Werte als Basis (vollständig)
        data = {k: row[k] for k in fields}
        # Änderungen drüberbügeln
        data.update(changes)

        # Normalisieren (Typen, Defaults, Booleans etc.)
        if normalizer:
            data = normalizer(data)

        # ID aus URL als Quelle der Wahrheit
        data["id"] = item_id
        return SimpleNamespace(**data)

    # Spezifische Normalizer für Tabellen, abhängig vom erwarteten DB-Update

    def _normalize_monthlycosts(self, d: dict) -> dict:
        out = dict(d)
        # ints
        for k in ("user_id", "kategorie_id", "ausgangs_konto_id",
                  "eingangs_konto_id", "securities_id"):
            if out.get(k) is not None:
                out[k] = int(out[k])
        # Datum → ISO-String
        if out.get("start_datum") is not None:
            out["start_datum"] = self._dt(out["start_datum"])
        if out.get("next_due") is not None:
            out["next_due"] = self._dt(out["next_due"])
        # Fallback next_due = start_datum
        if not out.get("next_due"):
            out["next_due"] = out.get("start_datum")
        # active → 0/1 (INTEGER)
        out["active"] = 1 if bool(out.get("active")) else 0
        return out

    def _normalize_receipt(self, d: dict) -> dict:
        out = dict(d)
        if out.get("datum") is not None:
            out["datum"] = self._dt(out["datum"])
        return out

    def _normalize_savings(self, d: dict) -> dict:
        out = dict(d)
        if out.get("start_datum") is not None:
            out["start_datum"] = self._dt(out["start_datum"])
        if out.get("end_datum") is not None:
            out["end_datum"] = self._dt(out["end_datum"])
        return out

    # ---- Request/Route-Definitionen -----------------------------------------
    def request_handling(self) -> None:
        opt_router = APIRouter(prefix="/options", tags=["Options"])

        @opt_router.get("", response_model=List[SchemaOption])
        def get_options(
            entity: str = Query(
                ..., description="users|konten|kategorien|laden|ausgabentypen"
            ),
            q: str = Query("", description="Filter-Text (optional)")
        ):
            table_map = {
                "users": "user",
                "konten": "konten",
                "kategorien": "kategorien",
                "laden": "laden",
                "ausgabentypen": "ausgabentypen",
            }
            table = table_map.get(entity)
            if not table:
                raise HTTPException(status_code=400, detail="Unknown entity")

            db = DBHandler()
            try:
                if q:
                    rows = db.cursor.execute(
                        f"SELECT id, name FROM {table} "
                        "WHERE name LIKE ? COLLATE NOCASE "
                        "ORDER BY name LIMIT 50",
                        (f"%{q}%",)
                    ).fetchall()
                else:
                    rows = db.cursor.execute(
                        f"SELECT id, name FROM {table} ORDER BY name LIMIT 50"
                    ).fetchall()
                return [SchemaOption(id=r["id"], name=r["name"]) for r in rows]
            finally:
                db.close()

        class EnsureIn(BaseModel):
            entity: str
            name: str

        @opt_router.post(
                "/ensure",
                response_model=SchemaOption,
                status_code=201)
        def ensure_option(payload: EnsureIn):
            if payload.entity not in {"kategorien", "laden"}:
                raise HTTPException(
                    status_code=400,
                    detail="Only 'kategorien' or 'laden' allowed")

            name = payload.name.strip()
            if not name:
                raise HTTPException(status_code=400, detail="Name required")

            table = payload.entity  # 'kategorien' ODER 'laden'
            db = DBHandler()
            try:
                row = db.cursor.execute(
                    f"SELECT id, name FROM {table} WHERE name = ?",
                    (name,)
                ).fetchone()
                if row:
                    return SchemaOption(id=row["id"], name=row["name"])

                db.cursor.execute(
                    f"INSERT INTO {table}(name) VALUES (?)",
                    (name,))
                new_id = db.cursor.lastrowid
                db.conn.commit()
                return SchemaOption(id=new_id, name=name)
            finally:
                db.close()

        jobs = APIRouter(prefix="/jobs", tags=["Jobs"])

        @jobs.post("/monthly-securities/run")
        def run_monthly(date: str | None = None):
            run_date = _parse_date_qs(date)
            return run_monthly_securities_jobs(run_date)

        @jobs.post("/depotstand/run")
        def run_depotstand(date: str | None = None):
            run_date = _parse_date_qs(date)
            return ensure_depotstand_from_last(run_date)

        # ---- Konto ----
        def get_konto() -> List[SchemaKonto]:
            db = DBHandler()
            try:
                rows = db.load_konten()
                return [SchemaKonto(id=row["id"], name=row["name"])
                        for row in rows]
            finally:
                db.close()

        def create_konto(payload: SchemaKonto) -> None:
            db = DBHandler()
            try:
                db.insert_konto(SimpleNamespace(name=payload.name))
            finally:
                db.close()

        def update_konto(konto_id: int, payload: SchemaKonto) -> None:
            db = DBHandler()
            try:
                ids = [r["id"] for r in db.load_konten()]
                if konto_id not in ids:
                    raise HTTPException(status_code=404,
                                        detail="Konto not found")
                db.update_konto(SimpleNamespace(
                    id=konto_id, name=payload.name))
            finally:
                db.close()

        def delete_konto(konto_id: int) -> None:
            db = DBHandler()
            try:
                db.cursor.execute("DELETE FROM konten WHERE id = ?",
                                  (konto_id,))
                if db.cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=404, detail="Konto not found")
                db.conn.commit()
            finally:
                db.close()

        # ---- Users ----
        def get_user() -> List[SchemaUser]:
            db = DBHandler()
            try:
                rows = db.cursor.execute(
                    "SELECT id, name FROM user ORDER BY id").fetchall()
                return [SchemaUser(id=r["id"], name=r["name"]) for r in rows]
            finally:
                db.close()

        def create_users(payload: SchemaUser) -> None:
            db = DBHandler()
            try:
                db.cursor.execute(
                    "INSERT INTO user(name) VALUES (?)", (payload.name,))
                db.conn.commit()
            finally:
                db.close()

        def update_user(user_id: int, payload: SchemaUser) -> None:
            db = DBHandler()
            try:
                db.cursor.execute(
                    "UPDATE user SET name=? WHERE id=?",
                    (payload.name, user_id))
                if db.cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=404, detail="User nicht gefunden")
                db.conn.commit()
            finally:
                db.close()

        def delete_user(user_id: int) -> None:
            db = DBHandler()
            try:
                db.cursor.execute("DELETE FROM user WHERE id=?", (user_id,))
                if db.cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=404, detail="User nicht gefunden")
                db.conn.commit()
            finally:
                db.close()

        # ---- Kategorien ----
        def get_kategorien() -> List[SchemaKategorie]:
            db = DBHandler()
            try:
                rows = db.cursor.execute(
                    "SELECT id, name FROM kategorien ORDER BY id").fetchall()
                return [SchemaKategorie(
                    id=r["id"],
                    name=r["name"]) for r in rows]
            finally:
                db.close()

        def create_kategorien(payload: SchemaKategorie) -> None:
            db = DBHandler()
            try:
                db.cursor.execute(
                    "INSERT INTO kategorien(name) VALUES (?)", (payload.name,))
                db.conn.commit()
            finally:
                db.close()

        def update_kategorien(
                kategorie_id: int,
                payload: SchemaKategorie) -> None:
            db = DBHandler()
            try:
                db.cursor.execute(
                    "UPDATE kategorien SET name=? WHERE id=?",
                    (payload.name, kategorie_id))
                if db.cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=404, detail="Kategorie nicht gefunden")
                db.conn.commit()
            finally:
                db.close()

        def delete_kategorien(kategorie_id: int) -> None:
            db = DBHandler()
            try:
                db.cursor.execute(
                    "DELETE FROM kategorien WHERE id=?",
                    (kategorie_id,))
                if db.cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=404, detail="Kategorie nicht gefunden")
                db.conn.commit()
            finally:
                db.close()

        # ---- Laden ----
        def get_laden() -> List[SchemaLaden]:
            db = DBHandler()
            try:
                rows = db.load_laden()
                return [SchemaLaden(id=row["id"], name=row["name"])
                        for row in rows]
            finally:
                db.close()

        def create_laden(payload: SchemaLaden) -> None:
            db = DBHandler()
            try:
                db.insert_laden(SimpleNamespace(name=payload.name))
            finally:
                db.close()

        def update_laden(laden_id: int, payload: SchemaLaden) -> None:
            db = DBHandler()
            try:
                ids = [r["id"] for r in db.load_laden()]
                if laden_id not in ids:
                    raise HTTPException(status_code=404,
                                        detail="Laden not found")
                db.update_laden(SimpleNamespace(
                    id=laden_id, name=payload.name))
            finally:
                db.close()

        def delete_laden(laden_id: int) -> None:
            db = DBHandler()
            try:
                db.cursor.execute("DELETE FROM laden WHERE id = ?",
                                  (laden_id,))
                if db.cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=404, detail="Laden not found")
                db.conn.commit()
            finally:
                db.close()

        # ---- MonthlyCosts ----
        def get_monthlycosts() -> List[SchemaMonthlyCosts]:
            db = DBHandler()
            try:
                rows = db.load_monthlycosts()
                return [
                    SchemaMonthlyCosts(
                        id=r["id"],
                        user_id=r["user_id"],
                        name=r["name"],
                        betrag=r["betrag"],
                        anteil=r["anteil"],
                        securities_id=r["securities_id"],
                        kategorie_id=r["kategorie_id"],
                        ausgangs_konto_id=r["ausgangs_konto_id"],
                        eingangs_konto_id=r["eingangs_konto_id"],
                        start_datum=(r["start_datum"][:10]
                                     if r["start_datum"]
                                     else None),
                        next_due=(r["next_due"][:10]
                                  if r["next_due"]
                                  else None),
                        active=bool(r["active"]),
                    )
                    for r in rows
                ]
            finally:
                db.close()

        def create_monthlycosts(payload: SchemaMonthlyCosts) -> None:
            db = DBHandler()
            try:
                p = SimpleNamespace(**payload.__dict__)

                # Normalisieren
                p.user_id = int(p.user_id) if p.user_id is not None else None
                p.kategorie_id = int(
                    p.kategorie_id) if p.kategorie_id is not None else None
                p.ausgangs_konto_id = int(
                    p.ausgangs_konto_id) if p.ausgangs_konto_id else None
                p.eingangs_konto_id = int(
                    p.eingangs_konto_id) if p.eingangs_konto_id else None
                p.securities_id = int(
                    p.securities_id) if p.securities_id else None
                p.active = 1 if bool(p.active) else 0
                if not p.next_due:
                    p.next_due = p.start_datum  # fallback

                # FK-Checks
                def exists(table, id_):
                    if id_ is None:
                        return True
                    row = db.cursor.execute(
                        f"SELECT 1 FROM {table} WHERE id=?", (id_,)).fetchone()
                    return row is not None

                if not exists("user", p.user_id):
                    raise HTTPException(400, detail="Unbekannter user_id")
                if not exists("kategorien", p.kategorie_id):
                    raise HTTPException(400, detail="Unbekannter kategorie_id")
                if p.ausgangs_konto_id and not exists(
                        "konten", p.ausgangs_konto_id):
                    raise HTTPException(
                        400, detail="Unbekannter ausgangs_konto_id")
                if p.eingangs_konto_id and not exists(
                        "konten", p.eingangs_konto_id):
                    raise HTTPException(
                        400, detail="Unbekannter eingangs_konto_id")
                if p.securities_id and not exists(
                        "securities", p.securities_id):
                    raise HTTPException(
                        400, detail="Unbekannter securities_id (Wertpapier)")

                if p.securities_id and (p.betrag is None and p.anteil is None):
                    raise HTTPException(
                        400, detail="Bei Wertpapier bitte Betrag oder Anteil"
                        "angeben.")

                db.insert_monthlycosts(p)
                db.conn.commit()
            finally:
                db.close()

        def update_monthlycosts(
                monthlycosts_id: int,
                payload: SchemaMonthlyCosts) -> None:
            """
            Optionales Update: Payload-Felder sind alle optional.
            → Bestehenden Datensatz laden, Änderungen mergen, normalisieren,
            dann voll updaten.
            """
            db = DBHandler()
            try:
                # Felder, die db_handling.update_monthlycosts erwartet:
                fields = [
                    "user_id", "name", "betrag", "anteil", "securities_id",
                    "kategorie_id", "ausgangs_konto_id", "eingangs_konto_id",
                    "start_datum", "next_due", "active",
                ]
                ns = self._merge_for_update(
                    db=db,
                    table="monthlycosts",
                    id_col="id",
                    item_id=monthlycosts_id,
                    payload_obj=payload,
                    fields=fields,
                    normalizer=self._normalize_monthlycosts,
                )
                db.update_monthlycosts(ns)  # erwartet voll befülltes Objekt
            finally:
                db.close()

        def delete_monthlycosts(monthlycosts_id: int) -> None:
            db = DBHandler()
            try:
                db.cursor.execute(
                    "DELETE FROM monthlycosts WHERE id = ?",
                    (monthlycosts_id,),
                )
                if db.cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=404,
                        detail="MonthlyCosts nicht gefunden",
                    )
                db.conn.commit()
            finally:
                db.close()

        # ---- Receipt ----
        def get_receipt() -> List[SchemaReceipt]:
            db = DBHandler()
            try:
                rows = db.load_receipt()
                return [
                    SchemaReceipt(
                        id=r["id"],
                        user_id=r["user_id"],
                        name=r["name"],
                        betrag=r["betrag"],
                        kategorie_id=r["kategorie_id"],
                        konto_id=r["konto_id"],
                        laden_id=r["laden_id"],
                        datum=r["datum"],
                    )
                    for r in rows
                ]
            finally:
                db.close()

        def create_receipt(payload: SchemaReceipt) -> None:
            db = DBHandler()
            try:
                db.insert_receipt(payload)
            finally:
                db.close()

        def update_receipt(receipt_id: int, payload: SchemaReceipt) -> None:
            db = DBHandler()
            try:
                fields = ["user_id", "name", "betrag", "kategorie_id",
                          "konto_id", "laden_id", "datum"]
                ns = self._merge_for_update(
                    db=db,
                    table="receipt",
                    id_col="id",
                    item_id=receipt_id,
                    payload_obj=payload,
                    fields=fields,
                    normalizer=self._normalize_receipt,
                )
                db.update_receipt(ns)
            finally:
                db.close()

        def delete_receipt(receipt_id: int) -> None:
            db = DBHandler()
            try:
                db.cursor.execute("DELETE FROM receipt WHERE id = ?",
                                  (receipt_id,))
                if db.cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=404, detail="receipt nicht gefunden")
                db.conn.commit()
            finally:
                db.close()

        # ---- Securities ----
        def get_securities() -> List[SchemaSecurities]:
            db = DBHandler()
            try:
                rows = db.load_securities()
                return [
                    SchemaSecurities(
                        id=r["id"],
                        name=r["name"],
                        isin=r["isin"],
                        ticker=r["ticker"],
                        instrument=r["instrument"],
                    )
                    for r in rows
                ]
            finally:
                db.close()

        def create_securities(payload: SchemaSecurities) -> None:
            db = DBHandler()
            try:
                db.insert_securities(payload)
            finally:
                db.close()

        def update_securities(
                securities_id: int,
                payload: SchemaSecurities) -> None:
            db = DBHandler()
            try:
                ids = [r["id"] for r in db.load_securities()]
                if securities_id not in ids:
                    raise HTTPException(
                        status_code=404, detail="Securities nicht gefunden")
                db.update_securities(
                    SimpleNamespace(id=securities_id, **payload.__dict__))
            finally:
                db.close()

        def delete_securities(securities_id: int) -> None:
            db = DBHandler()
            try:
                db.cursor.execute(
                    "DELETE FROM securities WHERE id = ?", (securities_id,))
                if db.cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=404, detail="Securities nicht gefunden")
                db.conn.commit()
            finally:
                db.close()

        # ---- Savings ----
        def get_savings() -> List[SchemaSparziel]:
            db = DBHandler()
            try:
                rows = db.load_savings()
                return [
                    SchemaSparziel(
                        id=r["id"],
                        name=r["name"],
                        user_id=r["user_id"],
                        konto_id=r["konto_id"],
                        kategorie_id=r["kategorie_id"],
                        betrag=r["betrag"],
                        start_datum=r["start_datum"],
                        end_datum=r["end_datum"],
                        sparrate_e=r["sparrate_e"],
                        sparrate_p=r["sparrate_p"],
                    )
                    for r in rows
                ]
            finally:
                db.close()

        def create_savings(payload: SchemaSparziel) -> None:
            db = DBHandler()
            try:
                db.insert_savings(payload)
            finally:
                db.close()

        def update_savings(savings_id: int, payload: SchemaSparziel) -> None:
            db = DBHandler()
            try:
                fields = ["name", "user_id", "konto_id", "kategorie_id",
                          "betrag", "start_datum", "end_datum",
                          "sparrate_e", "sparrate_p"]
                ns = self._merge_for_update(
                    db=db,
                    table="savings",
                    id_col="id",
                    item_id=savings_id,
                    payload_obj=payload,
                    fields=fields,
                    normalizer=self._normalize_savings,
                )
                db.update_savings(ns)
            finally:
                db.close()

        def delete_savings(savings_id: int) -> None:
            db = DBHandler()
            try:
                db.cursor.execute(
                    "DELETE FROM savings WHERE id = ?", (savings_id,))
                if db.cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=404, detail="savings nicht gefunden")
                db.conn.commit()
            finally:
                db.close()

        # ---- Depot Bewegung ----
        def get_depotbewegung() -> List[SchemaDepotbewegung]:
            db = DBHandler()
            try:
                rows = db.load_depotbewegung()
                return [
                    SchemaDepotbewegung(
                        id=r["id"],
                        user_id=r["user_id"],
                        konto_id=r["konto_id"],
                        securities_id=r["securities_id"],
                        kategorie_id=r["kategorie_id"],
                        type=r["type"],
                        betrag=r["betrag"],
                        anteile=r["anteile"],
                        datum=r["datum"]
                    )
                    for r in rows
                ]
            finally:
                db.close()

        def create_depotbewegung(payload: SchemaDepotbewegung) -> None:
            db = DBHandler()
            try:
                db.insert_depotbewegung(payload)
            finally:
                db.close()

        def update_depotbewegung(
                depotbewegung_id: int,
                payload: SchemaDepotbewegung) -> None:
            db = DBHandler()
            try:
                ids = [r["id"] for r in db.load_depotbewegung()]
                if depotbewegung_id not in ids:
                    raise HTTPException(
                        status_code=404, detail="Depotbewegung nicht gefunden")
                db.update_depotbewegung(
                    SimpleNamespace(id=depotbewegung_id, **payload.__dict__))
            finally:
                db.close()

        def delete_depotbewegung(depotbewegung_id: int) -> None:
            db = DBHandler()
            try:
                db.cursor.execute(
                    "DELETE FROM depotbewegung WHERE id = ?",
                    (depotbewegung_id,))
                if db.cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=404, detail="Depotbewegung nicht gefunden")
                db.conn.commit()
            finally:
                db.close()

        # ---- Depot Stand ----
        def get_depotstand() -> List[SchemaDepotstand]:
            db = DBHandler()
            try:
                rows = db.load_depotstand()
                return [
                    SchemaDepotstand(
                        id=r["id"],
                        user_id=r["user_id"],
                        konto_id=r["konto_id"],
                        securities_id=r["securities_id"],
                        summe_betrag=r["summe_betrag"],
                        summe_anteil=r["summe_anteil"],
                        wert=r["wert"],
                        entwicklung=r["entwicklung"],
                        datum=r["datum"]
                    )
                    for r in rows
                ]
            finally:
                db.close()

        def create_depotstand(payload: SchemaDepotstand) -> None:
            db = DBHandler()
            try:
                db.insert_depotstand(payload)
            finally:
                db.close()

        def update_depotstand(
                depotstand_id: int,
                payload: SchemaDepotstand) -> None:
            db = DBHandler()
            try:
                ids = [r["id"] for r in db.load_depotstand()]
                if depotstand_id not in ids:
                    raise HTTPException(
                        status_code=404, detail="Depotstand nicht gefunden")
                db.update_depotstand(
                    SimpleNamespace(id=depotstand_id, **payload.__dict__))
            finally:
                db.close()

        def delete_depotstand(depotstand_id: int) -> None:
            db = DBHandler()
            try:
                db.cursor.execute(
                    "DELETE FROM depotstand WHERE id = ?", (depotstand_id,))
                if db.cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=404, detail="Depotstand nicht gefunden")
                db.conn.commit()
            finally:
                db.close()

        # ---- Registry: alles an EINER Stelle deklarieren ----
        resources = [
            ("konten", SchemaKonto, SchemaKonto, get_konto, create_konto,
             update_konto, delete_konto, "Konten"),

            ("users",  SchemaUser,  SchemaUser,  get_user,  create_users,
             update_user,  delete_user,  "Users"),

            ("kategorien",  SchemaKategorie,  SchemaKategorie,  get_kategorien,
             create_kategorien, update_kategorien,  delete_kategorien,
             "Kategorien"),

            ("laden",  SchemaLaden,  SchemaLaden,  get_laden,  create_laden,
             update_laden,  delete_laden,  "Laden"),

            ("monthlycosts", SchemaMonthlyCosts, SchemaMonthlyCosts,
             get_monthlycosts, create_monthlycosts, update_monthlycosts,
             delete_monthlycosts, "MonthlyCosts"),

            ("receipt", SchemaReceipt, SchemaReceipt,
             get_receipt, create_receipt, update_receipt, delete_receipt,
             "Receipt"),

            ("securities", SchemaSecurities, SchemaSecurities,
             get_securities, create_securities, update_securities,
             delete_securities, "Securities"),

            ("savings", SchemaSparziel, SchemaSparziel,
             get_savings, create_savings, update_savings,
             delete_savings, "Savings"),

            ("depotbewegung", SchemaDepotbewegung, SchemaDepotbewegung,
             get_depotbewegung, create_depotbewegung, update_depotbewegung,
             delete_depotbewegung, "Depotbewegung"),

            ("depotstand", SchemaDepotstand, SchemaDepotstand,
             get_depotstand, create_depotstand, update_depotstand,
             delete_depotstand, "Depotstand"),

        ]

        for (
            name, dto_in, dto_out, list_fn, create_fn, update_fn, delete_fn,
            tag
        ) in resources:
            self.wire_crud(
                name, dto_in, dto_out, list_fn, create_fn, update_fn,
                delete_fn, tag
            )

        self.router.include_router(opt_router)
        self.router.include_router(jobs)
        self.router.include_router(r_market)
