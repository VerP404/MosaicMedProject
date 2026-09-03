"""Тесты пакета талонов ДН (2 Excel) и разбора файла."""

from __future__ import annotations

import io
import zipfile
from datetime import date

import pandas as pd
from django.test import TestCase

from apps.dn_matrix.models import (
    DnDiagnosis,
    DnDiagnosisCategory,
    DnDiagnosisGroup,
    DnDiagnosisGroupMembership,
    DnDiagnosisSpecialty,
    DnService,
    DnServicePrice,
    DnServicePricePeriod,
    DnServiceRequirement,
    DnSpecialty,
    DnUnavailableService,
    MatrixEdition,
)
from apps.dn_matrix.services.rf_workdays import is_rf_workday, pick_visit_dates
from apps.dn_matrix.services.talon_bundle import (
    TalonBundleItem,
    TalonBundleParams,
    _build_service_rows,
    _is_oncology_row,
    build_talon_bundle,
    codes_from_birth_year,
    render_talon_bundle_zip,
)
from apps.dn_matrix.services.talon_bundle_input import (
    enrich_file_rows_with_not_passed,
    items_from_not_passed_rows,
    parse_input_dataframe,
    read_upload_dataframe,
)


class _FixedRng:
    def randint(self, _a: int, _b: int) -> int:
        return _a


class RfWorkdaysTests(TestCase):
    def test_weekend_not_workday_april_2026(self):
        self.assertFalse(is_rf_workday(date(2026, 4, 4)))
        self.assertFalse(is_rf_workday(date(2026, 4, 5)))

    def test_pick_visit_dates_step1_consecutive(self):
        dates = pick_visit_dates(
            date(2026, 4, 1),
            date(2026, 4, 30),
            visits=3,
            step_workdays=1,
            rng=_FixedRng(),
        )
        self.assertEqual(dates, ["01-04-26", "02-04-26", "03-04-26"])

    def test_pick_visit_dates_step2_skips_workday(self):
        dates = pick_visit_dates(
            date(2026, 4, 1),
            date(2026, 4, 30),
            visits=3,
            step_workdays=2,
            rng=_FixedRng(),
        )
        self.assertEqual(dates, ["01-04-26", "03-04-26", "07-04-26"])

    def test_may_holiday_skipped(self):
        dates = pick_visit_dates(
            date(2026, 4, 28),
            date(2026, 5, 15),
            visits=3,
            step_workdays=1,
            rng=_FixedRng(),
        )
        joined = ",".join(dates)
        self.assertNotIn("01-05-26", joined)
        self.assertNotIn("09-05-26", joined)

    def test_anchor_plus_five_workdays_from_friday(self):
        from apps.dn_matrix.services.rf_workdays import add_rf_workdays, pick_visit_dates_from_anchor

        self.assertEqual(add_rf_workdays(date(2026, 4, 3), 5), date(2026, 4, 10))
        dates = pick_visit_dates_from_anchor(
            date(2026, 4, 3),
            visits=3,
            step_workdays=1,
            offset_workdays=5,
        )
        self.assertEqual(dates, ["10-04-26", "13-04-26", "14-04-26"])

    def test_anchor_skips_journal_blocked_dates(self):
        from apps.dn_matrix.services.rf_workdays import pick_visit_dates_from_anchor

        dates = pick_visit_dates_from_anchor(
            date(2026, 4, 3),
            visits=3,
            step_workdays=1,
            offset_workdays=5,
            blocked={date(2026, 4, 10), date(2026, 4, 13)},
        )
        self.assertEqual(dates[0], "14-04-26")
        self.assertNotIn("10-04-26", dates)
        self.assertNotIn("13-04-26", dates)

    def test_second_anchor_skips_already_picked_dates(self):
        from datetime import datetime

        from apps.dn_matrix.services.rf_workdays import pick_visit_dates_from_anchor

        first = pick_visit_dates_from_anchor(
            date(2026, 4, 3),
            visits=3,
            step_workdays=1,
            offset_workdays=5,
        )
        blocked = {datetime.strptime(d, "%d-%m-%y").date() for d in first}
        second = pick_visit_dates_from_anchor(
            date(2026, 4, 3),
            visits=3,
            step_workdays=1,
            offset_workdays=5,
            blocked=blocked,
        )
        self.assertFalse(set(first) & set(second))
        self.assertEqual(second[0], "15-04-26")


