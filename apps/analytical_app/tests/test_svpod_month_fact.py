"""Тесты расчёта факта SVPOD (вкладка выполнение по месяцам)."""
from __future__ import annotations

from decimal import Decimal

from django.test import SimpleTestCase

from apps.analytical_app.pages.economist.svpod.page import (
    _as_float,
    _month_closed_enabled,
    _svpod_carry_ispravleno,
    compute_svpod_month_fact,
    svpod_month_is_open,
)


_ROW = {"новые": 10, "в_тфомс": 20, "оплачено": 30, "исправлено": 5}


class SvpodMonthFactTests(SimpleTestCase):
    def test_month_closed_reporting_is_2_and_3(self):
        fact = compute_svpod_month_fact(
            _ROW,
            7,
            reporting_month=7,
            current_day=15,
            month_closed=True,
        )
        self.assertEqual(fact, 50.0)  # 20+30

    def test_month_closed_past_is_paid_only(self):
        fact = compute_svpod_month_fact(
            _ROW,
            5,
            reporting_month=7,
            current_day=15,
            month_closed=True,
        )
        self.assertEqual(fact, 30.0)

    def test_open_reporting_includes_this_month_fixed_not_year_total(self):
        row = {**_ROW, "исправлено": 7}
        fact = compute_svpod_month_fact(
            row,
            7,
            reporting_month=7,
            current_day=15,
            month_closed=False,
            calendar_month=7,
            manually_selected=False,
        )
        self.assertEqual(fact, 67.0)  # 10+20+30+7 этого месяца

    def test_manual_month_without_closed_is_paid(self):
        fact = compute_svpod_month_fact(
            _ROW,
            7,
            reporting_month=7,
            current_day=15,
            month_closed=False,
            calendar_month=9,
            manually_selected=True,
        )
        self.assertEqual(fact, 30.0)

    def test_sept1_july_is_paid_only(self):
        """1 сентября: отчётный август, июль уже закрыт — только оплачено."""
        fact = compute_svpod_month_fact(
            _ROW,
            7,
            reporting_month=8,
            current_day=1,
            month_closed=False,
            calendar_month=9,
            manually_selected=False,
        )
        self.assertEqual(fact, 30.0)
        self.assertFalse(
            svpod_month_is_open(
                7,
                reporting_month=8,
                current_day=1,
                calendar_month=9,
                month_closed=False,
                manually_selected=False,
            )
        )

    def test_sept1_august_still_open(self):
        fact = compute_svpod_month_fact(
            _ROW,
            8,
            reporting_month=8,
            current_day=1,
            month_closed=False,
            calendar_month=9,
            manually_selected=False,
        )
        self.assertEqual(fact, 65.0)  # 10+20+30+5

    def test_sept8_august_grace_until_10th(self):
        """После 5-го отчётный сентябрь, август открыт до 10-го."""
        fact = compute_svpod_month_fact(
            _ROW,
            8,
            reporting_month=9,
            current_day=8,
            month_closed=False,
            calendar_month=9,
            manually_selected=False,
        )
        self.assertEqual(fact, 65.0)

    def test_sept15_august_paid_only(self):
        """После 10-го август закрыт — в Факте только оплачено."""
        fact = compute_svpod_month_fact(
            _ROW,
            8,
            reporting_month=9,
            current_day=15,
            month_closed=False,
            calendar_month=9,
            manually_selected=False,
        )
        self.assertEqual(fact, 30.0)

    def test_sept17_carry_ispravleno_into_september(self):
        """17 сентября: исправлено августа уходит в Факт сентября."""
        rows = {
            8: {"исправлено": 5696, "оплачено": 4669, "новые": 0, "в_тфомс": 0},
            9: {"исправлено": 0, "оплачено": 0, "новые": 2550, "в_тфомс": 0},
        }
        carry = _svpod_carry_ispravleno(
            rows,
            reporting_month=9,
            current_day=17,
            calendar_month=9,
            month_closed=False,
            manually_selected=False,
        )
        self.assertEqual(carry, 5696.0)

        sept = compute_svpod_month_fact(
            rows[9],
            9,
            reporting_month=9,
            current_day=17,
            month_closed=False,
            calendar_month=9,
            manually_selected=False,
            carry_ispravleno=carry,
        )
        self.assertEqual(sept, 2550.0 + 5696.0)

        aug = compute_svpod_month_fact(
            rows[8],
            8,
            reporting_month=9,
            current_day=17,
            month_closed=False,
            calendar_month=9,
            manually_selected=False,
        )
        self.assertEqual(aug, 4669.0)

    def test_grace_august_keeps_own_fixed_not_in_carry(self):
        """До 10-го августа своё исправлено остаётся в августе, не в переносе."""
        rows = {
            7: {"исправлено": 100, "оплачено": 10, "новые": 0, "в_тфомс": 0},
            8: {"исправлено": 50, "оплачено": 20, "новые": 0, "в_тфомс": 0},
            9: {"исправлено": 0, "оплачено": 0, "новые": 5, "в_тфомс": 0},
        }
        carry = _svpod_carry_ispravleno(
            rows,
            reporting_month=9,
            current_day=8,
            calendar_month=9,
            month_closed=False,
            manually_selected=False,
        )
        self.assertEqual(carry, 100.0)  # только июль; август ещё открыт

    def test_switch_parser(self):
        self.assertTrue(_month_closed_enabled(["closed"]))
        self.assertFalse(_month_closed_enabled([]))
        self.assertTrue(_month_closed_enabled(True))

    def test_as_float_decimal_and_arithmetic(self):
        plan = _as_float(Decimal("1500.50"))
        fact = _as_float(Decimal("200.25"))
        self.assertEqual(plan - fact, 1300.25)
        self.assertEqual(_as_float(None), 0.0)
