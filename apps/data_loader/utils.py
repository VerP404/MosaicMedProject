# utils.py
import csv
from .serializers import OMSDataSerializer

CSV_TO_MODEL_MAPPING = {
    "Талон": "talon",
    "Источник": "source",
    "ID источника": "source_id",
    "Номер счёта": "account_number",
    "Дата выгрузки": "upload_date",
    "Причина аннулирования": "cancellation_reason",
    "Статус": "status",
    "Тип талона": "talon_type",
    "Цель": "goal",
    "Фед. цель": "federal_goal",
    "Пациент": "patient",
    "Дата рождения": "birth_date",
    "Возраст": "age",
    "Пол": "gender",
    "Полис": "policy",
    "Код СМО": "smo_code",
    "Страховая": "insurance",
    "ЕНП": "enp",
    "Начало лечения": "treatment_start",
    "Окончание лечения": "treatment_end",
    "Врач": "doctor",
    "Врач (Профиль МП)": "doctor_profile",
    "Должность мед.персонала (V021)": "staff_position",
    "Подразделение": "department",
    "Условия оказания помощи": "care_conditions",
    "Вид мед. помощи": "medical_assistance_type",
    "Тип заболевания": "disease_type",
    "Характер основного заболевания": "main_disease_character",
    "Посещения": "visits",
    "Посещения в МО": "mo_visits",
    "Посещения на Дому": "home_visits",
    "Случай": "case",
    "Диагноз основной (DS1)": "main_diagnosis",
    "Сопутствующий диагноз (DS2)": "additional_diagnosis",
    "Профиль МП": "mp_profile",
    "Профиль койки": "bed_profile",
    "Диспансерное наблюдение": "dispensary_monitoring",
    "Специальность": "specialty",
    "Исход": "outcome",
    "Результат": "result",
    "Оператор": "operator",
    "Первоначальная дата ввода": "initial_input_date",
    "Дата последнего изменения": "last_change_date",
    "Тариф": "tariff",
    "Сумма": "amount",
    "Оплачено": "paid",
    "Тип оплаты": "payment_type",
    "Санкции": "sanctions",
    "КСГ": "ksg",
    "КЗ": "kz",
    "Код схемы лекарственной терапии": "therapy_schema_code",
    "УЕТ": "uet",
    "Классификационный критерий": "classification_criterion",
    "ШРМ": "shrm",
    "МО, направившая": "directing_mo",
    "Код способа оплаты": "payment_method_code",
    "Новорожденный": "newborn",
    "Представитель": "representative",
    "Доп. инф. о статусе талона": "additional_status_info",
    "КСЛП": "kslp",
    "Источник оплаты": "payment_source",
    "Отчетный период выгрузки": "report_period",
}


def process_csv_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            # Удаляем кавычки из всех значений в строке
            mapped_row = {CSV_TO_MODEL_MAPPING.get(key.strip('"').strip("'"), key): value.strip('"').strip("'") for
                          key, value in row.items()}

            # Логируем значения поля 'talon' для диагностики
            print(f"Проверяем поле 'talon': {mapped_row.get('talon')}")

            serializer = OMSDataSerializer(data=mapped_row)
            if serializer.is_valid():
                serializer.save()
            else:
                print(f"Ошибка в данных: {serializer.errors}")
