"""Тесты ввода планов по корпусам: plan_kind, save volume+finance."""
from __future__ import annotations

from django.test import TestCase

from apps.organization.models import Building, MedicalOrganization
from apps.plan.models import (
    AnnualPlan,
    BuildingPlan,
    GroupIndicators,
    MonthlyBuildingPlan,
)


class PlanKindModelTests(TestCase):
    def setUp(self):
        self.group = GroupIndicators.objects.create(name="Тест индикатор", level=1)

    def test_two_kinds_same_group_year(self):
        ap_int = AnnualPlan.objects.create(
            group=self.group, year=2026, plan_kind=AnnualPlan.PlanKind.INTERNAL
        )
        ap_tfoms = AnnualPlan.objects.create(
            group=self.group, year=2026, plan_kind=AnnualPlan.PlanKind.TFOMS
        )
        self.assertNotEqual(ap_int.pk, ap_tfoms.pk)
        self.assertEqual(AnnualPlan.objects.filter(group=self.group, year=2026).count(), 2)

    def test_default_kind_internal(self):
        ap = AnnualPlan.objects.create(group=self.group, year=2025)
        self.assertEqual(ap.plan_kind, AnnualPlan.PlanKind.INTERNAL)
        self.assertEqual(ap.monthly_plans.count(), 12)


class IndicatorPlanFormServiceTests(TestCase):
    def setUp(self):
        self.org = MedicalOrganization.objects.create(
            name="МО",
            name_kvazar="МО",
            name_miskauz="МО",
            address="addr",
            phone_number="0",
            email="a@b.c",
            oid_mo="1.2.3",
        )
        self.group = GroupIndicators.objects.create(name="Неотложка", level=1)
        self.b1 = Building.objects.create(
            organization=self.org,
            name="Корпус 1",
            name_kvazar="К1",
            name_miskauz="К1",
        )
        self.b2 = Building.objects.create(
            organization=self.org,
            name="Корпус 2",
            name_kvazar="К2",
            name_miskauz="К2",
        )
        self.year = 2026

    def _save(self, *, plan_kind="internal", org_q=None, org_a=None, buildings=None, raise_org=False):
        from apps.analytical_app.pages.economist.building_indicators.query import (
            save_indicator_plan_form,
        )

        org_q = org_q or {str(m): 100 for m in range(1, 13)}
        org_a = org_a or {str(m): 1000.0 for m in range(1, 13)}
        return save_indicator_plan_form(
            year=self.year,
            group_id=self.group.id,
            plan_kind=plan_kind,
            org_quantity=org_q,
            org_amount=org_a,
            buildings=buildings or [],
            raise_org_from_buildings=raise_org,
        )

    def test_save_volume_and_finance(self):
        buildings = [
            {
                "building_id": self.b1.id,
                "building_name": self.b1.name,
                "quantity": {str(m): 40 for m in range(1, 13)},
                "amount": {str(m): 400.0 for m in range(1, 13)},
            }
        ]
        result = self._save(buildings=buildings)
        self.assertTrue(result["ok"])
        ap = AnnualPlan.objects.get(
            group=self.group, year=self.year, plan_kind=AnnualPlan.PlanKind.INTERNAL
        )
        mp = ap.monthly_plans.get(month=1)
        self.assertEqual(mp.quantity, 100)
        self.assertEqual(float(mp.amount), 1000.0)
        bp = BuildingPlan.objects.get(annual_plan=ap, building=self.b1)
        mbp = bp.monthly_building_plans.get(month=1)
        self.assertEqual(mbp.quantity, 40)
        self.assertEqual(float(mbp.amount), 400.0)

    def test_kinds_independent(self):
        self._save(plan_kind="internal", org_q={str(m): 10 for m in range(1, 13)})
        self._save(plan_kind="tfoms", org_q={str(m): 99 for m in range(1, 13)})
        ap_i = AnnualPlan.objects.get(group=self.group, year=self.year, plan_kind="internal")
        ap_t = AnnualPlan.objects.get(group=self.group, year=self.year, plan_kind="tfoms")
        self.assertEqual(ap_i.monthly_plans.get(month=1).quantity, 10)
        self.assertEqual(ap_t.monthly_plans.get(month=1).quantity, 99)

    def test_building_sum_constraint(self):
        buildings = [
            {
                "building_id": self.b1.id,
                "quantity": {str(m): 60 for m in range(1, 13)},
                "amount": {str(m): 0 for m in range(1, 13)},
            },
            {
                "building_id": self.b2.id,
                "quantity": {str(m): 50 for m in range(1, 13)},
                "amount": {str(m): 0 for m in range(1, 13)},
            },
        ]
        result = self._save(
            org_q={str(m): 100 for m in range(1, 13)},
            buildings=buildings,
            raise_org=False,
        )
        self.assertFalse(result["ok"])
        self.assertTrue(result["errors"])

    def test_raise_org_from_buildings(self):
        buildings = [
            {
                "building_id": self.b1.id,
                "quantity": {str(m): 120 for m in range(1, 13)},
                "amount": {str(m): 0 for m in range(1, 13)},
            }
        ]
        result = self._save(
            org_q={str(m): 50 for m in range(1, 13)},
            buildings=buildings,
            raise_org=True,
        )
        self.assertTrue(result["ok"])
        ap = AnnualPlan.objects.get(group=self.group, year=self.year, plan_kind="internal")
        self.assertEqual(ap.monthly_plans.get(month=1).quantity, 120)

    def test_add_building_creates_twelve_months(self):
        from apps.analytical_app.pages.economist.building_indicators.query import (
            add_building_to_plan,
        )

        payload = add_building_to_plan(self.year, self.group.id, self.b1.id, "internal")
        self.assertEqual(len(payload["buildings"]), 1)
        ap = AnnualPlan.objects.get(group=self.group, year=self.year, plan_kind="internal")
        bp = BuildingPlan.objects.get(annual_plan=ap, building=self.b1)
        self.assertEqual(MonthlyBuildingPlan.objects.filter(building_plan=bp).count(), 12)

    def test_load_form_after_save(self):
        from apps.analytical_app.pages.economist.building_indicators.query import (
            load_indicator_plan_form,
        )

        buildings = [
            {
                "building_id": self.b1.id,
                "quantity": {str(m): 5 for m in range(1, 13)},
                "amount": {str(m): 50.5 for m in range(1, 13)},
            }
        ]
        self._save(buildings=buildings)
        form = load_indicator_plan_form(self.year, self.group.id, "internal")
        self.assertEqual(form["org_quantity"]["1"], 100)
        self.assertEqual(form["buildings"][0]["quantity"]["1"], 5)
        self.assertEqual(form["buildings"][0]["amount"]["1"], 50.5)
