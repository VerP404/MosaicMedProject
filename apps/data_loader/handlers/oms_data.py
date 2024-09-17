import pandas as pd
from django.contrib import messages

from apps.data_loader.models.oms_data import OMSData


def handle_oms_data(file, request):
    df = pd.read_csv(file, sep=';', low_memory=False, na_values="-", dtype='str')

    required_fields = ['Талон']  # Обязательно
    model_fields = ['Талон', 'Источник', 'ID источника', 'Номер счёта', 'Дата выгрузки', 'Причина аннулирования',
                    'Статус',
                    'Тип талона', 'Цель', 'Фед. цель', 'Пациент', 'Дата рождения', 'Возраст', 'Пол', 'Полис',
                    'Код СМО', 'Страховая', 'ЕНП', 'Начало лечения', 'Окончание лечения', 'Врач', 'Врач (Профиль МП)',
                    'Должность мед.персонала (V021)', 'Подразделение', 'Условия оказания помощи', 'Вид мед. помощи',
                    'Тип заболевания', 'Характер основного заболевания', 'Посещения', 'Посещения в МО',
                    'Посещения на Дому',
                    'Случай', 'Диагноз основной (DS1)', 'Сопутствующий диагноз (DS2)', 'Профиль МП', 'Профиль койки',
                    'Диспансерное наблюдение', 'Специальность', 'Исход', 'Результат', 'Оператор',
                    'Первоначальная дата ввода', 'Дата последнего изменения', 'Тариф', 'Сумма', 'Оплачено',
                    'Тип оплаты', 'Санкции', 'КСГ', 'КЗ', 'Код схемы лекарственной терапии', 'УЕТ',
                    'Классификационный критерий', 'ШРМ', 'МО, направившая', 'Код способа оплаты', 'Новорожденный',
                    'Представитель', 'Доп. инф. о статусе талона', 'КСЛП', 'Источник оплаты',
                    'Отчетный период выгрузки']

    # Проверяем обязательные поля
    missing_required_fields = [field for field in required_fields if field not in df.columns]
    if missing_required_fields:
        messages.error(request,
                       f"Отсутствуют обязательные поля: {', '.join(missing_required_fields)}. Пожалуйста, проверьте CSV файл.")

    # Проверяем наличие всех полей модели в CSV
    missing_fields = [field for field in model_fields if field not in df.columns]
    extra_fields = [field for field in df.columns if field not in model_fields]

    if missing_fields:
        messages.warning(request,
                         f"Отсутствуют поля модели: {', '.join(missing_fields)}. Пожалуйста, проверьте CSV файл.")

    if extra_fields:
        messages.info(request, f"Обнаружены дополнительные поля в CSV: {', '.join(extra_fields)}.")

    # Загружаем данные в базу данных
    for _, row in df.iterrows():
        data, created = OMSData.objects.update_or_create(
            talon=row.get('Талон', ''),
            defaults={
                'source': row.get('Источник', ''),
                'source_id': row.get('ID источника', ''),
                'account_number': row.get('Номер счёта', ''),
                'upload_date': pd.to_datetime(row.get('Дата выгрузки', ''), errors='coerce'),
                'cancellation_reason': row.get('Причина аннулирования', ''),
                'status': row.get('Статус', ''),
                'talon_type': row.get('Тип талона', ''),
                'goal': row.get('Цель', ''),
                'federal_goal': row.get('Фед. цель', ''),
                'patient': row.get('Пациент', ''),
                'birth_date': pd.to_datetime(row.get('Дата рождения', ''), errors='coerce'),
                'gender': row.get('Пол', ''),
                'policy': row.get('Полис', ''),
                'smo_code': row.get('Код СМО', ''),
                'insurance': row.get('Страховая', ''),
                'enp': row.get('ЕНП', ''),
                'treatment_start': pd.to_datetime(row.get('Начало лечения', ''), errors='coerce'),
                'treatment_end': pd.to_datetime(row.get('Окончание лечения', ''), errors='coerce'),
                'doctor': row.get('Врач', ''),
                'doctor_profile': row.get('Врач (Профиль МП)', ''),
                'staff_position': row.get('Должность мед.персонала (V021)', ''),
                'department': row.get('Подразделение', ''),
                'care_conditions': row.get('Условия оказания помощи', ''),
                'medical_assistance_type': row.get('Вид мед. помощи', ''),
                'disease_type': row.get('Тип заболевания', ''),
                'main_disease_character': row.get('Характер основного заболевания', ''),
                'visits': pd.to_numeric(row.get('Посещения', ''), errors='coerce'),
                'mo_visits': pd.to_numeric(row.get('Посещения в МО', ''), errors='coerce'),
                'home_visits': pd.to_numeric(row.get('Посещения на Дому', ''), errors='coerce'),
                'case': row.get('Случай', ''),
                'main_diagnosis': row.get('Диагноз основной (DS1)', ''),
                'additional_diagnosis': row.get('Сопутствующий диагноз (DS2)', ''),
                'mp_profile': row.get('Профиль МП', ''),
                'bed_profile': row.get('Профиль койки', ''),
                'dispensary_monitoring': row.get('Диспансерное наблюдение', ''),
                'specialty': row.get('Специальность', ''),
                'outcome': row.get('Исход', ''),
                'result': row.get('Результат', ''),
                'operator': row.get('Оператор', ''),
                'initial_input_date': pd.to_datetime(row.get('Первоначальная дата ввода', ''), errors='coerce'),
                'last_change_date': pd.to_datetime(row.get('Дата последнего изменения', ''), errors='coerce'),
                'tariff': pd.to_numeric(row.get('Тариф', ''), errors='coerce'),
                'amount': pd.to_numeric(row.get('Сумма', ''), errors='coerce'),
                'paid': pd.to_numeric(row.get('Оплачено', ''), errors='coerce'),
                'payment_type': row.get('Тип оплаты', ''),
                'sanctions': row.get('Санкции', ''),
                'ksg': row.get('КСГ', ''),
                'kz': row.get('КЗ', ''),
                'therapy_schema_code': row.get('Код схемы лекарственной терапии', ''),
                'uet': pd.to_numeric(row.get('УЕТ', ''), errors='coerce'),
                'classification_criterion': row.get('Классификационный критерий', ''),
                'shrm': row.get('ШРМ', ''),
                'directing_mo': row.get('МО, направившая', ''),
                'payment_method_code': row.get('Код способа оплаты', ''),
                'newborn': row.get('Новорожденный', '0') == '1',
                'representative': row.get('Представитель', ''),
                'additional_status_info': row.get('Доп. инф. о статусе талона', ''),
                'kslp': row.get('КСЛП', ''),
                'payment_source': row.get('Источник оплаты', ''),
                'report_period': row.get('Отчетный период выгрузки', ''),
            }
        )
