from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase, TestCase

from apps.health_schools.models import HealthSchool
from apps.health_schools.services.analysis import classify_talons, due_list
from apps.health_schools.services.catalog import spec_from_model
from apps.health_schools.services.matching import (
    SchoolSpec,
    code_matches_rule,
    match_schools,
    parse_diagnosis_codes,
    primary_school,
)
import pandas as pd


def _spec(**kwargs) -> SchoolSpec:
    base = dict(
        number=1,
        name="АГ",
        group_name="ДН",
        mkb_rule="I10-I15",
        visits=5,
        duration="60",
        tariff="1",
        service_code="B04.015.001",
        service_title="АГ",
        period_years=3,
        criterion="mkb",
        min_age=None,
        max_age=None,
    )
    base.update(kwargs)
    return SchoolSpec(**base)


CATALOG = [
    _spec(number=1, name="АГ", mkb_rule="I10-I15", visits=5, service_code="B04.015.001"),
    _spec(number=2, name="ИБС", mkb_rule="I20-I25", visits=4, service_code=""),
    _spec(number=8, name="ФП", mkb_rule="I48.0-I48.9", visits=4, service_code=""),
    _spec(number=11, name="Ожирение", mkb_rule="ИМТ", visits=4, criterion="bmi", service_code="B05.069.008"),
    _spec(number=13, name="СД 2 взрослые", mkb_rule="E11.2-E11.9", visits=5, min_age=18, service_code="B04.012.001"),
    _spec(number=14, name="СД дети", mkb_rule="E11.2-E11.9", visits=10, max_age=17, service_code="B04.012.001"),
]


class MatchingTests(SimpleTestCase):
    def test_range_includes_decimals(self):
        self.assertTrue(code_matches_rule("I25.1", "I20-I25"))
        self.assertTrue(code_matches_rule("I11.9", "I10-I15"))
        self.assertFalse(code_matches_rule("I67.8", "I20-I25"))

    def test_af_parent_and_codes(self):
        self.assertTrue(code_matches_rule("I48", "I48.0-I48.9"))
        self.assertTrue(code_matches_rule("I48.2", "I48.0-I48.9"))
        self.assertFalse(code_matches_rule("I49.9", "I48.0-I48.9"))

    def test_parse_codes(self):
        self.assertEqual(parse_diagnosis_codes("I20.8", "I11.9, I25.2"), ["I20.8", "I11.9", "I25.2"])

    def test_primary_ihd(self):
        primary, hits = primary_school("I25.1", ["I11.9"], CATALOG)
        self.assertEqual(primary.name, "ИБС")
        self.assertEqual([h.name for h in hits], ["АГ", "ИБС"])

    def test_diabetes_by_age(self):
        child = match_schools(["E11.7"], CATALOG, age=12)
        adult = match_schools(["E11.7"], CATALOG, age=50)
        unknown = match_schools(["E11.7"], CATALOG, age=None)
        self.assertEqual([s.name for s in child], ["СД дети"])
        self.assertEqual([s.name for s in adult], ["СД 2 взрослые"])
        self.assertEqual([s.name for s in unknown], ["СД 2 взрослые"])

    def test_bmi_e66(self):
        hits = match_schools(["E66.0"], CATALOG)
        self.assertEqual(hits[0].name, "Ожирение")


class PeriodicityTests(SimpleTestCase):
    def test_too_soon_within_three_years(self):
        oms = pd.DataFrame(
            [
                {
                    "talon": "old",
                    "enp": "123",
                    "patient": "A",
                    "birth_date": "1950-01-01",
                    "treatment_start": "2023-08-01",
                    "treatment_end": "2023-08-05",
                    "main_diagnosis_code": "I11.9",
                    "additional_diagnosis_codes": "",
                    "status": "3",
                    "building": "ГП",
                    "doctor": "X",
                    "specialty": "",
                    "mo_visits": 5,
                    "report_year": 2023,
                },
                {
                    "talon": "new",
                    "enp": "123",
                    "patient": "A",
                    "birth_date": "1950-01-01",
                    "treatment_start": "2026-08-01",
                    "treatment_end": "2026-08-05",
                    "main_diagnosis_code": "I11.9",
                    "additional_diagnosis_codes": "",
                    "status": "1",
                    "building": "ГП",
                    "doctor": "X",
                    "specialty": "",
                    "mo_visits": 5,
                    "report_year": 2026,
                },
            ]
        )
        talons, too_soon = classify_talons(oms, CATALOG, 2026)
        self.assertEqual(len(talons), 1)
        self.assertEqual(talons.iloc[0]["периодичность_ок"], "нет")
        self.assertEqual(len(too_soon), 1)

    def test_due_after_period(self):
        oms = pd.DataFrame(
            [
                {
                    "talon": "old",
                    "enp": "999",
                    "patient": "B",
                    "birth_date": "1960-01-01",
                    "treatment_start": "2022-01-01",
                    "treatment_end": "2022-01-10",
                    "main_diagnosis_code": "I11.9",
                    "additional_diagnosis_codes": "",
                    "status": "3",
                    "building": "",
                    "doctor": "",
                    "specialty": "",
                    "mo_visits": 5,
                    "report_year": 2022,
                }
            ]
        )
        iszl = pd.DataFrame(
            [
                {
                    "ЕНП": "999",
                    "ФИО": "B",
                    "Дата рождения": "1960-01-01",
                    "МКБ_ИСЗЛ": "I11.9",
                    "школа": "АГ",
                    "№_школы": 1,
                    "код_услуги": "B04.015.001",
                    "явки": 5,
                    "период_лет": 3,
                    "участок": "1",
                }
            ]
        )
        due = due_list(iszl, oms, CATALOG, as_of=date(2026, 9, 1))
        self.assertEqual(len(due), 1)


class ImportModelTests(TestCase):
    def test_spec_from_model(self):
        row = HealthSchool.objects.create(
            number=1,
            name="АГ",
            mkb_rule="I10-I15",
            visits=5,
            service_code="B04.015.001",
            period_years=3,
        )
        spec = spec_from_model(row)
        self.assertEqual(spec.number, 1)
        self.assertEqual(spec.period_years, 3)
        self.assertEqual(row.tariff, Decimal("0"))
