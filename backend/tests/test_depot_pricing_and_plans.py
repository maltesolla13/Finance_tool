import sqlite3
import unittest
from datetime import date, datetime
from unittest.mock import patch

import pandas as pd
from fastapi import BackgroundTasks

from backend.app.database import db_config
from backend.app.models.schema import SchemaDepotbewegung, SchemaMonthlyCosts
from backend.app.services.apis.backend_api import BackendRoutes
from backend.app.services.apis.market_api import fetch_daily_lows_eur
from backend.app.services.depot.monthly_jobs import run_monthly_securities_jobs
from backend.app.services.depot.daily_jobs import ensure_depotstand_from_last
from backend.app.services.account_overview import account_overview
from backend.app.services.jobs.monthly_and_depot_posting import (
    mirror_depotbewegung_to_kontobewegung,
)
from backend.app.services.jobs.monthly_and_depot_posting import run_monthlycosts_for_date


class MarketSeriesTest(unittest.TestCase):
    def test_weekends_use_preceding_stock_and_fx_quotes(self):
        frames = {
            "NVDA": pd.DataFrame({"Low": [100, 120]}, index=pd.to_datetime(["2026-01-02", "2026-01-05"])),
            "EURUSD=X": pd.DataFrame({"Close": [2, 4]}, index=pd.to_datetime(["2026-01-02", "2026-01-05"])),
        }
        with patch("backend.app.services.apis.market_api.resolve_currency", return_value=("USD", 1)):
            with patch("backend.app.services.apis.market_api.yf.Ticker") as ticker:
                ticker.side_effect = lambda symbol: type("Quote", (), {"history": lambda self, **kwargs: frames[symbol]})()
                values = fetch_daily_lows_eur("NVDA", date(2026, 1, 2), date(2026, 1, 5))
        self.assertEqual(list(values.values()), [50, 50, 50, 30])
        self.assertEqual(ticker.call_count, 2)

    def test_no_future_quote_is_used_before_the_first_available_price(self):
        frame = pd.DataFrame({"Low": [100]}, index=pd.to_datetime(["2026-01-05"]))
        with patch("backend.app.services.apis.market_api.resolve_currency", return_value=("EUR", 1)):
            with patch("backend.app.services.apis.market_api.yf.Ticker") as ticker:
                ticker.return_value.history.return_value = frame
                with self.assertRaises(ValueError):
                    fetch_daily_lows_eur("ETF", date(2026, 1, 2), date(2026, 1, 5))


class MemoryConnection(sqlite3.Connection):
    def close(self):
        pass


class SavingsPlanDepotTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:", factory=MemoryConnection)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        with patch.object(db_config, "get_connection", return_value=self.conn):
            db_config.init_db()
        self.conn.executescript("""
            INSERT INTO user(id,name) VALUES (1,'Anna');
            INSERT INTO konten(id,name) VALUES (1,'Cash'),(2,'Depot');
            INSERT INTO konto_user(konto_id,user_id) VALUES (1,1),(2,1);
            INSERT INTO securities(id,name,isin,ticker,instrument) VALUES (1,'NVIDIA','NVDA','NVDA','Aktie');
        """)
        connection_patch = patch("backend.app.database.db_handling.get_connection", return_value=self.conn)
        connection_patch.start()
        self.addCleanup(connection_patch.stop)
        self.addCleanup(lambda: sqlite3.Connection.close(self.conn))
        for name in ("fetch_low_on_or_after", "fetch_high_on_or_after"):
            quote_patch = patch(
                "backend.app.services.depot.trade_amounts." + name,
                return_value=100,
            )
            quote_patch.start()
            self.addCleanup(quote_patch.stop)

    def plan(self, plan_id):
        self.conn.execute("""
            INSERT INTO monthlycosts (
                id,user_id,name,betrag,securities_id,ausgangs_konto_id,eingangs_konto_id,
                start_datum,next_due,repeat_type,active
            ) VALUES (?,1,'Sparplan',200,1,1,2,'2026-01-01','2026-01-01','MONTHLY',1)
        """, (plan_id,))
        self.conn.commit()

    def test_two_identical_plans_execute_independently_and_refresh_after_commit(self):
        self.plan(1)
        self.plan(2)
        run_date = datetime(2026, 1, 1, 23)
        with patch("backend.app.services.depot.monthly_jobs.fetch_high_on_or_after", return_value=100):
            with patch("backend.app.services.depot.monthly_jobs.refresh_depotstand") as refresh:
                refresh.side_effect = lambda day: self.assertFalse(self.conn.in_transaction)
                result = run_monthly_securities_jobs(run_date)
                self.assertEqual(result["created"], 2)
                refresh.assert_called_once_with(run_date)
                self.conn.execute("UPDATE monthlycosts SET next_due='2026-01-01'")
                self.conn.commit()
                again = run_monthly_securities_jobs(run_date)
        self.assertEqual(again["created"], 0)
        self.assertEqual(self.conn.execute("SELECT SUM(anteile) FROM depotbewegung").fetchone()[0], 4)

    def test_general_job_does_not_advance_security_plan(self):
        self.plan(1)
        run_monthlycosts_for_date(date(2026, 1, 1))
        self.assertEqual(self.conn.execute("SELECT next_due FROM monthlycosts").fetchone()[0], "2026-01-01")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM kontobewegung").fetchone()[0], 0)

    def test_new_plan_starts_with_first_purchase_and_queues_execution(self):
        routes = BackendRoutes().router.routes
        create = next(r.endpoint for r in routes if r.path == "/monthlycosts" and "POST" in r.methods)
        tasks = BackgroundTasks()
        create(SchemaMonthlyCosts(
            user_id=1, name="Sparplan", betrag=200, securities_id=1,
            ausgangs_konto_id=1, eingangs_konto_id=2, active=True,
            start_datum=date(2026, 1, 1), next_due=date(2026, 2, 1),
            repeat_type="MONTHLY",
        ), tasks)
        self.assertEqual(self.conn.execute("SELECT next_due FROM monthlycosts").fetchone()[0], "2026-01-01")
        self.assertEqual(len(tasks.tasks), 1)
        self.assertEqual(tasks.tasks[0].func.__name__, "refresh_monthly_securities")
        with patch("backend.app.services.depot.monthly_jobs.fetch_high_on_or_after", return_value=100), \
                patch("backend.app.services.depot.monthly_jobs.refresh_depotstand"):
            run_monthly_securities_jobs(datetime(2026, 1, 1, 23))
        movement = self.conn.execute("SELECT anteile, datum FROM depotbewegung").fetchone()
        self.assertEqual(tuple(movement), (2, "2026-01-01"))

    def test_booking_create_edit_delete_each_queue_daily_valuation(self):
        routes = BackendRoutes().router.routes

        def endpoint(method, path):
            return next(r.endpoint for r in routes if r.path == path and method in r.methods)

        tasks = BackgroundTasks()
        result = endpoint("POST", "/depotbewegung")(SchemaDepotbewegung(
            user_id=1, konto_id=2, ausgangs_konto_id=1, eingangs_konto_id=2,
            securities_id=1, type="Kauf", betrag=200, anteile=2, datum=date(2026, 1, 1),
        ), tasks)
        self.assertTrue(result["valuation_pending"])
        movement_id = self.conn.execute("SELECT id FROM depotbewegung").fetchone()[0]
        endpoint("PUT", "/depotbewegung/{item_id}")(
            movement_id, SchemaDepotbewegung(anteile=3, betrag=300), tasks,
        )
        self.assertEqual(self.conn.execute("SELECT anteile FROM depotbewegung").fetchone()[0], 2.99)
        endpoint("DELETE", "/depotbewegung/{item_id}")(movement_id, tasks)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM depotbewegung").fetchone()[0], 0)
        self.assertEqual([task.func.__name__ for task in tasks.tasks], ["refresh_depotstand"] * 3)

    def book(self, kind, amount=None, shares=None):
        routes = BackendRoutes().router.routes
        create = next(
            r.endpoint for r in routes
            if r.path == "/depotbewegung" and "POST" in r.methods
        )
        sale = kind == "Verkauf"
        create(SchemaDepotbewegung(
            user_id=1, konto_id=2, ausgangs_konto_id=2 if sale else 1,
            eingangs_konto_id=1 if sale else 2, securities_id=1,
            type=kind, betrag=amount, anteile=shares,
            datum=date(2026, 1, 1),
        ), BackgroundTasks())
        return self.conn.execute(
            "SELECT * FROM depotbewegung ORDER BY id DESC LIMIT 1"
        ).fetchone()

    def test_trade_fee_reduces_purchase_shares_and_sale_payout(self):
        buy = self.book("Kauf", amount=80)
        sale = self.book("Verkauf", amount=80)
        self.assertEqual((buy["betrag"], buy["anteile"]), (80, 0.79))
        self.assertEqual((sale["betrag"], sale["anteile"]), (80, 0.8))
        self.assertEqual(buy["gebuehr"], 1)
        self.assertEqual(sale["gebuehr"], 1)
        overview = account_overview(self.conn, 1, date(2026, 1, 1))
        self.assertEqual(overview["balance"], -1)
        self.assertEqual(overview["income"], 79)
        self.assertEqual(overview["expenses"], -80)
        mirror_depotbewegung_to_kontobewegung()
        mirror_depotbewegung_to_kontobewegung()
        mirrored = account_overview(self.conn, 1, date(2026, 1, 1))
        self.assertEqual(mirrored["balance"], -1)
        self.assertEqual(len(mirrored["transactions"]), 2)

    def test_share_input_adds_fee_to_buy_budget_only(self):
        buy = self.book("Kauf", shares=0.8)
        sale = self.book("Verkauf", shares=0.8)
        self.assertEqual(buy["betrag"], 81)
        self.assertEqual(sale["betrag"], 80)
        self.assertEqual(buy["anteile"], 0.8)
        self.assertEqual(sale["anteile"], 0.8)

    def test_savings_plan_has_no_fee(self):
        plan = self.book("Sparplan", amount=80, shares=0.8)
        self.assertEqual(plan["betrag"], 80)
        self.assertEqual(plan["anteile"], 0.8)
        self.assertEqual(plan["gebuehr"], 0)

    def test_daily_and_account_profit_include_both_trade_fees(self):
        self.book("Kauf", amount=80)
        self.book("Verkauf", amount=79)
        with patch(
            "backend.app.services.depot.daily_jobs.fetch_daily_lows_eur"
        ) as prices:
            ensure_depotstand_from_last(date(2026, 1, 1))
            prices.assert_not_called()
        row = self.conn.execute("SELECT * FROM depotstand").fetchone()
        self.assertEqual(row["summe_anteil"], 0)
        self.assertEqual(row["summe_betrag"], 2)
        self.assertEqual(row["entwicklung"], -2)
        overview = account_overview(self.conn, 2, date(2026, 1, 1))
        self.assertEqual(overview["purchase_value"], 80)
        self.assertEqual(overview["portfolio_profit"], -2)

    def test_repeated_update_does_not_charge_fee_again(self):
        buy = self.book("Kauf", amount=80)
        update = next(
            r.endpoint for r in BackendRoutes().router.routes
            if r.path == "/depotbewegung/{item_id}" and "PUT" in r.methods
        )
        for _ in range(2):
            update(buy["id"], SchemaDepotbewegung(
                betrag=80, anteile=0.79,
            ), BackgroundTasks())
        row = self.conn.execute("SELECT * FROM depotbewegung").fetchone()
        self.assertEqual(row["betrag"], 80)
        self.assertEqual(row["anteile"], 0.79)
        self.assertEqual(row["gebuehr"], 1)

    def test_too_small_budget_is_not_booked(self):
        from fastapi import HTTPException

        for kind, amount in (("Kauf", 1), ("Verkauf", 0.5)):
            with self.subTest(kind=kind), self.assertRaises(HTTPException):
                self.book(kind, amount=amount)
        count = self.conn.execute(
            "SELECT COUNT(*) FROM depotbewegung"
        ).fetchone()[0]
        self.assertEqual(count, 0)
