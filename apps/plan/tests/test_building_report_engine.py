from django.test import SimpleTestCase

import pandas as pd

from apps.plan.services.building_report_engine import (
    accumulate_pair,
    pivot_report,
    LAYOUT_INDICATOR_BUILDING,
    LAYOUT_BUILDING_INDICATOR,
    LAYOUT_INDICATOR_BUILDING_MONTHS,
    _month_fact,
)


class BuildingReportEngineUnitTests(SimpleTestCase):
    def test_month_fact_presented(self):
        data = {"новые": 1, "в_тфомс": 2, "оплачено": 10, "исправлено": 3}
        self.assertEqual(_month_fact(data, 3, 5, "presented"), 10)
        self.assertEqual(_month_fact(data, 5, 5, "presented"), 1 + 2 + 10 + 3)

    def test_month_fact_paid(self):
        data = {"оплачено": 7, "новые": 100}
        self.assertEqual(_month_fact(data, 1, 1, "paid"), 7)

    def test_accumulate_pair_balance(self):
        plan = {1: 100, 2: 100}
        fact_rows = [
            {"month": 1, "оплачено": 80, "новые": 0, "в_тфомс": 0, "исправлено": 0},
            {"month": 2, "оплачено": 50, "новые": 10, "в_тфомс": 5, "исправлено": 0},
        ]
        months, cum_plan, cum_fact, balance = accumulate_pair(
            plan, fact_rows, reporting_month=2, payment_type="presented"
        )
        self.assertEqual(cum_plan, 200)
        # m1: paid 80; m2 reporting: 10+5+50+0=65
        self.assertEqual(cum_fact, 80 + 65)
        self.assertEqual(len(months), 2)
        # balance after m1 = 100-80=20; m2 plan=100+20=120, fact=65, balance=55
        self.assertEqual(balance, 55)

    def test_pivot_indicator_building(self):
        long_df = pd.DataFrame(
            [
                {
                    "group_id": 1,
                    "group_path": "A \\ B",
                    "building_id": 10,
                    "building_name": "Корпус 1",
                    "month": None,
                    "plan": 100,
                    "fact": 40,
                    "balance": 60,
                    "pct": 40.0,
                    "is_total": True,
                },
                {
                    "group_id": 1,
                    "group_path": "A \\ B",
                    "building_id": 10,
                    "building_name": "Корпус 1",
                    "month": 1,
                    "plan": 50,
                    "fact": 20,
                    "balance": 30,
                    "pct": 40.0,
                    "is_total": False,
                },
            ]
        )
        pivoted = pivot_report(long_df, LAYOUT_INDICATOR_BUILDING)
        self.assertEqual(list(pivoted.columns)[:2], ["Индикатор", "Корпус"])
        self.assertEqual(len(pivoted), 1)
        self.assertEqual(pivoted.iloc[0]["План"], 100)

        by_building = pivot_report(long_df, LAYOUT_BUILDING_INDICATOR)
        self.assertEqual(list(by_building.columns)[:2], ["Корпус", "Индикатор"])

        months = pivot_report(long_df, LAYOUT_INDICATOR_BUILDING_MONTHS)
        self.assertIn("1", months.columns)
        self.assertIn("Итого", months.columns)
        self.assertGreaterEqual(len(months), 1)
