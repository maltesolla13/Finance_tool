from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Callable, Any
from types import SimpleNamespace
from zoneinfo import ZoneInfo
from backend.app.services.depot.daily_jobs import ensure_depotstand_from_last
from backend.app.services.depot.monthly_jobs import run_monthly_securities_jobs
from backend.app.services.jobs.monthly_and_depot_posting import (
    _backfill_monthlycost_executions_until,
    _first_due_after,
    _next_due_date,
    _set_monthlycost_next_due,
    _to_date,
    run_monthlycosts_for_date,
)
from backend.app.services.jobs.savings_execution import (
    recalc_all_savings, recalc_savings)
from backend.app.database.db_handling import DBHandler
from backend.app.services.account_users import list_accounts, save_account, resolve_payload_user
from backend.app.services.account_overview import account_overview
from backend.app.services.apis.market_api import (
    fetch_high_on_or_after, fetch_low_on_or_after, fetch_low_on_or_before
)
from backend.app.models.schema import SchemaKonto, \
    SchemaUser, SchemaMonthlyCosts, SchemaReceipt, SchemaKategorie, \
    SchemaOption, SchemaSecurities, SchemaLaden, SchemaSparziel, \
    SchemaDepotbewegung, SchemaDepotstand, SchemaKontobewegung, \
    SchemaMonthlyCostsExecution, SchemaSavingsExecution

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
        def create_item(payload: dto_in):
            if name in {"receipt", "savings", "kontobewegung", "depotbewegung",
                        "depotstand", "monthlycosts", "monthlycosts_execution",
                        "savings_execution"}:
                db = DBHandler()
                try:
                    payload = resolve_payload_user(db.conn, name, payload)
                finally:
                    db.close()
            create_fn(payload)
            return {"ok": True}
        create_item.__annotations__["payload"] = dto_in

        # PUT /{name}/{item_id}
        @r.put("/{item_id}")
        def update_item(item_id: int, payload: dto_in):
            if name in {"receipt", "savings", "kontobewegung", "depotbewegung",
                        "depotstand", "monthlycosts", "monthlycosts_execution",
                        "savings_execution"}:
                db = DBHandler()
                try:
                    payload = resolve_payload_user(db.conn, name, payload, item_id)
                finally:
                    db.close()
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
        return x.isoformat() if isinstance(x, (date, datetime)) else x

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
                  "eingangs_konto_id", "securities_id", "custom_interval"):
            if out.get(k) is not None:
                out[k] = int(out[k])
        # Datum → ISO-String
        if out.get("start_datum") is not None:
            out["start_datum"] = self._dt(out["start_datum"])
        if out.get("next_due") is not None:
            out["next_due"] = self._dt(out["next_due"])
        # active → 0/1 (INTEGER)
        out["active"] = 1 if bool(out.get("active")) else 0
        out["repeat_type"] = (out.get("repeat_type") or "MONTHLY").upper()
        if out.get("custom_unit") is not None:
            out["custom_unit"] = out["custom_unit"].upper()
        start_date = _to_date(out.get("start_datum"))
        next_due_date = _to_date(out.get("next_due")) if out.get(
            "next_due") else None
        if start_date and (not next_due_date or next_due_date <= start_date):
            out["next_due"] = _next_due_date(
                start_date,
                out.get("repeat_type"),
                out.get("custom_interval"),
                out.get("custom_unit"),
            )
        return out

    def _normalize_monthlycosts_execution(self, d: dict) -> dict:
        out = dict(d)
        for k in ("monthlycost_id", "user_id", "kategorie_id",
                  "ausgangs_konto_id", "eingangs_konto_id",
                  "securities_id"):
            if out.get(k) is not None:
                out[k] = int(out[k])
        if out.get("execution_datum") is not None:
            out["execution_datum"] = self._dt(out["execution_datum"])
        out["status"] = (out.get("status") or "PENDING").upper()
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

    def _normalize_depotbewegung(self, d: dict) -> dict:
        out = dict(d)
        for k in ("user_id", "konto_id", "ausgangs_konto_id",
                  "eingangs_konto_id", "securities_id", "kategorie_id"):
            if out.get(k) is not None:
                out[k] = int(out[k])
        if out.get("datum") is not None:
            out["datum"] = self._dt(out["datum"])

        type_lower = (out.get("type") or "").strip().lower()
        if out.get("konto_id") is None:
            if type_lower == "kauf":
                out["konto_id"] = out.get("eingangs_konto_id")
            elif type_lower == "verkauf":
                out["konto_id"] = out.get("ausgangs_konto_id")
            else:
                out["konto_id"] = (
                    out.get("eingangs_konto_id")
                    or out.get("ausgangs_konto_id")
                )
        if out.get("ausgangs_konto_id") is None:
            out["ausgangs_konto_id"] = out.get("konto_id")
        if out.get("eingangs_konto_id") is None:
            out["eingangs_konto_id"] = out.get("konto_id")
        return out

    def _is_gehalt_category(self, db: DBHandler, kategorie_id: int | None):
        if not kategorie_id:
            return False
        row = db.cursor.execute(
            "SELECT name FROM kategorien WHERE id = ?", (kategorie_id,)
        ).fetchone()
        return bool(row and (row["name"] or "").strip().lower() == "gehalt")

    def _invalidate_depotstand_from(
            self,
            db: DBHandler,
            *,
            user_id: int | None,
            konto_id: int | None,
            securities_id: int | None,
            datum) -> None:
        if not konto_id or not securities_id or not datum:
            return
        db.cursor.execute("""
            DELETE FROM depotstand
            WHERE konto_id = ?
              AND securities_id = ?
              AND (? IS NULL OR user_id = ?)
              AND DATE(datum) >= DATE(?)
        """, (
            konto_id,
            securities_id,
            user_id,
            user_id,
            self._dt(datum),
        ))

    # ---- Request/Route-Definitionen -----------------------------------------
    def request_handling(self) -> None:
        @self.router.get("/accounts/{account_id}/summary", tags=["Konten"])
        def get_account_summary(account_id: int):
            db = DBHandler()
            try:
                return account_overview(db.conn, account_id, datetime.now(TZ).date())
            finally:
                db.close()

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
        portfolio = APIRouter(prefix="/portfolio", tags=["Portfolio"])

        @jobs.post("/monthly-securities/run")
        def run_monthly(date: str | None = None):
            run_date = _parse_date_qs(date)
            return run_monthly_securities_jobs(run_date)

        @jobs.post("/monthlycosts/run")
        def run_monthlycosts(date: str | None = None):
            run_date = _parse_date_qs(date)
            run_monthlycosts_for_date(run_date)
            return {"ok": True, "date": run_date.strftime("%Y-%m-%d")}

        @jobs.post("/savings/recalculate")
        def run_savings_recalculate():
            recalc_all_savings()
            return {"ok": True}

        @jobs.post("/depotstand/run")
        def run_depotstand(date: str | None = None):
            run_date = _parse_date_qs(date)
            return ensure_depotstand_from_last(run_date)

        def _range_start(period: str | None) -> str | None:
            today = datetime.now(TZ).date()
            p = (period or "MAX").upper()
            if p == "WEEK":
                return (today - date.resolution * 7).isoformat()
            if p == "MONTH":
                return (today.replace(day=1)).isoformat()
            if p == "HALFYEAR":
                return (today - date.resolution * 183).isoformat()
            if p == "YEAR":
                return (today - date.resolution * 365).isoformat()
            if p == "5Y":
                return (today - date.resolution * 365 * 5).isoformat()
            return None

        def _parse_account_ids(account_ids: str | None) -> list[int]:
            if not account_ids:
                return []
            out = []
            for raw in account_ids.split(","):
                raw = raw.strip()
                if raw:
                    out.append(int(raw))
            return out

        def _placeholders(values: list[int]) -> str:
            return ",".join("?" for _ in values)

        @portfolio.get("/summary")
        def portfolio_summary(
            account_ids: str | None = Query(None),
            period: str = Query("MAX"),
        ):
            selected_ids = _parse_account_ids(account_ids)
            period_start = _range_start(period)
            db = DBHandler()
            try:
                account_rows = db.cursor.execute("""
                    SELECT DISTINCT k.id, k.name
                    FROM konten k
                    WHERE k.id IN (
                        SELECT eingangs_konto_id
                        FROM depotbewegung
                        WHERE eingangs_konto_id IS NOT NULL
                    )
                    OR k.id IN (
                        SELECT eingangs_konto_id
                        FROM monthlycosts
                        WHERE securities_id IS NOT NULL
                          AND eingangs_konto_id IS NOT NULL
                    )
                    ORDER BY k.name
                """).fetchall()
                accounts = [
                    {"id": r["id"], "name": r["name"]}
                    for r in account_rows
                ]
                if not selected_ids:
                    selected_ids = [a["id"] for a in accounts]

                if not selected_ids:
                    return {
                        "accounts": accounts,
                        "selected_account_ids": [],
                        "period": period,
                        "overview": [],
                        "totals": {
                            "invested": 0,
                            "value": 0,
                            "development": 0,
                            "development_pct": 0,
                        },
                        "allocation": [],
                        "assets": [],
                    }

                account_sql = _placeholders(selected_ids)
                account_params = tuple(selected_ids)
                movement_rows = db.cursor.execute(f"""
                    SELECT db.user_id, db.konto_id, db.securities_id,
                           db.type, db.betrag, db.anteile, DATE(db.datum) AS d,
                           s.name, s.instrument, s.ticker, s.isin
                    FROM depotbewegung db
                    JOIN securities s ON s.id = db.securities_id
                    WHERE db.konto_id IN ({account_sql})
                    ORDER BY DATE(db.datum), db.id
                """, account_params).fetchall()

                price_cache = {}

                def price_for(ticker: str | None, iso_date: str):
                    if not ticker:
                        return 0.0
                    key = (ticker, iso_date)
                    if key not in price_cache:
                        try:
                            dt = datetime.fromisoformat(iso_date[:10])
                            price_cache[key] = float(
                                fetch_low_on_or_before(ticker, dt)
                            )
                        except Exception:
                            price_cache[key] = 0.0
                    return price_cache[key]

                asset_meta = {}
                state = {}
                dates = []
                for r in movement_rows:
                    sec_id = r["securities_id"]
                    asset_meta[sec_id] = {
                        "name": r["name"],
                        "instrument": r["instrument"],
                        "ticker": r["ticker"],
                        "isin": r["isin"],
                    }
                    if sec_id not in state:
                        state[sec_id] = {"shares": 0.0, "invested": 0.0}
                    sign = -1 if (r["type"] or "").lower() == "verkauf" else 1
                    state[sec_id]["shares"] += sign * float(r["anteile"] or 0)
                    state[sec_id]["invested"] += sign * float(r["betrag"] or 0)
                    if r["d"] not in dates:
                        dates.append(r["d"])

                if not dates:
                    overview = []
                    asset_map = {}
                else:
                    today_iso = datetime.now(TZ).date().isoformat()
                    if today_iso not in dates:
                        dates.append(today_iso)
                    dates = sorted(dates)

                    running = {
                        sec_id: {"shares": 0.0, "invested": 0.0}
                        for sec_id in asset_meta
                    }
                    moves_by_date = {}
                    for r in movement_rows:
                        moves_by_date.setdefault(r["d"], []).append(r)

                    overview = []
                    series_by_sec = {sec_id: [] for sec_id in asset_meta}
                    for d in dates:
                        for r in moves_by_date.get(d, []):
                            sec_id = r["securities_id"]
                            sign = (
                                -1
                                if (r["type"] or "").lower() == "verkauf"
                                else 1
                            )
                            running[sec_id]["shares"] += sign * float(
                                r["anteile"] or 0)
                            running[sec_id]["invested"] += sign * float(
                                r["betrag"] or 0)

                        total_invested = 0.0
                        total_value = 0.0
                        total_shares = 0.0
                        for sec_id, values in running.items():
                            meta = asset_meta[sec_id]
                            sec_value = values["shares"] * price_for(
                                meta["ticker"], d)
                            total_invested += values["invested"]
                            total_value += sec_value
                            total_shares += values["shares"]
                            series_by_sec[sec_id].append({
                                "date": d,
                                "shares": values["shares"],
                                "invested": values["invested"],
                                "value": sec_value,
                            })
                        if not period_start or d >= period_start:
                            overview.append({
                                "date": d,
                                "shares": total_shares,
                                "invested": total_invested,
                                "value": total_value,
                            })

                    latest_state = {
                        sec_id: vals
                        for sec_id, vals in running.items()
                        if abs(vals["shares"]) > 0.0000001
                    }
                    asset_map = {}
                    for sec_id, vals in latest_state.items():
                        meta = asset_meta[sec_id]
                        latest_value = vals["shares"] * price_for(
                            meta["ticker"], today_iso)
                        filtered_series = [
                            p for p in series_by_sec[sec_id]
                            if not period_start or p["date"] >= period_start
                        ]
                        asset_map[sec_id] = {
                            "security_id": sec_id,
                            "name": meta["name"],
                            "instrument": meta["instrument"],
                            "ticker": meta["ticker"],
                            "isin": meta["isin"],
                            "shares": vals["shares"],
                            "value": latest_value,
                            "invested": vals["invested"],
                            "series": filtered_series,
                            "active_savings": 0,
                            "next_execution_date": None,
                        }

                totals = {
                    "invested": sum(a["invested"] for a in asset_map.values()),
                    "value": sum(a["value"] for a in asset_map.values()),
                }
                totals["development"] = totals["value"] - totals["invested"]
                totals["development_pct"] = (
                    (totals["development"] / totals["invested"]) * 100
                    if totals["invested"] else 0
                )

                allocation_map = {}
                for asset in asset_map.values():
                    instrument = asset["instrument"] or "Unbekannt"
                    allocation_map[instrument] = (
                        allocation_map.get(instrument, 0) + asset["value"]
                    )
                total_value = totals["value"]
                allocation = [
                    {
                        "id": instrument,
                        "label": instrument,
                        "value": value,
                        "percentage": (
                            (value / total_value) * 100
                            if total_value else 0
                        ),
                    }
                    for instrument, value in sorted(allocation_map.items())
                ]

                savings_rows = db.cursor.execute(f"""
                    SELECT mc.securities_id,
                           s.name, s.instrument, s.ticker, s.isin,
                           SUM(COALESCE(mc.betrag, 0)) AS amount,
                           MIN(DATE(mc.next_due)) AS next_due
                    FROM monthlycosts
                    mc JOIN securities s ON s.id = mc.securities_id
                    WHERE mc.active = 1
                      AND mc.securities_id IS NOT NULL
                      AND mc.eingangs_konto_id IN ({account_sql})
                    GROUP BY mc.securities_id, s.name, s.instrument,
                             s.ticker, s.isin
                """, account_params).fetchall()
                for r in savings_rows:
                    asset = asset_map.get(r["securities_id"])
                    if not asset:
                        asset = {
                            "security_id": r["securities_id"],
                            "name": r["name"],
                            "instrument": r["instrument"],
                            "ticker": r["ticker"],
                            "isin": r["isin"],
                            "shares": 0,
                            "value": 0,
                            "invested": 0,
                            "series": [],
                            "active_savings": 0,
                            "next_execution_date": None,
                        }
                        asset_map[r["securities_id"]] = asset
                    if asset:
                        asset["active_savings"] = float(r["amount"] or 0)
                        asset["next_execution_date"] = r["next_due"]

                assets = sorted(
                    asset_map.values(),
                    key=lambda item: item["value"],
                    reverse=True,
                )

                return {
                    "accounts": accounts,
                    "selected_account_ids": selected_ids,
                    "period": period,
                    "overview": overview,
                    "totals": totals,
                    "allocation": allocation,
                    "assets": assets,
                }
            finally:
                db.close()

        # ---- Konto ----
        def get_konto() -> List[SchemaKonto]:
            db = DBHandler()
            try:
                return [SchemaKonto(**account) for account in list_accounts(db.conn)]
            finally:
                db.close()

        def create_konto(payload: SchemaKonto) -> None:
            db = DBHandler()
            try:
                save_account(db.conn, payload.name, payload.user_ids)
            finally:
                db.close()

        def update_konto(konto_id: int, payload: SchemaKonto) -> None:
            db = DBHandler()
            try:
                ids = [r["id"] for r in db.load_konten()]
                if konto_id not in ids:
                    raise HTTPException(status_code=404,
                                        detail="Konto not found")
                save_account(db.conn, payload.name, payload.user_ids, konto_id)
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
                if db.cursor.execute(
                    "SELECT 1 FROM konto_user WHERE user_id=? LIMIT 1", (user_id,)
                ).fetchone():
                    raise HTTPException(409, "Bitte zuerst die Konten dieses Users neu zuordnen.")
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
                        repeat_type=r["repeat_type"],
                        custom_interval=r["custom_interval"],
                        custom_unit=r["custom_unit"],
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
                p.repeat_type = (p.repeat_type or "MONTHLY").upper()
                p.custom_interval = (
                    int(p.custom_interval)
                    if p.custom_interval is not None else None
                )
                p.custom_unit = (
                    p.custom_unit.upper() if p.custom_unit else None
                )
                start_date = _to_date(p.start_datum)
                next_due_date = _to_date(p.next_due) if p.next_due else None
                if not next_due_date or next_due_date <= start_date:
                    p.next_due = _next_due_date(
                        start_date, p.repeat_type, p.custom_interval,
                        p.custom_unit
                    )

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
                new_id = db.cursor.lastrowid
                run_date = datetime.now(TZ).date()
                if p.active:
                    _backfill_monthlycost_executions_until(
                        db,
                        monthlycost_id=new_id,
                        user_id=p.user_id,
                        name=p.name,
                        betrag=p.betrag,
                        anteil=p.anteil,
                        securities_id=p.securities_id,
                        kategorie_id=p.kategorie_id,
                        ausgangs_konto_id=p.ausgangs_konto_id,
                        eingangs_konto_id=p.eingangs_konto_id,
                        start_datum=p.start_datum,
                        repeat_type=p.repeat_type,
                        custom_interval=p.custom_interval,
                        custom_unit=p.custom_unit,
                        until_date=run_date,
                    )
                    next_due = _first_due_after(
                        p.start_datum,
                        run_date,
                        p.repeat_type,
                        p.custom_interval,
                        p.custom_unit,
                    )
                    if next_due:
                        _set_monthlycost_next_due(
                            db,
                            mc_id=new_id,
                            user_id=p.user_id,
                            name=p.name,
                            betrag=p.betrag,
                            anteil=p.anteil,
                            securities_id=p.securities_id,
                            kategorie_id=p.kategorie_id,
                            ausgangs_konto_id=p.ausgangs_konto_id,
                            eingangs_konto_id=p.eingangs_konto_id,
                            start_datum=p.start_datum,
                            next_due=next_due,
                            repeat_type=p.repeat_type,
                            custom_interval=p.custom_interval,
                            custom_unit=p.custom_unit,
                            active=p.active,
                        )
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
                    "start_datum", "next_due", "repeat_type",
                    "custom_interval", "custom_unit", "active",
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

        # ---- MonthlyCostsExecution ----
        def get_monthlycosts_execution() -> List[SchemaMonthlyCostsExecution]:
            db = DBHandler()
            try:
                rows = db.load_monthlycosts_execution()
                return [
                    SchemaMonthlyCostsExecution(
                        id=r["id"],
                        monthlycost_id=r["monthlycost_id"],
                        user_id=r["user_id"],
                        name=r["name"],
                        betrag=r["betrag"],
                        anteil=r["anteil"],
                        securities_id=r["securities_id"],
                        kategorie_id=r["kategorie_id"],
                        ausgangs_konto_id=r["ausgangs_konto_id"],
                        eingangs_konto_id=r["eingangs_konto_id"],
                        execution_datum=(r["execution_datum"][:10]
                                         if r["execution_datum"]
                                         else None),
                        status=r["status"],
                    )
                    for r in rows
                ]
            finally:
                db.close()

        def create_monthlycosts_execution(
                payload: SchemaMonthlyCostsExecution) -> None:
            db = DBHandler()
            try:
                data = self._normalize_monthlycosts_execution(
                    dict(payload.__dict__)
                )
                p = SimpleNamespace(**data)

                def exists(table, id_):
                    if id_ is None:
                        return True
                    row = db.cursor.execute(
                        f"SELECT 1 FROM {table} WHERE id=?", (id_,)).fetchone()
                    return row is not None

                if not exists("monthlycosts", p.monthlycost_id):
                    raise HTTPException(
                        400, detail="Unbekannter monthlycost_id")
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

                db.insert_monthlycosts_execution(p)
                db.conn.commit()
            finally:
                db.close()

        def update_monthlycosts_execution(
                execution_id: int,
                payload: SchemaMonthlyCostsExecution) -> None:
            db = DBHandler()
            try:
                fields = [
                    "monthlycost_id", "user_id", "name", "betrag", "anteil",
                    "securities_id", "kategorie_id", "ausgangs_konto_id",
                    "eingangs_konto_id", "execution_datum", "status",
                ]
                ns = self._merge_for_update(
                    db=db,
                    table="monthlycosts_execution",
                    id_col="id",
                    item_id=execution_id,
                    payload_obj=payload,
                    fields=fields,
                    normalizer=self._normalize_monthlycosts_execution,
                )
                db.update_monthlycosts_execution(ns)
            finally:
                db.close()

        def delete_monthlycosts_execution(execution_id: int) -> None:
            db = DBHandler()
            try:
                db.cursor.execute(
                    "DELETE FROM monthlycosts_execution WHERE id = ?",
                    (execution_id,),
                )
                if db.cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=404,
                        detail="MonthlyCostsExecution nicht gefunden",
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
                db.conn.commit()
                if self._is_gehalt_category(db, payload.kategorie_id):
                    recalc_all_savings()
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
                db.conn.commit()
                if self._is_gehalt_category(db, ns.kategorie_id):
                    recalc_all_savings()
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
                recalc_all_savings()
            finally:
                db.close()

        # ---- Kontobewegung ----
        def get_kontobewegung() -> List[SchemaKontobewegung]:
            db = DBHandler()
            try:
                rows = db.load_kontobewegung()
                return [
                    SchemaKontobewegung(
                        id=r["id"],
                        user_id=r["user_id"],
                        name=r["name"],
                        betrag=r["betrag"],
                        kategorie_id=r["kategorie_id"],
                        konto_id=r["konto_id"],
                        type=r["type"],
                        datum=r["datum"],
                    )
                    for r in rows
                ]
            finally:
                db.close()

        def create_kontobewegung(payload: SchemaKontobewegung) -> None:
            db = DBHandler()
            try:
                db.insert_kontobewegung(payload)
                db.conn.commit()
                if self._is_gehalt_category(db, payload.kategorie_id):
                    recalc_all_savings()
            finally:
                db.close()

        def update_kontobewegung(
                kontobewegung_id: int,
                payload: SchemaKontobewegung) -> None:
            db = DBHandler()
            try:
                fields = ["user_id", "name", "betrag", "kategorie_id",
                          "konto_id", "type", "datum"]
                ns = self._merge_for_update(
                    db=db,
                    table="kontobewegung",
                    id_col="id",
                    item_id=kontobewegung_id,
                    payload_obj=payload,
                    fields=fields,
                    normalizer=self._normalize_receipt,
                )
                db.cursor.execute("""
                    UPDATE kontobewegung
                    SET user_id = ?, name = ?, betrag = ?, kategorie_id = ?,
                        konto_id = ?, type = ?, datum = ?
                    WHERE id = ?
                """, (
                    ns.user_id, ns.name, ns.betrag, ns.kategorie_id,
                    ns.konto_id, ns.type, ns.datum, kontobewegung_id,
                ))
                db.conn.commit()
                recalc_all_savings()
            finally:
                db.close()

        def delete_kontobewegung(kontobewegung_id: int) -> None:
            db = DBHandler()
            try:
                db.cursor.execute(
                    "DELETE FROM kontobewegung WHERE id = ?",
                    (kontobewegung_id,),
                )
                db.conn.commit()
                recalc_all_savings()
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
                new_id = db.cursor.lastrowid
                db.conn.commit()
            finally:
                db.close()
            recalc_savings(new_id)

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
                db.conn.commit()
            finally:
                db.close()
            recalc_savings(savings_id)

        def delete_savings(savings_id: int) -> None:
            db = DBHandler()
            try:
                db.cursor.execute(
                    "DELETE FROM savings WHERE id = ?", (savings_id,))
                if db.cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=404, detail="savings nicht gefunden")
                db.cursor.execute(
                    "DELETE FROM savings_execution WHERE savings_id = ?",
                    (savings_id,),
                )
                db.conn.commit()
            finally:
                db.close()

        def get_savings_execution() -> List[SchemaSavingsExecution]:
            db = DBHandler()
            try:
                rows = db.cursor.execute("""
                    SELECT id, savings_id, user_id, konto_id, kategorie_id,
                           income_kontobewegung_id, execution_month,
                           income_amount, amount, status
                    FROM savings_execution
                    ORDER BY execution_month, id
                """).fetchall()
                return [
                    SchemaSavingsExecution(
                        id=r["id"],
                        savings_id=r["savings_id"],
                        user_id=r["user_id"],
                        konto_id=r["konto_id"],
                        kategorie_id=r["kategorie_id"],
                        income_kontobewegung_id=r["income_kontobewegung_id"],
                        execution_month=r["execution_month"],
                        income_amount=r["income_amount"],
                        amount=r["amount"],
                        status=r["status"],
                    )
                    for r in rows
                ]
            finally:
                db.close()

        def create_savings_execution(
                _payload: SchemaSavingsExecution) -> None:
            raise HTTPException(
                status_code=405,
                detail="SavingsExecution wird automatisch berechnet")

        def update_savings_execution(
                _execution_id: int,
                _payload: SchemaSavingsExecution) -> None:
            raise HTTPException(
                status_code=405,
                detail="SavingsExecution wird automatisch berechnet")

        def delete_savings_execution(execution_id: int) -> None:
            db = DBHandler()
            try:
                db.cursor.execute(
                    "DELETE FROM savings_execution WHERE id = ?",
                    (execution_id,),
                )
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
                        ausgangs_konto_id=r["ausgangs_konto_id"],
                        eingangs_konto_id=r["eingangs_konto_id"],
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
                data = self._normalize_depotbewegung(payload.__dict__)
                db.insert_depotbewegung(SimpleNamespace(**data))
                self._invalidate_depotstand_from(
                    db,
                    user_id=data.get("user_id"),
                    konto_id=data.get("konto_id"),
                    securities_id=data.get("securities_id"),
                    datum=data.get("datum"),
                )
                db.conn.commit()
            finally:
                db.close()
            ensure_depotstand_from_last(datetime.now(TZ))

        def update_depotbewegung(
                depotbewegung_id: int,
                payload: SchemaDepotbewegung) -> None:
            db = DBHandler()
            try:
                fields = [
                    "user_id", "konto_id", "ausgangs_konto_id",
                    "eingangs_konto_id", "securities_id", "kategorie_id",
                    "type", "betrag", "anteile", "datum",
                ]
                ns = self._merge_for_update(
                    db=db,
                    table="depotbewegung",
                    id_col="id",
                    item_id=depotbewegung_id,
                    payload_obj=payload,
                    fields=fields,
                    normalizer=self._normalize_depotbewegung,
                )
                db.update_depotbewegung(ns)
                self._invalidate_depotstand_from(
                    db,
                    user_id=ns.user_id,
                    konto_id=ns.konto_id,
                    securities_id=ns.securities_id,
                    datum=ns.datum,
                )
                db.conn.commit()
            finally:
                db.close()
            ensure_depotstand_from_last(datetime.now(TZ))

        def delete_depotbewegung(depotbewegung_id: int) -> None:
            db = DBHandler()
            try:
                old = db.cursor.execute("""
                    SELECT user_id, konto_id, securities_id, datum
                    FROM depotbewegung
                    WHERE id = ?
                """, (depotbewegung_id,)).fetchone()
                db.cursor.execute(
                    "DELETE FROM depotbewegung WHERE id = ?",
                    (depotbewegung_id,))
                if db.cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=404, detail="Depotbewegung nicht gefunden")
                if old:
                    self._invalidate_depotstand_from(
                        db,
                        user_id=old["user_id"],
                        konto_id=old["konto_id"],
                        securities_id=old["securities_id"],
                        datum=old["datum"],
                    )
                db.conn.commit()
            finally:
                db.close()
            ensure_depotstand_from_last(datetime.now(TZ))

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

            ("monthlycosts_execution", SchemaMonthlyCostsExecution,
             SchemaMonthlyCostsExecution, get_monthlycosts_execution,
             create_monthlycosts_execution, update_monthlycosts_execution,
             delete_monthlycosts_execution, "MonthlyCostsExecution"),

            ("receipt", SchemaReceipt, SchemaReceipt,
             get_receipt, create_receipt, update_receipt, delete_receipt,
             "Receipt"),

            ("kontobewegung", SchemaKontobewegung, SchemaKontobewegung,
             get_kontobewegung, create_kontobewegung, update_kontobewegung,
             delete_kontobewegung, "Kontobewegung"),

            ("securities", SchemaSecurities, SchemaSecurities,
             get_securities, create_securities, update_securities,
             delete_securities, "Securities"),

            ("savings", SchemaSparziel, SchemaSparziel,
             get_savings, create_savings, update_savings,
             delete_savings, "Savings"),

            ("savings_execution", SchemaSavingsExecution,
             SchemaSavingsExecution, get_savings_execution,
             create_savings_execution, update_savings_execution,
             delete_savings_execution, "SavingsExecution"),

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
        self.router.include_router(portfolio)
        self.router.include_router(r_market)
