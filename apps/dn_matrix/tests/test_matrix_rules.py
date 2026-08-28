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
