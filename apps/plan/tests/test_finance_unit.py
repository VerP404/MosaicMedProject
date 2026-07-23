"""Тесты единицы финансов (руб / тыс. руб.)."""
from __future__ import annotations

from django.test import TestCase

from apps.home.models import MainSettings
from apps.plan.services.finance_unit import (
    FINANCE_UNIT_RUBLES,
    FINANCE_UNIT_THOUSANDS,
    convert_month_map_units,
    display_to_rubles,
    get_default_finance_unit,
    rubles_to_display,
    scale_kind_payload_amounts,
    scale_rows_money,
)


class FinanceUnitHelpersTests(TestCase):
    def test_rubles_passthrough(self):
        self.assertEqual(rubles_to_display(1234.56, FINANCE_UNIT_RUBLES), 1234.56)
        self.assertEqual(display_to_rubles(1234.56, FINANCE_UNIT_RUBLES), 1234.56)

    def test_thousands_roundtrip(self):
        self.assertEqual(rubles_to_display(1_500_000, FINANCE_UNIT_THOUSANDS), 1500.0)
        self.assertEqual(display_to_rubles(1500, FINANCE_UNIT_THOUSANDS), 1_500_000.0)
        self.assertEqual(rubles_to_display(1_234_567.89, FINANCE_UNIT_THOUSANDS), 1234.57)

    def test_convert_month_map(self):
        src = {str(m): 1000.0 for m in range(1, 13)}
        th = convert_month_map_units(src, FINANCE_UNIT_RUBLES, FINANCE_UNIT_THOUSANDS)
        self.assertEqual(th["1"], 1.0)
        back = convert_month_map_units(th, FINANCE_UNIT_THOUSANDS, FINANCE_UNIT_RUBLES)
        self.assertEqual(back["1"], 1000.0)

    def test_scale_kind_payload(self):
        payload = {
            "org_amount": {str(m): 2000.0 for m in range(1, 13)},
            "buildings": [
                {
                    "building_id": 1,
                    "amount": {str(m): 1000.0 for m in range(1, 13)},
                }
            ],
        }
        ui = scale_kind_payload_amounts(payload, FINANCE_UNIT_THOUSANDS, to_display=True)
        self.assertEqual(ui["org_amount"]["1"], 2.0)
        self.assertEqual(ui["buildings"][0]["amount"]["1"], 1.0)
        db = scale_kind_payload_amounts(ui, FINANCE_UNIT_THOUSANDS, to_display=False)
        self.assertEqual(db["org_amount"]["1"], 2000.0)

    def test_scale_rows_money_skips_pct(self):
        rows = [{"План": 1000, "Факт": 500, "%": 50.0, "Остаток": 500}]
        out = scale_rows_money(rows, FINANCE_UNIT_THOUSANDS)
        self.assertEqual(out[0]["План"], 1.0)
        self.assertEqual(out[0]["Факт"], 0.5)
        self.assertEqual(out[0]["%"], 50.0)

    def test_default_from_settings(self):
        MainSettings.objects.all().delete()
        MainSettings.objects.create(finance_plan_unit=FINANCE_UNIT_THOUSANDS)
        self.assertEqual(get_default_finance_unit(), FINANCE_UNIT_THOUSANDS)
