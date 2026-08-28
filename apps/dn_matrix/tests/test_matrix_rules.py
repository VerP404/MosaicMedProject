from datetime import date
import unittest

from django.db import connection
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
    MatrixEdition,
)
from apps.dn_matrix.services.matrix import (
    build_matrix_pick_cache,
    expand_group_diagnosis_ids,
    groups_for_diagnosis,
    select_services_for_context,
    select_services_from_cache,
    service_applies,
)


class MatrixRuleExpansionTests(TestCase):
    def setUp(self):
        self.edition = MatrixEdition.objects.create(
            code="rule-ed",
            title="Rule test",
            effective_from=date(2026, 1, 1),
            status=MatrixEdition.Status.DRAFT,
        )
        self.cat = DnDiagnosisCategory.objects.create(edition=self.edition, code="c1", title="Cat")
        self.d_i10 = DnDiagnosis.objects.create(
            edition=self.edition, category=self.cat, mkb_code="I10", title="Гипертония"
        )
        self.d_i20 = DnDiagnosis.objects.create(
            edition=self.edition, category=self.cat, mkb_code="I20", title="Стенокардия"
        )
        self.d_a00 = DnDiagnosis.objects.create(
            edition=self.edition, category=self.cat, mkb_code="A00.0", title="Холера"
        )
        self.group = DnDiagnosisGroup.objects.create(
            edition=self.edition,
            code="g-prefix",
            title="I1*",
            rule={"mkb_prefixes": ["I1"]},
            sort_order=0,
        )
        DnDiagnosisGroupMembership.objects.create(group=self.group, diagnosis=self.d_a00)

    @unittest.skipUnless(connection.vendor == "postgresql", "prefix expansion verified on PostgreSQL")
    def test_expand_group_includes_prefix_and_membership(self):
        ids = expand_group_diagnosis_ids(self.group)
        self.assertIn(self.d_i10.id, ids)
        self.assertIn(self.d_i20.id, ids)
        self.assertIn(self.d_a00.id, ids)

    def test_expand_group_skips_noniterable_rule_fragments(self):
        g = DnDiagnosisGroup.objects.create(
            edition=self.edition,
            code="g-bad",
            title="bad rule",
            rule={"mkb_codes": 123, "mkb_prefixes": "oops", "category_codes": None},
            sort_order=1,
        )
        DnDiagnosisGroupMembership.objects.create(group=g, diagnosis=self.d_i10)
        ids = expand_group_diagnosis_ids(g)
        self.assertIn(self.d_i10.id, ids)

    def test_groups_for_diagnosis_merges_rule_and_membership(self):
        gids = groups_for_diagnosis(self.edition.id, self.d_i10.id)
        self.assertIn(self.group.id, gids)
        gids_a = groups_for_diagnosis(self.edition.id, self.d_a00.id)
        self.assertIn(self.group.id, gids_a)


class ServiceSelectionLogicTests(TestCase):
    def setUp(self):
        self.edition = MatrixEdition.objects.create(
            code="sel-ed",
            title="Sel",
            effective_from=date(2026, 1, 1),
            status=MatrixEdition.Status.DRAFT,
        )
        cat = DnDiagnosisCategory.objects.create(edition=self.edition, code="c", title="C")
        self.diagnosis = DnDiagnosis.objects.create(
            edition=self.edition, category=cat, mkb_code="E11", title="СД2"
        )
        self.spec = DnSpecialty.objects.create(edition=self.edition, code="end", title="Эндокринология")
        DnDiagnosisSpecialty.objects.create(
            diagnosis=self.diagnosis, specialty=self.spec, kind=DnDiagnosisSpecialty.Kind.PRIMARY
        )
        self.svc = DnService.objects.create(edition=self.edition, code="u1", title="Услуга 1", sort_order=0)
        DnServiceRequirement.objects.create(service=self.svc, diagnosis=self.diagnosis, specialty=self.spec)
        period = DnServicePricePeriod.objects.create(
            edition=self.edition,
            code="p1",
            title="",
            valid_from=date(2026, 1, 1),
            valid_to=None,
        )
        DnServicePrice.objects.create(period=period, service=self.svc, amount="100.00", currency="RUB")

    def test_service_applies_when_row_matches(self):
        gids = groups_for_diagnosis(self.edition.id, self.diagnosis.id)
        self.assertTrue(service_applies(self.svc.id, self.spec.id, {self.diagnosis.id}, gids))

    def test_select_returns_service_with_price(self):
        rows, period, did = select_services_for_context(
            self.edition,
            specialty_id=self.spec.id,
            mkb_code="E11",
            price_period_id=None,
            price_on=date(2026, 6, 1),
        )
        self.assertEqual(did, self.diagnosis.id)
        self.assertIsNotNone(period)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["code"], "U1")
        self.assertEqual(rows[0]["price"], "100.00")

    def test_cached_select_matches_db_select(self):
        cache = build_matrix_pick_cache(self.edition)
        cached_rows, cached_period, cached_did = select_services_from_cache(
            cache,
            specialty_id=self.spec.id,
            mkb_code="E11",
            price_on=date(2026, 6, 1),
        )
        db_rows, db_period, db_did = select_services_for_context(
            self.edition,
            specialty_id=self.spec.id,
            mkb_code="E11",
            price_on=date(2026, 6, 1),
        )
        self.assertEqual(cached_did, db_did)
        self.assertEqual(cached_period and cached_period.id, db_period and db_period.id)
        self.assertEqual([r["code"] for r in cached_rows], [r["code"] for r in db_rows])


