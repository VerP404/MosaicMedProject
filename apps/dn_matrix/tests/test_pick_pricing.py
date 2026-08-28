from decimal import Decimal

from django.test import TestCase

from apps.dn_matrix.services.pick_pricing import (
    is_per_visit_service,
    parse_price_amount,
    service_line_qty,
    sum_services_amount,
)


class PickPricingTests(TestCase):
    def test_is_per_visit(self):
        self.assertTrue(is_per_visit_service("Диспансерный прием терапевта"))
        self.assertFalse(is_per_visit_service("Анализ крови"))

    def test_service_line_qty(self):
        self.assertEqual(service_line_qty("Диспансерный прием", 3), 3)
        self.assertEqual(service_line_qty("Анализ", 3), 1)
        self.assertEqual(service_line_qty("Диспансерный прием", 0), 1)
        self.assertEqual(service_line_qty("Диспансерный прием", 3, max_visits=1), 1)

    def test_sum_services_amount(self):
        services = [
            {"title": "Диспансерный прием", "price": "100.00"},
            {"title": "Анализ", "price": "50"},
        ]
        total, missing = sum_services_amount(services, visits=2)
        self.assertFalse(missing)
        self.assertEqual(total, Decimal("250.00"))

    def test_sum_missing_price(self):
        services = [{"title": "X", "price": None}]
        total, missing = sum_services_amount(services, visits=1)
        self.assertTrue(missing)
        self.assertEqual(total, Decimal("0"))

    def test_parse_price_comma(self):
        self.assertEqual(parse_price_amount("1,5"), Decimal("1.5"))

    def test_sum_skips_unavailable(self):
        services = [
            {"title": "Анализ", "price": "50", "unavailable": True},
            {"title": "Анализ 2", "price": "20"},
        ]
        total, missing = sum_services_amount(services, visits=1)
        self.assertFalse(missing)
        self.assertEqual(total, Decimal("20"))
        total_all, _ = sum_services_amount(services, visits=1, skip_unavailable=False)
        self.assertEqual(total_all, Decimal("70"))