class JournalVisitSqlTests(TestCase):
    def test_like_wildcards_escaped_for_pandas(self):
        from apps.analytical_app.pages.head.dn.query import sql_journal_visits_in_period

        sql = sql_journal_visits_in_period(date(2026, 4, 1), date(2026, 4, 30), None)
        self.assertIn("%%не явил%%", sql)
        self.assertIn("____-__-__%%", sql)


class TalonBundleExportTests(TestCase):
    def setUp(self):
        self.edition = MatrixEdition.objects.create(
            code="dn_bundle_test",
            title="After 04.2026",
            effective_from=date(2026, 4, 1),
            status=MatrixEdition.Status.ACTIVE,
            max_doctor_visits=3,
        )
        self.cat = DnDiagnosisCategory.objects.create(
            edition=self.edition,
            code="ct_4",
            title="БСК",
            sort_order=0,
        )
        self.onko_cat = DnDiagnosisCategory.objects.create(
            edition=self.edition,
            code="ct_2",
            title="ОНКО",
            sort_order=1,
        )
        self.diag = DnDiagnosis.objects.create(
            edition=self.edition,
            category=self.cat,
            mkb_code="I10",
            title="Гипертония",
        )
        self.onko_diag = DnDiagnosis.objects.create(
            edition=self.edition,
            category=self.onko_cat,
            mkb_code="C50",
            title="Рак молочной железы",
        )
        self.spec_ther = DnSpecialty.objects.create(
            edition=self.edition,
            code="ther",
            title="Терапевт",
            sort_order=0,
        )
        self.spec_onko = DnSpecialty.objects.create(
            edition=self.edition,
            code="onko",
            title="Онколог",
            sort_order=1,
        )
        DnDiagnosisSpecialty.objects.create(diagnosis=self.diag, specialty=self.spec_ther, kind="primary")
        DnDiagnosisSpecialty.objects.create(diagnosis=self.onko_diag, specialty=self.spec_onko, kind="primary")

        for code, title in (
            ("SRV1", "Анализ крови"),
            ("SRV2", "Диспансерный прием терапевта"),
        ):
            group = DnDiagnosisGroup.objects.create(
                edition=self.edition,
                code=f"g_{code}",
                title=title,
                rule={"mkb_codes": ["I10", "C50"]},
                sort_order=0,
            )
            DnDiagnosisGroupMembership.objects.create(group=group, diagnosis=self.diag)
            DnDiagnosisGroupMembership.objects.create(group=group, diagnosis=self.onko_diag)
            svc = DnService.objects.create(edition=self.edition, code=code, title=title, sort_order=0)
            DnServiceRequirement.objects.create(
                service=svc,
                specialty=self.spec_ther,
                diagnosis_group=group,
            )
            DnServiceRequirement.objects.create(
                service=svc,
                specialty=self.spec_onko,
                diagnosis_group=group,
            )

        self.period = DnServicePricePeriod.objects.create(
            edition=self.edition,
            code="p1",
            title="2026",
            valid_from=date(2026, 4, 1),
            valid_to=None,
        )
        for svc in DnService.objects.filter(edition=self.edition):
            DnServicePrice.objects.create(period=self.period, service=svc, amount="100.00", currency="RUB")

    def test_oncology_by_title_not_bsk_code(self):
        self.assertTrue(_is_oncology_row(specialty="Онколог", category_code=None, category_title=None))
        self.assertTrue(_is_oncology_row(specialty="Терапевт", category_code="ct_2", category_title="ОНКО"))
        self.assertFalse(_is_oncology_row(specialty="Терапевт", category_code="ct_4", category_title="БСК"))

    def test_header_ds2_category_and_visits(self):
        params = TalonBundleParams(
            date_from=date(2026, 4, 1),
            date_to=date(2026, 4, 30),
            visit_step=1,
            visits=3,
            edition=self.edition,
            header_defaults={"врач": "12345", "Корпус": "К1"},
            seed=1,
        )
        items = [
            TalonBundleItem(
                enp="1234567890123456",
                ds1="I10",
                ds2_list=["E11", "J06"],
                specialty="Терапия",
            )
        ]
        result = build_talon_bundle(items=items, params=params)
        self.assertEqual(result["talons_count"], 1)
        row = result["headers"][0]
        self.assertEqual(row["цель"], "3")
        self.assertEqual(row["Диагноз"], "I10")
        self.assertEqual(row["Диагноз 2"], "E11, J06")
        self.assertEqual(row["Категория"], "БСК")
        self.assertEqual(row["врач"], "12345")
        self.assertEqual(row["Корпус"], "К1")
        self.assertEqual(row["посещений в МО"], "3")
        self.assertNotIn("Цель консил", row)

        svc_by_code = {r["Код услуги"]: r for r in result["services"]}
        self.assertEqual(svc_by_code["SRV2"]["Кол-во"], "3")
        self.assertEqual(svc_by_code["SRV2"]["Дата окончания"], result["headers"][0]["окончание"])
        self.assertEqual(svc_by_code["SRV1"]["Кол-во"], "1")
        self.assertEqual(svc_by_code["SRV1"]["Дата окончания"], svc_by_code["SRV1"]["Дата начала"])

    def test_social_status_from_birth_year(self):
        today = date(2026, 8, 31)
        self.assertEqual(codes_from_birth_year(date(1965, 5, 1), today=today), ("22", "3"))
        self.assertEqual(codes_from_birth_year(date(1966, 1, 1), today=today), ("11", "1"))
        self.assertEqual(codes_from_birth_year(date(1980, 12, 31), today=today), ("11", "1"))
        self.assertEqual(codes_from_birth_year(None, today=today), ("", ""))

    def test_header_social_status_over_60(self):
        params = TalonBundleParams(
            date_from=date(2026, 4, 1),
            date_to=date(2026, 4, 30),
            visits=1,
            edition=self.edition,
            header_defaults={"врач": "1", "Корпус": "K"},
            seed=1,
        )
        items = [
            TalonBundleItem(
                enp="1234567890123456",
                ds1="I10",
                specialty="Терапия",
                birth_date=date(1950, 3, 10),
            )
        ]
        result = build_talon_bundle(items=items, params=params)
        row = result["headers"][0]
        self.assertEqual(row["Соцстатус"], "22")
        self.assertEqual(row["Вид занятости"], "3")

    def test_header_social_status_from_person_table(self):
        from apps.dn_app.models import Person

        Person.objects.create(enp="1234567890123456", fio="Тест", dr=date(1990, 1, 1))
        params = TalonBundleParams(
            date_from=date(2026, 4, 1),
            date_to=date(2026, 4, 30),
            visits=1,
            edition=self.edition,
            header_defaults={"врач": "1", "Корпус": "K"},
            seed=1,
        )
        result = build_talon_bundle(
            items=[TalonBundleItem(enp="1234567890123456", ds1="I10", specialty="Терапия")],
            params=params,
        )
        row = result["headers"][0]
        self.assertEqual(row["Соцстатус"], "11")
        self.assertEqual(row["Вид занятости"], "1")

    def test_visits_qty_two(self):
        params = TalonBundleParams(
            date_from=date(2026, 4, 1),
            date_to=date(2026, 4, 30),
            visits=2,
            edition=self.edition,
            header_defaults={"врач": "11111", "Корпус": "К"},
            seed=1,
        )
        items = [TalonBundleItem(enp="1234567890123456", ds1="I10", specialty="Терапия")]
        result = build_talon_bundle(items=items, params=params)
        self.assertEqual(result["headers"][0]["посещений в МО"], "2")
        recv = {r["Код услуги"]: r["Кол-во"] for r in result["services"]}
        self.assertEqual(recv["SRV2"], "2")
        self.assertEqual(recv["SRV1"], "1")

    def test_skips_unavailable_service(self):
        DnUnavailableService.objects.create(edition=self.edition, service_code="SRV1", mkb_code="")
        params = TalonBundleParams(
            date_from=date(2026, 4, 1),
            date_to=date(2026, 4, 30),
            visits=1,
            edition=self.edition,
            header_defaults={"врач": "1", "Корпус": "K"},
            seed=1,
        )
        items = [TalonBundleItem(enp="1234567890123456", ds1="I10", specialty="Терапия")]
        result = build_talon_bundle(items=items, params=params)
        codes = {r["Код услуги"] for r in result["services"]}
        self.assertIn("SRV2", codes)
        self.assertNotIn("SRV1", codes)

    def test_service_row_shape(self):
        rows = _build_service_rows(
            plan_id=1,
            services=[
                {"code": "SRV1", "title": "Анализ крови"},
                {"code": "SRV2", "title": "Диспансерный прием терапевта"},
                {"code": "SKIP", "title": "Анализ", "unavailable": True},
            ],
            visit_dates=["01-04-26", "02-04-26", "03-04-26"],
            doctor_id="11111",
            visits=3,
        )
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["Код услуги"], "SRV2")
        self.assertEqual(rows[0]["Кол-во"], "3")
        self.assertEqual(rows[1]["Код услуги"], "SRV1")
        self.assertEqual(rows[1]["Кол-во"], "1")

    def test_zip_has_two_xlsx(self):
        params = TalonBundleParams(
            date_from=date(2026, 4, 1),
            date_to=date(2026, 4, 30),
            edition=self.edition,
            header_defaults={"врач": "1", "Корпус": "K"},
            seed=1,
        )
        items = [TalonBundleItem(enp="1234567890123456", ds1="I10", specialty="Терапия")]
        result = build_talon_bundle(items=items, params=params)
        blob, stamp = render_talon_bundle_zip(headers=result["headers"], services=result["services"], stamp="2026-04-01")
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            names = set(zf.namelist())
        self.assertIn(f"талоны_{stamp}.xlsx", names)
        self.assertIn(f"услуги_{stamp}.xlsx", names)

    def test_empty_profile_picks_therapy_when_several_specialties(self):
        cardio = DnSpecialty.objects.create(edition=self.edition, code="card", title="Кардиолог", sort_order=2)
        DnDiagnosisSpecialty.objects.create(diagnosis=self.diag, specialty=cardio, kind="joint")
        from apps.dn_matrix.services.batch_pick import resolve_specialty_id
        from apps.dn_matrix.services.matrix import build_matrix_pick_cache

        cache = build_matrix_pick_cache(self.edition)
        specialties = list(self.edition.specialties.all())
        sid = resolve_specialty_id(cache, specialties, profile="", mkb_code="I10")
        self.assertEqual(sid, self.spec_ther.id)

        params = TalonBundleParams(
            date_from=date(2026, 4, 1),
            date_to=date(2026, 4, 30),
            visits=1,
            edition=self.edition,
            header_defaults={"врач": "1", "Корпус": "K"},
            seed=1,
        )
        result = build_talon_bundle(
            items=[TalonBundleItem(enp="1234567890123456", ds1="I10")],
            params=params,
        )
        self.assertEqual(result["talons_count"], 1, result["warnings"])

    def test_empty_profile_picks_endocrinology_for_diabetes(self):
        sd_cat = DnDiagnosisCategory.objects.create(edition=self.edition, code="ct_3", title="СД", sort_order=2)
        d_e11 = DnDiagnosis.objects.create(edition=self.edition, category=sd_cat, mkb_code="E11.7", title="СД2")
        spec_end = DnSpecialty.objects.create(edition=self.edition, code="end", title="Эндокринолог", sort_order=3)
        DnDiagnosisSpecialty.objects.create(diagnosis=d_e11, specialty=spec_end, kind="primary")
        DnDiagnosisSpecialty.objects.create(diagnosis=d_e11, specialty=self.spec_ther, kind="joint")
        from apps.dn_matrix.services.batch_pick import resolve_specialty_id
        from apps.dn_matrix.services.matrix import build_matrix_pick_cache

        cache = build_matrix_pick_cache(self.edition)
        specialties = list(self.edition.specialties.all())
        sid = resolve_specialty_id(cache, specialties, profile="", mkb_code="E11.7")
        self.assertEqual(sid, spec_end.id)


