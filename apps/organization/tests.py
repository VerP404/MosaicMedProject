from django.test import TestCase

from apps.organization.models import (
    Building,
    Department,
    MedicalOrganization,
    OMSDepartment,
    Station,
)
from apps.organization.services.structure_io import (
    build_native_structure,
    build_portal_medical_structure,
    import_native_structure,
)


class StructureIOTests(TestCase):
    def setUp(self):
        self.org = MedicalOrganization.objects.create(
            name='БУЗ ВО "ВГП №16"',
            name_kvazar='ВГП16',
            name_miskauz='ВГП16',
            address='г. Воронеж',
            phone_number='+7',
            email='test@example.com',
            code_mo='003',
            oid_mo='1.2.643.5.1.13.13.12.2.36.003',
        )
        building = Building.objects.create(
            organization=self.org,
            name='Корпус №1',
            additional_name='ГП16',
            name_kvazar='К1',
            name_miskauz='К1',
        )
        Building.objects.create(
            organization=self.org,
            name='Общий персонал',
            additional_name='',
            name_kvazar='',
            name_miskauz='',
        )
        department = Department.objects.create(
            building=building,
            name='Терапия',
            additional_name='',
        )
        OMSDepartment.objects.create(department=department, name='Терапевтическое')
        Station.objects.create(department=department, code='101', name='Участок 1')

    def test_portal_export_shape(self):
        payload = build_portal_medical_structure(
            region_code='36',
            region_name='Воронеж',
            org_code='003',
        )
        self.assertEqual(payload['export_info']['source'], 'mosaicmedproject')
        self.assertEqual(payload['export_info']['total_buildings'], 2)
        self.assertEqual(payload['export_info']['total_departments'], 1)
        self.assertEqual(payload['export_info']['total_districts'], 1)
        self.assertEqual(payload['export_info']['total_department_synonyms'], 1)

        org = payload['regions'][0]['organizations'][0]
        self.assertEqual(org['org_code'], '003')
        self.assertEqual(org['full_code'], '36.003')
        self.assertEqual(len(org['buildings']), 2)

        medical = next(b for b in org['buildings'] if b['name'] == 'Корпус №1')
        general = next(b for b in org['buildings'] if b['name'] == 'Общий персонал')
        self.assertTrue(medical['is_medical'])
        self.assertFalse(general['is_medical'])
        self.assertEqual(medical['departments'][0]['synonyms'][0]['external_system'], 'weboms')
        self.assertEqual(medical['departments'][0]['districts'][0]['name'], '101')

        # стабильные UUID при повторном экспорте
        again = build_portal_medical_structure(org_code='003')
        self.assertEqual(
            org['buildings'][0]['external_id'],
            again['regions'][0]['organizations'][0]['buildings'][0]['external_id'],
        )

    def test_portal_merge_reuses_external_ids(self):
        first = build_portal_medical_structure(org_code='003')
        # подменяем external_id в эталоне
        first['regions'][0]['organizations'][0]['external_id'] = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
        merged = build_portal_medical_structure(org_code='003', merge_from=first)
        self.assertEqual(
            merged['regions'][0]['organizations'][0]['external_id'],
            'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
        )

    def test_native_roundtrip(self):
        native = build_native_structure()
        self.assertEqual(native['format'], 'mosaicmedproject_organization')
        self.assertEqual(len(native['organization']['buildings']), 2)

        stats = import_native_structure(native, clear_tree=True)
        self.assertEqual(stats['buildings'], 2)
        self.assertEqual(stats['departments'], 1)
        self.assertEqual(stats['oms'], 1)
        self.assertEqual(stats['stations'], 1)
        self.assertEqual(Building.objects.count(), 2)
        self.assertEqual(Station.objects.filter(code='101').count(), 1)
