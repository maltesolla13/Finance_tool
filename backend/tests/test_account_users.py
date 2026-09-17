import asyncio
import json
import sqlite3
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI, HTTPException
from backend.app.services.account_users import (
    init_account_users, list_accounts, resolve_payload_user, save_account,
)
from backend.app.services.apis.backend_api import BackendRoutes


async def request(app, method, path, payload=None):
    body = json.dumps(payload).encode() if payload is not None else b""
    messages = []
    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}
    async def send(message):
        messages.append(message)
    await app({
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
        "method": method, "scheme": "http", "path": path, "raw_path": path.encode(),
        "query_string": b"", "root_path": "",
        "headers": [(b"content-type", b"application/json")],
        "server": ("test", 80), "client": ("test", 123),
    }, receive, send)
    status = next(m["status"] for m in messages if m["type"] == "http.response.start")
    content = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    return status, json.loads(content)


class AccountUsersTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript("""
            CREATE TABLE user (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
            CREATE TABLE konten (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
            CREATE TABLE receipt (id INTEGER PRIMARY KEY, user_id INTEGER, konto_id INTEGER);
            INSERT INTO user VALUES (1, 'Anna');
            INSERT INTO konten VALUES (1, 'Altbestand');
        """)
        init_account_users(self.conn)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def add_second_user(self):
        self.conn.execute("INSERT INTO user VALUES (2, 'Ben')")
        self.conn.commit()

    def test_migration_assigns_sole_user_and_does_not_reset_changes(self):
        self.assertEqual(list_accounts(self.conn)[0]["user_ids"], [1])
        self.add_second_user()
        save_account(self.conn, "Altbestand", [2], 1)
        init_account_users(self.conn)
        self.assertEqual(list_accounts(self.conn)[0]["user_ids"], [2])

    def test_shared_account_and_required_valid_owners(self):
        self.add_second_user()
        account_id = save_account(self.conn, "Gemeinsam", [1, 2, 2])
        self.assertEqual(next(a for a in list_accounts(self.conn) if a["id"] == account_id)["user_ids"], [1, 2])
        for owners in ([], None, [999]):
            with self.subTest(owners=owners), self.assertRaises(HTTPException):
                save_account(self.conn, "Ungueltig", owners)
        with self.assertRaises(HTTPException):
            save_account(self.conn, "Altbestand", [], 1)
        self.assertEqual(list_accounts(self.conn)[0]["user_ids"], [1])

    def test_auto_user_and_shared_selection(self):
        payload = SimpleNamespace(konto_id=1, user_id=None)
        self.assertEqual(resolve_payload_user(self.conn, "receipt", payload).user_id, 1)
        self.add_second_user()
        save_account(self.conn, "Altbestand", [1, 2], 1)
        with self.assertRaises(HTTPException):
            resolve_payload_user(self.conn, "receipt", SimpleNamespace(konto_id=1, user_id=None))
        self.assertEqual(resolve_payload_user(self.conn, "receipt", SimpleNamespace(konto_id=1, user_id=2)).user_id, 2)

    def test_dual_accounts_require_common_user(self):
        self.add_second_user()
        account_id = save_account(self.conn, "Ben", [2])
        payload = SimpleNamespace(ausgangs_konto_id=1, eingangs_konto_id=account_id, user_id=None)
        with self.assertRaises(HTTPException):
            resolve_payload_user(self.conn, "monthlycosts", payload)
        save_account(self.conn, "Gemeinsam", [1, 2], account_id)
        self.assertEqual(resolve_payload_user(self.conn, "monthlycosts", payload).user_id, 1)

    def test_history_is_not_reassigned_but_invalid_new_user_is_rejected(self):
        self.conn.execute("INSERT INTO receipt VALUES (1, 1, 1)")
        self.add_second_user()
        save_account(self.conn, "Altbestand", [2], 1)
        payload = SimpleNamespace(konto_id=None, user_id=None)
        self.assertIs(resolve_payload_user(self.conn, "receipt", payload, 1), payload)
        with self.assertRaises(HTTPException):
            resolve_payload_user(self.conn, "receipt", SimpleNamespace(konto_id=1, user_id=1))

    def test_account_api_accepts_json_and_persists_assignments(self):
        conn = self.conn
        class FakeDB:
            def __init__(self):
                self.conn = conn
                self.cursor = conn.cursor()
            def load_konten(self):
                return conn.execute("SELECT id, name FROM konten").fetchall()
            def close(self):
                conn.commit()
        app = FastAPI()
        app.include_router(BackendRoutes().router)
        with patch("backend.app.services.apis.backend_api.DBHandler", FakeDB):
            status, _ = asyncio.run(request(app, "POST", "/konten", {"name": "Neu", "user_ids": [1]}))
            self.assertEqual(status, 201)
            status, accounts = asyncio.run(request(app, "GET", "/konten"))
            self.assertEqual(status, 200)
            self.assertTrue(any(a["name"] == "Neu" and a["user_ids"] == [1] for a in accounts))
            status, _ = asyncio.run(request(app, "POST", "/konten", {"name": "Ohne User", "user_ids": []}))
            self.assertEqual(status, 422)
            status, _ = asyncio.run(request(app, "PUT", "/konten/1", {"name": "Umbenannt", "user_ids": [1]}))
            self.assertEqual(status, 200)
            status, _ = asyncio.run(request(app, "DELETE", "/users/1"))
            self.assertEqual(status, 409)


if __name__ == "__main__":
    unittest.main()