class TalonBundleInputTests(TestCase):
    def test_parse_file_aliases_and_excel_doctor(self):
        df = pd.DataFrame(
            [
                {
                    "ЕНП": "1234567890123456",
                    "Код врача": 12345.0,
                    "Корпус": "К1",
                    "Дата начала": "01.04.2026",
                    "Дата окончания": "30.04.2026",
                }
            ]
        )
        rows, warnings = parse_input_dataframe(df)
        self.assertFalse(warnings)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["enp"], "1234567890123456")
        self.assertEqual(rows[0]["doctor"], "12345")
        self.assertEqual(rows[0]["corpus"], "К1")
        self.assertEqual(rows[0]["date_from"], date(2026, 4, 1))
        self.assertEqual(rows[0]["date_to"], date(2026, 4, 30))

    def test_join_not_passed_fills_diagnoses(self):
        file_rows = [
            {
                "enp": "1234567890123456",
                "doctor": "99999",
                "corpus": "К2",
                "date_from": date(2026, 4, 1),
                "date_to": date(2026, 4, 30),
                "ds1": "",
                "ds2": [],
                "profile": "",
                "category": "",
            }
        ]
        not_passed = [
            {
                "ЕНП": "1234567890123456",
                "Основной МКБ": "I10",
                "Сопутствующие МКБ": "E11, I20",
                "Профиль": "Терапия",
                "Группа основного": "БСК",
            }
        ]
        items, warnings = enrich_file_rows_with_not_passed(file_rows, not_passed, grouped=True)
        self.assertEqual(len(items), 1, warnings)
        self.assertEqual(items[0].ds1, "I10")
        self.assertEqual(items[0].ds2_list, ["E11", "I20"])
        self.assertEqual(items[0].specialty, "Терапия")
        self.assertEqual(items[0].doctor_id, "99999")
        self.assertEqual(items[0].category_168n, "БСК")

    def test_not_passed_selection_items(self):
        rows = [
            {
                "ЕНП": "111",
                "Основной МКБ": "I10",
                "Сопутствующие МКБ": "E11",
                "Профиль": "Терапия",
            }
        ]
        items, warnings = items_from_not_passed_rows(
            rows,
            grouped=True,
            doctor="55555",
            corpus="К3",
            date_from=date(2026, 8, 1),
            date_to=date(2026, 8, 31),
        )
        self.assertEqual(len(items), 1, warnings)
        self.assertEqual(items[0].doctor_id, "55555")
        self.assertEqual(items[0].ds2_list, ["E11"])
        self.assertEqual(items[0].date_from, date(2026, 8, 1))

    def test_parse_goal3_example_xlsx(self):
        from pathlib import Path

        path = Path(__file__).resolve().parents[2] / "analytical_app" / "pages" / "head" / "dn" / "3 цель дн.xlsx"
        if not path.is_file():
            self.skipTest("пример файла не лежит рядом с вкладкой ДН")
        df = read_upload_dataframe(path.read_bytes(), path.name)
        rows, warnings = parse_input_dataframe(df)
        self.assertGreaterEqual(len(rows), 1000, warnings)
        sample = rows[0]
        self.assertEqual(sample["enp"], "2856320873000197")
        self.assertEqual(sample["doctor"], "30097144")
        self.assertEqual(sample["ds1"], "I11.9")
        self.assertEqual(sample["date_from"], date(2026, 7, 6))
        self.assertEqual(sample["date_to"], date(2026, 7, 10))
        with_ds2 = next(r for r in rows if r.get("ds2"))
        self.assertEqual(with_ds2["ds1"], "E11.7")
        self.assertIn("I11.9", with_ds2["ds2"])


