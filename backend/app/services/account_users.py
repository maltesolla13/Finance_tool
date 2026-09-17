from fastapi import HTTPException


def init_account_users(conn):
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='konto_user'"
    ).fetchone()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS konto_user (
            konto_id INTEGER NOT NULL REFERENCES konten(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES user(id) ON DELETE RESTRICT,
            PRIMARY KEY (konto_id, user_id)
        )
    """)
    # Existing accounts have an unambiguous owner if only one user exists.
    # Run once so later restarts never undo manually edited assignments.
    if not exists:
        users = conn.execute("SELECT id FROM user").fetchall()
        if len(users) == 1:
            conn.execute(
                "INSERT INTO konto_user (konto_id, user_id) SELECT id, ? FROM konten",
                (users[0][0],),
            )


def list_accounts(conn):
    accounts = {}
    for row in conn.execute("""
        SELECT k.id, k.name, ku.user_id
        FROM konten k LEFT JOIN konto_user ku ON ku.konto_id = k.id
        ORDER BY k.name COLLATE NOCASE, k.id, ku.user_id
    """):
        account = accounts.setdefault(row["id"], {
            "id": row["id"], "name": row["name"], "user_ids": [],
        })
        if row["user_id"] is not None:
            account["user_ids"].append(row["user_id"])
    return list(accounts.values())


def save_account(conn, name, user_ids, account_id=None):
    if account_id is not None:
        current = conn.execute("SELECT name FROM konten WHERE id=?", (account_id,)).fetchone()
        if current is None:
            raise HTTPException(404, "Konto nicht gefunden.")
        if name is None:
            name = current["name"]
        if user_ids is None:
            user_ids = [r[0] for r in conn.execute(
                "SELECT user_id FROM konto_user WHERE konto_id=?", (account_id,)
            )]
    name = (name or "").strip()
    if not name:
        raise HTTPException(422, "Bitte einen Kontonamen angeben.")
    user_ids = sorted(set(user_ids or []))
    if not user_ids:
        raise HTTPException(422, "Jedem Konto muss mindestens ein User zugeordnet sein.")
    known = {r[0] for r in conn.execute("SELECT id FROM user")}
    if not set(user_ids) <= known:
        raise HTTPException(422, "Ein ausgewaehlter User existiert nicht.")
    duplicate = conn.execute("SELECT id FROM konten WHERE name=?", (name,)).fetchone()
    if duplicate is not None and duplicate[0] != account_id:
        raise HTTPException(409, "Ein Konto mit diesem Namen existiert bereits.")
    with conn:
        if account_id is None:
            account_id = conn.execute("INSERT INTO konten(name) VALUES (?)", (name,)).lastrowid
        else:
            conn.execute("UPDATE konten SET name=? WHERE id=?", (name, account_id))
        conn.execute("DELETE FROM konto_user WHERE konto_id=?", (account_id,))
        conn.executemany(
            "INSERT INTO konto_user(konto_id, user_id) VALUES (?, ?)",
            [(account_id, user_id) for user_id in user_ids],
        )
    return account_id


ACCOUNT_FIELDS = {
    "receipt": ("konto_id",),
    "savings": ("konto_id",),
    "kontobewegung": ("konto_id",),
    "depotstand": ("konto_id",),
    "savings_execution": ("konto_id",),
    "depotbewegung": ("konto_id", "ausgangs_konto_id", "eingangs_konto_id"),
    "monthlycosts": ("ausgangs_konto_id", "eingangs_konto_id"),
    "monthlycosts_execution": ("ausgangs_konto_id", "eingangs_konto_id"),
}


def resolve_payload_user(conn, resource, payload, item_id=None):
    fields = ACCOUNT_FIELDS.get(resource)
    if not fields:
        return payload
    values = dict(payload.__dict__)
    if item_id is not None:
        current = conn.execute(f"SELECT * FROM {resource} WHERE id=?", (item_id,)).fetchone()
        if current is None:
            raise HTTPException(404, "Eintrag nicht gefunden.")
        # Preserve historical attribution when no account/user change is requested.
        if not any(values.get(key) is not None and values[key] != current[key]
                   for key in ("user_id", *fields)):
            return payload
        values = {**dict(current), **{k: v for k, v in values.items() if v is not None}}
    account_ids = {values[key] for key in fields if values.get(key) is not None}
    if not account_ids:
        raise HTTPException(422, "Bitte ein Konto auswaehlen.")
    allowed = None
    for account_id in account_ids:
        owners = {r[0] for r in conn.execute(
            "SELECT user_id FROM konto_user WHERE konto_id=?", (account_id,)
        )}
        if not owners:
            raise HTTPException(422, "Bitte dem Konto zuerst mindestens einen User zuordnen.")
        allowed = owners if allowed is None else allowed & owners
    if not allowed:
        raise HTTPException(422, "Die gewaehlten Konten haben keinen gemeinsamen User.")
    user_id = values.get("user_id")
    if user_id is None and len(allowed) == 1:
        user_id = next(iter(allowed))
    if user_id not in allowed:
        raise HTTPException(422, "Bitte einen zugeordneten User auswaehlen.")
    payload.user_id = user_id
    return payload
