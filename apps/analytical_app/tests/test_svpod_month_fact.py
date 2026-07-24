"""Тесты расчёта факта SVPOD (вкладка выполнение по месяцам)."""
from __future__ import annotations

from decimal import Decimal

from django.test import SimpleTestCase

from apps.analytical_app.pages.economist.svpod.page import (
    _as_float,
    _month_closed_enabled,
    compute_svpod_month_fact,
)


class SvpodMonthFactTests(SimpleTestCase):
    def test_month_closed_reporting_is_2_and_3(self):
        row = {"новые": 10, "в_тфомс": 20, "оплачено": 30, "исправлено": 5}
        fact = compute_svpod_month_fact(
            row,
            7,
            reporting_month=7,
            current_day=15,
            month_closed=True,
            total_ispravleno_all_months=5,
        )
        self.assertEqual(fact, 50.0)  # 20+30

    def test_month_closed_past_is_paid_only(self):
        row = {"новые": 10, "в_тфомс": 20, "оплачено": 30}
        fact = compute_svpod_month_fact(
            row,
            5,
            reporting_month=7,
            current_day=15,
            month_closed=True,
        )
        self.assertEqual(fact, 30.0)

    def test_open_reporting_includes_new_and_fixed(self):
        row = {"новые": 10, "в_тфомс": 20, "оплачено": 30}
        fact = compute_svpod_month_fact(
            row,
            7,
            reporting_month=7,
            current_day=15,
            month_closed=False,
            total_ispravleno_all_months=7,
            manually_selected=False,
        )
        self.assertEqual(fact, 67.0)  # 10+20+30+7

    def test_manual_month_without_closed_is_paid(self):
        row = {"новые": 10, "в_тфомс": 20, "оплачено": 30}
        fact = compute_svpod_month_fact(
            row,
            7,
            reporting_month=7,
            current_day=15,
            month_closed=False,
            manually_selected=True,
        )
        self.assertEqual(fact, 30.0)

    def test_switch_parser(self):
        self.assertTrue(_month_closed_enabled(["closed"]))
        self.assertFalse(_month_closed_enabled([]))
        self.assertTrue(_month_closed_enabled(True))

    def test_as_float_decimal_and_arithmetic(self):
        plan = _as_float(Decimal("1500.50"))
        fact = _as_float(Decimal("200.25"))
        # Раньше Decimal - float падал TypeError в режиме финансов
        self.assertEqual(plan - fact, 1300.25)
        self.assertEqual(_as_float(None), 0.0)