class UnavailableServicePickTests(TestCase):
    def setUp(self):
        from apps.dn_matrix.models import DnUnavailableService
        from apps.dn_matrix.services.workspace import pick_services

        self.DnUnavailableService = DnUnavailableService
        self.pick_services = pick_services
        self.edition = MatrixEdition.objects.create(
            code="unavail-ed",
            title="Unavail",
            effective_from=date(2026, 1, 1),
            status=MatrixEdition.Status.DRAFT,
        )
        cat = DnDiagnosisCategory.objects.create(edition=self.edition, code="c", title="C")
        self.d_e11 = DnDiagnosis.objects.create(
            edition=self.edition, category=cat, mkb_code="E11", title="СД2"
        )
        self.d_i10 = DnDiagnosis.objects.create(
            edition=self.edition, category=cat, mkb_code="I10", title="ГБ"
        )
        self.spec = DnSpecialty.objects.create(edition=self.edition, code="end", title="Эндокринология")
        for diag in (self.d_e11, self.d_i10):
            DnDiagnosisSpecialty.objects.create(
                diagnosis=diag, specialty=self.spec, kind=DnDiagnosisSpecialty.Kind.PRIMARY
            )
        self.svc_lab = DnService.objects.create(edition=self.edition, code="A09.05.001", title="Глюкоза", sort_order=0)
        self.svc_visit = DnService.objects.create(
            edition=self.edition, code="B04.047.001", title="Диспансерный прием эндокринолога", sort_order=1
        )
        for svc in (self.svc_lab, self.svc_visit):
            DnServiceRequirement.objects.create(service=svc, diagnosis=self.d_e11, specialty=self.spec)
            DnServiceRequirement.objects.create(service=svc, diagnosis=self.d_i10, specialty=self.spec)
        period = DnServicePricePeriod.objects.create(
            edition=self.edition, code="p1", title="", valid_from=date(2026, 1, 1), valid_to=None
        )
        DnServicePrice.objects.create(period=period, service=self.svc_lab, amount="50.00", currency="RUB")
        DnServicePrice.objects.create(period=period, service=self.svc_visit, amount="100.00", currency="RUB")

    def test_global_unavailable_is_marked_but_kept(self):
        self.DnUnavailableService.objects.create(
            edition=self.edition, service_code="A09.05.001", mkb_code=""
        )
        rows, _, _ = select_services_for_context(
            self.edition, specialty_id=self.spec.id, mkb_code="E11", price_on=date(2026, 6, 1)
        )
        by_code = {r["code"]: r for r in rows}
        self.assertTrue(by_code["A09.05.001"]["unavailable"])
        self.assertFalse(by_code["B04.047.001"]["unavailable"])

        picked = self.pick_services(self.edition, specialty_id=self.spec.id, mkb="E11", visits=1)
        self.assertEqual(picked["count"], 1)
        self.assertEqual(picked["excluded_count"], 1)
        self.assertEqual(picked["total"], "100.00")
        self.assertEqual(picked["excluded_total"], "50.00")
        statuses = {r["Код"]: r["Проводится"] for r in picked["rows"]}
        self.assertEqual(statuses["A09.05.001"], "не проводится")
        self.assertEqual(statuses["B04.047.001"], "да")

    def test_mkb_specific_unavailable_does_not_apply_to_other_diagnosis(self):
        self.DnUnavailableService.objects.create(
            edition=self.edition, service_code="A09.05.001", mkb_code="E11"
        )
        rows_e11, _, _ = select_services_for_context(
            self.edition, specialty_id=self.spec.id, mkb_code="E11", price_on=date(2026, 6, 1)
        )
        rows_i10, _, _ = select_services_for_context(
            self.edition, specialty_id=self.spec.id, mkb_code="I10", price_on=date(2026, 6, 1)
        )
        self.assertTrue({r["code"]: r["unavailable"] for r in rows_e11}["A09.05.001"])
        self.assertFalse({r["code"]: r["unavailable"] for r in rows_i10}["A09.05.001"])


