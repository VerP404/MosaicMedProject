import pandas as pd
from sqlalchemy import create_engine, text
from config.settings import DATABASES

# Настройка подключения к базе данных
postgres_settings = DATABASES['default']
engine = create_engine(
    f'postgresql://{postgres_settings["USER"]}:{postgres_settings["PASSWORD"]}@{postgres_settings["HOST"]}:{postgres_settings["PORT"]}/{postgres_settings["NAME"]}'
)

def load_csv_to_omsdata(file_path):
    print("Подключение к базе данных...")
    with engine.connect() as connection:
        print("Таблица data_loader_omsdata доступна.")

        # Вывод информации о текущих записях
        existing_records = connection.execute(text("SELECT COUNT(*) FROM data_loader_omsdata")).scalar()
        print(f"Количество записей в таблице до загрузки: {existing_records}")

        # Загрузка CSV с помощью pandas
        df = pd.read_csv(file_path, sep=';', low_memory=False, na_values="-", dtype='str')

        # Печать заголовков для проверки
        print("Заголовки CSV файла:", df.columns.tolist())

        # Переименование столбцов, чтобы они соответствовали параметрам SQL
        df.rename(columns={
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
            "Отчетный период выгрузки": "report_period"
        }, inplace=True)

        # Удаление строк, где отсутствует значение в поле "talon"
        df.dropna(subset=["talon"], inplace=True)

        # Преобразование столбца 'talon' в строку
        df['talon'] = df['talon'].astype(str)

        # Счетчики для логирования
        added_count = 0
        updated_count = 0
        error_count = 0

        # Цикл для обработки каждой строки данных
        for _, row in df.iterrows():
            try:
                talon = row['talon']

                # Проверка, существует ли уже запись с таким талоном
                select_query = text("SELECT id FROM data_loader_omsdata WHERE talon = :talon")
                result = connection.execute(select_query, {"talon": talon}).fetchone()

                if result:
                    # Обновление существующей записи
                    update_query = """
                        UPDATE data_loader_omsdata
                        SET source = :source, source_id = :source_id, account_number = :account_number, upload_date = :upload_date,
                            cancellation_reason = :cancellation_reason, status = :status, talon_type = :talon_type, goal = :goal,
                            federal_goal = :federal_goal, patient = :patient, birth_date = :birth_date, age = :age, gender = :gender,
                            policy = :policy, smo_code = :smo_code, insurance = :insurance, enp = :enp, treatment_start = :treatment_start,
                            treatment_end = :treatment_end, doctor = :doctor, doctor_profile = :doctor_profile, staff_position = :staff_position,
                            department = :department, care_conditions = :care_conditions, medical_assistance_type = :medical_assistance_type,
                            disease_type = :disease_type, main_disease_character = :main_disease_character, visits = :visits,
                            mo_visits = :mo_visits, home_visits = :home_visits, "case" = :case, main_diagnosis = :main_diagnosis,
                            additional_diagnosis = :additional_diagnosis, mp_profile = :mp_profile, bed_profile = :bed_profile,
                            dispensary_monitoring = :dispensary_monitoring, specialty = :specialty, outcome = :outcome, result = :result,
                            operator = :operator, initial_input_date = :initial_input_date, last_change_date = :last_change_date,
                            tariff = :tariff, amount = :amount, paid = :paid, payment_type = :payment_type, sanctions = :sanctions,
                            ksg = :ksg, kz = :kz, therapy_schema_code = :therapy_schema_code, uet = :uet,
                            classification_criterion = :classification_criterion, shrm = :shrm, directing_mo = :directing_mo,
                            payment_method_code = :payment_method_code, newborn = :newborn, representative = :representative,
                            additional_status_info = :additional_status_info, kslp = :kslp, payment_source = :payment_source,
                            report_period = :report_period
                        WHERE talon = :talon
                    """
                    connection.execute(text(update_query), row.to_dict())
                    updated_count += 1
                else:
                    # Вставка новой записи
                    insert_query = """
                        INSERT INTO data_loader_omsdata (
                            talon, source, source_id, account_number, upload_date, cancellation_reason, status,
                            talon_type, goal, federal_goal, patient, birth_date, age, gender, policy, smo_code,
                            insurance, enp, treatment_start, treatment_end, doctor, doctor_profile, staff_position,
                            department, care_conditions, medical_assistance_type, disease_type, main_disease_character,
                            visits, mo_visits, home_visits, "case", main_diagnosis, additional_diagnosis, mp_profile,
                            bed_profile, dispensary_monitoring, specialty, outcome, result, operator, initial_input_date,
                            last_change_date, tariff, amount, paid, payment_type, sanctions, ksg, kz, therapy_schema_code,
                            uet, classification_criterion, shrm, directing_mo, payment_method_code, newborn,
                            representative, additional_status_info, kslp, payment_source, report_period
                        ) VALUES (
                            :talon, :source, :source_id, :account_number, :upload_date, :cancellation_reason, :status,
                            :talon_type, :goal, :federal_goal, :patient, :birth_date, :age, :gender, :policy, :smo_code,
                            :insurance, :enp, :treatment_start, :treatment_end, :doctor, :doctor_profile, :staff_position,
                            :department, :care_conditions, :medical_assistance_type, :disease_type, :main_disease_character,
                            :visits, :mo_visits, :home_visits, :case, :main_diagnosis, :additional_diagnosis, :mp_profile,
                            :bed_profile, :dispensary_monitoring, :specialty, :outcome, :result, :operator, :initial_input_date,
                            :last_change_date, :tariff, :amount, :paid, :payment_type, :sanctions, :ksg, :kz, :therapy_schema_code,
                            :uet, :classification_criterion, :shrm, :directing_mo, :payment_method_code, :newborn,
                            :representative, :additional_status_info, :kslp, :payment_source, :report_period
                        )
                    """
                    connection.execute(text(insert_query), row.to_dict())
                    added_count += 1

            except Exception as e:
                print(f"Ошибка при обработке строки с талоном {talon}: {e}")
                error_count += 1

        # Вывод информации о записях после выполнения
        final_records = connection.execute(text("SELECT COUNT(*) FROM data_loader_omsdata")).scalar()
        print(f"Количество записей в таблице после загрузки: {final_records}")

    # Логирование результатов
    print(f"Обновлено записей: {updated_count}")
    print(f"Добавлено новых записей: {added_count}")
    print(f"Ошибок при обработке: {error_count}")

if __name__ == "__main__":
    # Замените на правильный путь к вашему CSV файлу
    file_path = fr"C:\Users\RDN\Downloads\journal_20241004 (2).csv"
    load_csv_to_omsdata(file_path)