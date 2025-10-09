from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Callable, Any
from types import SimpleNamespace
from backend.app.database.db_handling import DBHandler
from backend.app.models.schema import SchemaKonto, \
    SchemaUser, SchemaMonthlyCosts, SchemaEinkauf, SchemaKategorie, \
    SchemaOption


class BackendRoutes:

    def __init__(self) -> None:
        self.router = APIRouter()
        self.request_handling()

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
        def list_items(_list_fn=list_fn):
            return _list_fn()

        # POST /{name}
        @r.post("", status_code=201)
        def create_item(payload: Any, _create_fn=create_fn):
            _create_fn(payload)
            return {"ok": True}
        create_item.__annotations__["payload"] = dto_in

        # PUT /{name}/{item_id}
        @r.put("/{item_id}")
        def update_item(item_id: int, payload: Any, _update_fn=update_fn):
            _update_fn(item_id, payload)
            return {"ok": True}
        update_item.__annotations__["payload"] = dto_in

        # DELETE /{name}/{item_id}
        @r.delete("/{item_id}")
        def delete_item(item_id: int, _delete_fn=delete_fn):
            _delete_fn(item_id)
            return {"ok": True}

        self.router.include_router(r)

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
            if payload.entity != "kategorien":
                raise HTTPException(
                    status_code=400,
                    detail="Only 'kategorien' allowed")

            name = payload.name.strip()
            if not name:
                raise HTTPException(status_code=400, detail="Name required")

            db = DBHandler()
            try:
                row = db.cursor.execute(
                    "SELECT id, name FROM kategorien WHERE name = ?", (name,)
                ).fetchone()
                if row:
                    return SchemaOption(id=row["id"], name=row["name"])

                db.cursor.execute(
                    "INSERT INTO kategorien(name) VALUES (?)",
                    (name,))
                new_id = db.cursor.lastrowid
                db.conn.commit()
                return SchemaOption(id=new_id, name=name)
            finally:
                db.close()

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
                        aktien_id=r["aktien_id"],
                        kategorie_id=r["kategorie_id"],
                        ausgangs_konto_id=r["ausgangs_konto_id"],
                        eingangs_konto_id=r["eingangs_konto_id"],
                        start_datum=r["start_datum"],
                        next_due=r["next_due"],
                        active=bool(r["active"]),
                    )
                    for r in rows
                ]
            finally:
                db.close()

        def create_monthlycosts(payload: SchemaMonthlyCosts) -> None:
            db = DBHandler()
            try:
                db.insert_monthlycosts(payload)
            finally:
                db.close()

        def update_monthlycosts(
                monthlycosts_id: int,
                payload: SchemaMonthlyCosts
        ) -> None:
            db = DBHandler()
            try:
                ids = [r["id"] for r in db.load_monthlycosts()]
                if monthlycosts_id not in ids:
                    raise HTTPException(
                        status_code=404,
                        detail="MonthlyCosts nicht gefunden"
                    )
                # DBHandler.update_monthlycosts erwartet ein Objekt mit id
                from types import SimpleNamespace
                db.update_monthlycosts(SimpleNamespace(
                    id=monthlycosts_id,
                    **payload.__dict__
                ))
            finally:
                db.close()

        def delete_monthlycosts(monthlycosts_id: int) -> None:
            db = DBHandler()
            try:
                db.cursor.execute(
                    "DELETE FROM monthlycosts WHERE id = ?",
                    (monthlycosts_id,))
                if db.cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=404,
                        detail="MonthlyCosts nicht gefunden"
                    )
                db.conn.commit()
            finally:
                db.close()

        # ---- Einkauf ----
        def get_einkauf() -> List[SchemaEinkauf]:
            db = DBHandler()
            try:
                rows = db.load_einkauf()
                return [
                    SchemaEinkauf(
                        id=r["id"],
                        user_id=r["user_id"],
                        name=r["name"],
                        betrag=r["betrag"],
                        kategorie_id=r["kategorie_id"],
                        konto_id=r["konto_id"],
                        laden_id=r["laden_id"],
                        ausgabentyp_id=r["ausgabentyp_id"],
                        datum=r["datum"],
                    )
                    for r in rows
                ]
            finally:
                db.close()

        def create_einkauf(payload: SchemaEinkauf) -> None:
            db = DBHandler()
            try:
                db.insert_einkauf(payload)
            finally:
                db.close()

        def update_einkauf(einkauf_id: int, payload: SchemaEinkauf) -> None:
            db = DBHandler()
            try:
                ids = [r["id"] for r in db.load_einkauf()]
                if einkauf_id not in ids:
                    raise HTTPException(
                        status_code=404,
                        detail="Einkauf nicht gefunden"
                    )
                from types import SimpleNamespace
                db.update_einkauf(SimpleNamespace(
                    id=einkauf_id,
                    **payload.__dict__))
            finally:
                db.close()

        def delete_einkauf(einkauf_id: int) -> None:
            db = DBHandler()
            try:
                db.cursor.execute(
                    "DELETE FROM einkauf WHERE id = ?",
                    (einkauf_id,))
                if db.cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=404,
                        detail="Einkauf nicht gefunden")
                db.conn.commit()
            finally:
                db.close()

        # ---- Registry: alles an EINER Stelle deklarieren ----
        resources = [
            ("konten", SchemaKonto, SchemaKonto, get_konto, create_konto,
             update_konto, delete_konto, "Konten"),

            ("users",  SchemaUser,  SchemaUser,  get_user,  create_users,
             update_user,  delete_user,  "Users"),

            ("monthlycosts", SchemaMonthlyCosts, SchemaMonthlyCosts,
             get_monthlycosts, create_monthlycosts, update_monthlycosts,
             delete_monthlycosts, "MonthlyCosts"),

            ("einkauf", SchemaEinkauf, SchemaEinkauf,
             get_einkauf, create_einkauf, update_einkauf, delete_einkauf,
             "Einkauf"),

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