class PatientSexRestrictionTests(TestCase):
    def setUp(self):
        self.edition = MatrixEdition.objects.create(
            code="sex-ed",
            title="Sex filter",
            effective_from=date(2026, 1, 1),
            status=MatrixEdition.Status.DRAFT,
        )
        cat = DnDiagnosisCategory.objects.create(edition=self.edition, code="c", title="C")
        self.diagnosis = DnDiagnosis.objects.create(
            edition=self.edition, category=cat, mkb_code="C61", title="Рак простаты"
        )
        self.spec = DnSpecialty.objects.create(edition=self.edition, code="uro", title="Урология")
        DnDiagnosisSpecialty.objects.create(
            diagnosis=self.diagnosis, specialty=self.spec, kind=DnDiagnosisSpecialty.Kind.PRIMARY
        )
        self.svc_any = DnService.objects.create(
            edition=self.edition, code="B01", title="Общая услуга", sort_order=0
        )
        self.svc_male = DnService.objects.create(
            edition=self.edition,
            code="A09.05.130",
            title="ПСА",
            sort_order=1,
            sex_restriction=DnService.SexRestriction.MALE,
        )
        for svc in (self.svc_any, self.svc_male):
            DnServiceRequirement.objects.create(service=svc, diagnosis=self.diagnosis, specialty=self.spec)
        period = DnServicePricePeriod.objects.create(
            edition=self.edition, code="p1", title="", valid_from=date(2026, 1, 1), valid_to=None
        )
        DnServicePrice.objects.create(period=period, service=self.svc_any, amount="10.00", currency="RUB")
        DnServicePrice.objects.create(period=period, service=self.svc_male, amount="20.00", currency="RUB")
        self.cache = build_matrix_pick_cache(self.edition)

    def _codes(self, patient_sex: str | None) -> list[str]:
        rows, _, _ = select_services_from_cache(
            self.cache,
            specialty_id=self.spec.id,
            mkb_code="C61",
            price_on=date(2026, 6, 1),
            patient_sex=patient_sex,
        )
        return [r["code"] for r in rows]

    def test_male_patient_gets_psa(self):
        codes = self._codes("M")
        self.assertIn("A09.05.130", codes)
        self.assertIn("B01", codes)

    def test_female_patient_excludes_psa(self):
        codes = self._codes("F")
        self.assertNotIn("A09.05.130", codes)
        self.assertIn("B01", codes)

    def test_unknown_sex_includes_all(self):
        codes = self._codes(None)
        self.assertIn("A09.05.130", codes)
        self.assertIn("B01", codes)


class BundleChecksumTests(TestCase):
    def test_build_bundle_checksum_validates(self):
        from apps.dn_matrix.services.bundle import build_bundle, verify_bundle_checksum

        edition = MatrixEdition.objects.create(
            code="chk",
            title="Chk",
            effective_from=date(2026, 1, 1),
            status=MatrixEdition.Status.DRAFT,
        )
        data = build_bundle(edition)
        verify_bundle_checksum(data)


class BatchPickNotPassedTests(TestCase):
    def setUp(self):
        self.edition = MatrixEdition.objects.create(
            code="batch-ed",
            title="Batch",
            effective_from=date(2026, 1, 1),
            status=MatrixEdition.Status.DRAFT,
        )
        cat = DnDiagnosisCategory.objects.create(edition=self.edition, code="c", title="C")
        self.d_i11 = DnDiagnosis.objects.create(
            edition=self.edition, category=cat, mkb_code="I11.0", title="ГБ"
        )
        self.d_e11 = DnDiagnosis.objects.create(
            edition=self.edition, category=cat, mkb_code="E11.8", title="СД"
        )
        self.spec = DnSpecialty.objects.create(
            edition=self.edition, code="sp_6", title="Терапевт", sort_order=1
        )
        for d in (self.d_i11, self.d_e11):
            DnDiagnosisSpecialty.objects.create(
                diagnosis=d, specialty=self.spec, kind=DnDiagnosisSpecialty.Kind.PRIMARY
            )
        self.svc_ecg = DnService.objects.create(
            edition=self.edition, code="A04.10.002", title="ЭКГ", sort_order=0
        )
        self.svc_glu = DnService.objects.create(
            edition=self.edition, code="A09.05.023", title="Глюкоза", sort_order=1
        )
        DnServiceRequirement.objects.create(service=self.svc_ecg, diagnosis=self.d_i11, specialty=self.spec)
        DnServiceRequirement.objects.create(service=self.svc_glu, diagnosis=self.d_e11, specialty=self.spec)

    def test_grouped_includes_secondary_services(self):
        from apps.dn_matrix.services.batch_pick import COL_SERVICES, enrich_not_passed_rows

        rows, status = enrich_not_passed_rows(
            [
                {
                    "Основной МКБ": "I11.0",
                    "Сопутствующие МКБ": "E11.8",
                    "Профиль": "Терапия",
                }
            ],
            self.edition,
            grouped=True,
        )
        self.assertIn("A04.10.002", rows[0][COL_SERVICES])
        self.assertIn("A09.05.023", rows[0][COL_SERVICES])
        self.assertIn("Batch", status)

    def test_detail_ignores_accompanying(self):
        from apps.dn_matrix.services.batch_pick import COL_SERVICES, enrich_not_passed_rows

        rows, _ = enrich_not_passed_rows(
            [{"МКБ": "I11.0", "Профиль": "Терапия", "Сопутствующие МКБ": "E11.8"}],
            self.edition,
            grouped=False,
        )
        self.assertIn("A04.10.002", rows[0][COL_SERVICES])
        self.assertNotIn("A09.05.023", rows[0][COL_SERVICES])
