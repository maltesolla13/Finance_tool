import sqlite3
import unittest
from datetime import date
from fastapi import HTTPException
from backend.app.services.account_overview import account_overview


class AccountOverviewTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
            CREATE TABLE konten (id INTEGER, name TEXT);
            CREATE TABLE user (id INTEGER, name TEXT);
            CREATE TABLE kategorien (id INTEGER, name TEXT);
            CREATE TABLE securities (id INTEGER, name TEXT);
            CREATE TABLE kontobewegung (
                id INTEGER, konto_id INTEGER, user_id INTEGER, kategorie_id INTEGER,
                datum TEXT, name TEXT, type TEXT, betrag REAL);
            CREATE TABLE receipt (
                id INTEGER, konto_id INTEGER, user_id INTEGER, kategorie_id INTEGER,
                datum TEXT, name TEXT, betrag REAL);
            CREATE TABLE depotbewegung (
                id INTEGER, konto_id INTEGER, ausgangs_konto_id INTEGER, eingangs_konto_id INTEGER,
                user_id INTEGER, kategorie_id INTEGER, securities_id INTEGER,
                datum TEXT, type TEXT, betrag REAL);
            CREATE TABLE monthlycosts_execution (
                id INTEGER, monthlycost_id INTEGER, ausgangs_konto_id INTEGER, eingangs_konto_id INTEGER,
                user_id INTEGER, kategorie_id INTEGER, securities_id INTEGER,
                execution_datum TEXT, name TEXT, status TEXT, betrag REAL);
            CREATE TABLE kontostand (
                id INTEGER, konto_id INTEGER, user_id INTEGER, datum TEXT, kontostand REAL);
            INSERT INTO konten VALUES (1, 'Gemeinschaft'), (2, 'Depot'), (3, 'Leer');
            INSERT INTO user VALUES (1, 'Anna'), (2, 'Ben');
            INSERT INTO kategorien VALUES (1, 'Essen');
            INSERT INTO securities VALUES (1, 'ETF');
        """)

    def tearDown(self):
        self.conn.close()

    def overview(self, account=1):
        return account_overview(self.conn, account, date(2026, 9, 17))

    def test_combines_users_receipts_and_signed_movements(self):
        self.conn.executescript("""
            INSERT INTO kontobewegung VALUES (1,1,1,1,'2026-09-01','Gehalt','Eingang',1000);
            INSERT INTO receipt VALUES (1,1,2,1,'2026-09-02','Essen',25.34);
            INSERT INTO receipt VALUES (2,3,1,1,'2026-09-02','Anderes Konto',10);
        """)
        data = self.overview()
        self.assertEqual(data["balance"], 974.66)
        self.assertEqual(data["transactions"][0]["user"], "Ben")
        self.assertEqual(data["transactions"][0]["balance"], 974.66)
        self.assertEqual(data["history"][-1]["balance"], 974.66)
        self.assertEqual(len(data["transactions"]), 2)

    def test_cash_and_depot_legs_and_mirror_deduplication(self):
        self.conn.execute("INSERT INTO depotbewegung VALUES (5,2,1,2,1,1,1,'2026-09-01','Kauf',100)")
        self.assertEqual(self.overview()["balance"], -100)
        depot = self.overview(2)
        self.assertEqual(depot["balance"], 0)
        self.assertEqual(depot["transactions"][0]["amount"], -100)
        self.assertEqual(depot["transactions"][0]["cash_change"], 0)
        self.conn.execute("INSERT INTO kontobewegung VALUES (7,1,1,1,'2026-09-01','AUTO: depot#5 kauf','Depot Kauf',-100)")
        self.assertEqual(self.overview()["balance"], -100)
        self.assertEqual(len(self.overview()["transactions"]), 1)

    def test_only_executed_monthly_bookings_and_no_double_count(self):
        self.conn.executescript("""
            INSERT INTO monthlycosts_execution VALUES (1,9,1,3,1,1,NULL,'2026-09-01','Miete','EXECUTED',100);
            INSERT INTO monthlycosts_execution VALUES (2,10,1,3,1,1,NULL,'2026-09-01','Geplant','PENDING',200);
        """)
        self.assertEqual(self.overview()["balance"], -100)
        self.conn.execute("INSERT INTO kontobewegung VALUES (7,1,1,1,'2026-09-01','AUTO: monthlycost#9 (Miete) - Ausgang','MonthlyCosts',-100)")
        self.assertEqual(self.overview()["balance"], -100)
        self.assertEqual(len(self.overview()["transactions"]), 1)
        self.assertEqual(self.overview(3)["balance"], 100)

    def test_checkpoints_and_future_bookings(self):
        self.conn.executescript("""
            INSERT INTO kontostand VALUES (1,1,1,'2026-08-31',500);
            INSERT INTO kontostand VALUES (2,1,2,'2026-08-31',200);
            INSERT INTO receipt VALUES (1,1,1,1,'2026-09-01','Essen',20);
            INSERT INTO receipt VALUES (2,1,2,1,'2026-10-01','Zukunft',50);
        """)
        data = self.overview()
        self.assertEqual(data["balance"], 680)
        self.assertEqual(data["transactions"][0]["balance"], 630)
        self.assertTrue(data["transactions"][0]["future"])
        self.assertTrue(data["has_checkpoints"])
        self.assertEqual(data["expenses"], -20)

    def test_empty_and_missing_account(self):
        self.assertEqual(self.overview(3)["balance"], 0)
        self.assertEqual(self.overview(3)["transactions"], [])
        with self.assertRaises(HTTPException) as error:
            self.overview(999)
        self.assertEqual(error.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()