class ClinicVisitorItemsTests(TestCase):
    def test_skips_existing_goal3_same_group(self):
        from apps.dn_matrix.services.journal_visitors import items_from_clinic_visitors

        visits = [
            {
                "enp_norm": "111",
                "visit_date": date(2026, 4, 3),
                "fio": "Иванов",
                "department": "Терапия",
                "employee_last_name": "Петров",
                "employee_first_name": "Иван",
                "journal_number": "42",
            }
        ]
        not_passed = [
            {
                "ЕНП": "111",
                "Основной МКБ": "I10",
                "Сопутствующие МКБ": "",
                "Профиль": "Терапия",
                "Группа основного": "БСК",
            }
        ]
        items, preview, _ = items_from_clinic_visitors(
            visits,
            not_passed,
            blocked_by_enp={"111": {date(2026, 4, 3)}},
            existing_goal3={"111": [{"mkb": "I11.9", "category_168n": "БСК"}]},
            doctor_codes={},
        )
        self.assertEqual(items, [])
        self.assertEqual(preview[0]["Статус"], "уже есть цель 3 по группе")

    def test_builds_item_with_journal_anchor(self):
        from apps.dn_matrix.services.journal_visitors import items_from_clinic_visitors

        visits = [
            {
                "enp_norm": "222",
                "visit_date": date(2026, 4, 3),
                "fio": "Сидоров",
                "department": "Терапия",
                "employee_last_name": "Петров",
                "employee_first_name": "Иван",
                "journal_number": "7",
            }
        ]
        not_passed = [
            {
                "ЕНП": "222",
                "Основной МКБ": "E11",
                "Сопутствующие МКБ": "I10",
                "Профиль": "Эндокринология",
                "Группа основного": "СД",
                "Дата рождения": date(1950, 1, 1),
            }
        ]
        items, preview, _ = items_from_clinic_visitors(
            visits,
            not_passed,
            blocked_by_enp={"222": {date(2026, 4, 3)}},
            existing_goal3={"222": [{"mkb": "I10", "category_168n": "БСК"}]},
            doctor_codes={("петров", "иван"): "30097144"},
            default_corpus="К1",
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].ds1, "E11")
        self.assertEqual(items[0].journal_visit_date, date(2026, 4, 3))
        self.assertEqual(items[0].doctor_id, "30097144")
        self.assertEqual(items[0].corpus, "К1")
        self.assertEqual(preview[0]["Статус"], "в пакет")
        self.assertEqual(preview[0]["Номер"], "7")

