import tablib
from import_export import resources

from apps.data_loader.models.oms_data import OMSData
from django.contrib import messages


class OMSDataResource(resources.ModelResource):
    class Meta:
        model = OMSData
        fields = (
            'talon', 'source', 'source_id', 'account_number', 'upload_date',
            'cancellation_reason', 'status', 'talon_type', 'goal', 'federal_goal',
            'patient', 'birth_date', 'age', 'gender', 'policy', 'smo_code', 'insurance',
            'enp', 'treatment_start', 'treatment_end', 'doctor', 'doctor_profile',
            'staff_position', 'department', 'care_conditions', 'medical_assistance_type',
            'disease_type', 'main_disease_character', 'visits', 'mo_visits', 'home_visits',
            'case', 'main_diagnosis', 'additional_diagnosis', 'mp_profile', 'bed_profile',
            'dispensary_monitoring', 'specialty', 'outcome', 'result', 'operator',
            'initial_input_date', 'last_change_date', 'tariff', 'amount', 'paid',
            'payment_type', 'sanctions', 'ksg', 'kz', 'therapy_schema_code', 'uet',
            'classification_criterion', 'shrm', 'directing_mo', 'payment_method_code',
            'newborn', 'representative', 'additional_status_info', 'kslp', 'payment_source',
            'report_period'
        )

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        # Убедимся, что разделитель 'delimiter' правильно задан
        dataset.headers = dataset[0]
        if dataset.width != 53:  # Проверьте правильное количество колонок
            raise ValueError(f"Ошибка импорта: Ожидалось 53 столбца, найдено {dataset.width}. Проверьте структуру CSV.")
