import sqlite3
import unittest
from datetime import date, timedelta
from unittest.mock import patch

from backend.app.services.depot.daily_jobs import ensure_depotstand_from_last


class DailyDepotTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
            CREATE TABLE securities (id INTEGER PRIMARY KEY, ticker TEXT);
            CREATE TABLE depotbewegung (
                id INTEGER PRIMARY KEY, user_id INTEGER, konto_id INTEGER, securities_id INTEGER,
                type TEXT, betrag REAL, anteile REAL, datum TEXT);
            CREATE TABLE depotstand (
                id INTEGER PRIMARY KEY, user_id INTEGER, konto_id INTEGER, securities_id INTEGER,
                summe_betrag REAL, summe_anteil REAL, wert REAL, entwicklung REAL, datum TEXT);
            INSERT INTO securities VALUES (1, 'NVDA'), (2, 'ETF');
        """)
        self.connection_patch = patch("backend.app.database.db_handling.get_connection", return_value=self.conn)
        self.close_patch = patch("backend.app.database.db_handling.DBHandler.close", lambda db: None)
        self.connection_patch.start()
        self.close_patch.start()
        self.addCleanup(self.connection_patch.stop)
        self.addCleanup(self.close_patch.stop)
        self.addCleanup(self.conn.close)
        self.prices = patch("backend.app.services.depot.daily_jobs.fetch_daily_lows_eur", side_effect=self.quotes)
        self.price_mock = self.prices.start()
        self.addCleanup(self.prices.stop)

    @staticmethod
    def quotes(ticker, start, end):
        result = {}
        while start <= end:
            result[start] = 100 if start.month == 1 else 120
            start += timedelta(days=1)
        return result

    def buy(self, day, shares=2, kind="Kauf", user=1, account=1, security=1):
        self.conn.execute("""
            INSERT INTO depotbewegung(user_id,konto_id,securities_id,type,betrag,anteile,datum)
            VALUES (?,?,?,?,?,?,?)
        """, (user, account, security, kind, abs(shares) * 100, shares, day))
        self.conn.commit()

    def rebuild(self, end="2026-02-15"):
        return ensure_depotstand_from_last(date.fromisoformat(end))

    def rows(self):
        return [tuple(row) for row in self.conn.execute(
            "SELECT user_id,konto_id,securities_id,datum,summe_anteil,wert FROM depotstand ORDER BY datum,id"
        )]

    def test_nvidia_example_has_every_calendar_day_and_cumulative_shares(self):
        self.buy("2026-01-01", 2)
        self.buy("2026-02-01", 1)
        result = self.rebuild()
        rows = self.rows()
        self.assertEqual(result["written"], 46)
        self.assertEqual(rows[0][-3:], ("2026-01-01", 2, 200))
        self.assertEqual(rows[30][-3:], ("2026-01-31", 2, 200))
        self.assertEqual(rows[31][-3:], ("2026-02-01", 3, 360))
        self.assertEqual(rows[-1][-3:], ("2026-02-15", 3, 360))
        self.assertEqual(self.price_mock.call_count, 1)

    def test_sales_sparplans_and_zero_days(self):
        self.buy("2026-01-01", 2)
        self.buy("2026-01-02", 1, "Sparplan")
        self.buy("2026-01-03", 1, "Verkauf")
        self.buy("2026-01-04", 2, "Verkauf")
        self.rebuild("2026-01-06")
        self.assertEqual([r[-2] for r in self.rows()], [2, 3, 2, 0, 0, 0])
        self.assertEqual(self.price_mock.call_args.args[2], date(2026, 1, 3))

    def test_moving_first_purchase_and_changing_account_removes_old_values(self):
        self.buy("2026-01-01")
        self.rebuild("2026-01-05")
        self.conn.execute("UPDATE depotbewegung SET datum='2026-01-03', konto_id=2")
        self.conn.commit()
        self.rebuild("2026-01-05")
        self.assertEqual(len(self.rows()), 3)
        self.assertTrue(all(row[1] == 2 for row in self.rows()))
        self.assertEqual(self.rows()[0][3], "2026-01-03")

    def test_deleting_last_purchase_clears_orphaned_values(self):
        self.buy("2026-01-01")
        self.rebuild("2026-01-05")
        self.conn.execute("DELETE FROM depotbewegung")
        self.conn.commit()
        self.rebuild("2026-01-05")
        self.assertEqual(self.rows(), [])

    def test_rerun_null_user_and_multiple_securities_do_not_duplicate(self):
        self.buy("2026-01-01", user=None)
        self.buy("2026-01-01", user=2, security=2)
        self.rebuild("2026-01-03")
        expected = self.rows()
        self.rebuild("2026-01-03")
        self.assertEqual(self.rows(), expected)
        self.assertEqual(len(expected), 6)

    def test_price_failure_preserves_previous_snapshot_and_closes_transaction(self):
        self.buy("2026-01-01")
        self.rebuild("2026-01-03")
        expected = self.rows()
        self.buy("2026-01-02", 1)
        self.price_mock.side_effect = ValueError("No quotes")
        with self.assertRaises(ValueError):
            self.rebuild("2026-01-03")
        self.assertEqual(self.rows(), expected)
        self.assertFalse(self.conn.in_transaction)

    def test_insert_failure_rolls_back_the_delete(self):
        self.buy("2026-01-01")
        self.rebuild("2026-01-03")
        expected = self.rows()
        self.conn.execute("""
            CREATE TRIGGER fail_insert BEFORE INSERT ON depotstand
            BEGIN SELECT RAISE(ABORT, 'test failure'); END
        """)
        self.conn.commit()
        with self.assertRaises(sqlite3.IntegrityError):
            self.rebuild("2026-01-03")
        self.assertEqual(self.rows(), expected)

    def test_change_during_pricing_retries_with_fresh_transactions(self):
        self.buy("2026-01-01")
        calls = 0
        def quotes(ticker, start, end):
            nonlocal calls
            calls += 1
            if calls == 1:
                self.buy("2026-01-02", 1)
            return self.quotes(ticker, start, end)
        self.price_mock.side_effect = quotes
        self.rebuild("2026-01-03")
        self.assertEqual([row[-2] for row in self.rows()], [2, 3, 3])
        self.assertEqual(calls, 2)

    def test_future_purchases_and_non_position_events_do_not_change_holdings(self):
        self.buy("2026-02-01")
        self.buy("2026-01-01", 1, "Dividende")
        self.rebuild("2026-01-31")
        self.assertEqual(self.rows(), [])
        self.price_mock.assert_not_called()

