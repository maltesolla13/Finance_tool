from fastapi import APIRouter, HTTPException
from typing import List, Callable, Any
from types import SimpleNamespace
from backend.app.database.db_handling import DBHandler
from backend.app.models.schema import SchemaKonto, SchemaUser


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

        # ---- Users (gleiches Muster) ----
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

        # ---- Registry: alles an EINER Stelle deklarieren ----
        resources = [
            ("konten", SchemaKonto, SchemaKonto, get_konto, create_konto,
             update_konto, delete_konto, "Konten"),

            ("users",  SchemaUser,  SchemaUser,  get_user,  create_users,
             update_user,  delete_user,  "Users"),
            # später: ("stocks", StockCreate, StockOut, stocks_list, ... ,
            # "Stocks"),
            # später: ("bewegungen", BewegungCreate, BewegungOut, ...),
        ]

        for (
            name, dto_in, dto_out, list_fn, create_fn, update_fn, delete_fn,
            tag
        ) in resources:
            self.wire_crud(
                name, dto_in, dto_out, list_fn, create_fn, update_fn,
                delete_fn, tag
            )
