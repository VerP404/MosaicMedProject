from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, text
from config.settings import DATABASES

# Настройка подключения к базе данных
postgres_settings = DATABASES['default']
engine = create_engine(
    f'postgresql://{postgres_settings["USER"]}:{postgres_settings["PASSWORD"]}@{postgres_settings["HOST"]}:{postgres_settings["PORT"]}/{postgres_settings["NAME"]}'
)

columns_table = {
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
}


class DataLoader:
    def __init__(self, engine, table_name, columns_table, file_format='csv', sep=';', dtype='str'):
        """
        Инициализация загрузчика данных.

        :param engine: SQLAlchemy engine для подключения к базе данных
        :param table_name: Название таблицы, в которую будут загружены данные
        :param columns_table: Словарь для переименования столбцов
        :param file_format: Формат файла (по умолчанию CSV)
        :param sep: Разделитель для CSV файлов (по умолчанию ;)
        :param dtype: Тип данных для чтения (по умолчанию строки)
        """
        self.engine = engine
        self.table_name = table_name
        self.columns_table = columns_table
        self.file_format = file_format
        self.sep = sep
        self.dtype = dtype

    def load_data(self, file_path):
        """
        Основной метод для загрузки данных из файла в таблицу.
        :param file_path: Путь к файлу
        """
        total_start_time = datetime.now()
        print("Стартовое время:", total_start_time)

        # Шаг 1: Загрузка данных
        stage_start_time = datetime.now()

        if self.file_format == 'csv':
            df = pd.read_csv(file_path, sep=self.sep, low_memory=False, dtype=self.dtype)
        elif self.file_format == 'excel':
            df = pd.read_excel(file_path)

        print(f"Файл загружен. Количество строк: {df.shape[0]}")

        # Проверка столбцов
        self._check_columns(df)

        stage_end_time = datetime.now()
        elapsed_time = stage_end_time - stage_start_time
        print(f"Этап 1 завершён. Время выполнения: {elapsed_time}")

        # Шаг 2: Переименование столбцов
        self._rename_columns(df)

        # Шаг 3: Обработка DataFrame
        df = self._process_dataframe(df)

        # Шаг 4: Удаление существующих строк по talon
        self._delete_existing_rows(df)

        # Шаг 5: Загрузка данных в базу
        self._load_to_db(df)

        # Финальное время
        total_end_time = datetime.now()
        elapsed_time = total_end_time - total_start_time
        print(f"Общее время выполнения: {elapsed_time}")

    def _check_columns(self, df):
        """
        Проверяет наличие и соответствие столбцов.
        """
        file_columns = set(df.columns)
        expected_columns = set(self.columns_table.keys())

        missing_columns = expected_columns - file_columns
        extra_columns = file_columns - expected_columns

        if missing_columns or extra_columns:
            if missing_columns:
                print(f"Отсутствующие столбцы: {missing_columns}")
            if extra_columns:
                print(f"Лишние столбцы: {extra_columns}")
            raise ValueError("Структура файла не соответствует ожиданиям.")

    def _rename_columns(self, df):
        """
        Переименовывает столбцы DataFrame на основе словаря.
        """
        df.rename(columns=self.columns_table, inplace=True)
        print("Столбцы переименованы.")

    def _process_dataframe(self, df):
        """
        Обрабатывает DataFrame: удаляет NaN и преобразует данные в строки.
        """
        df.dropna(subset=["patient"], inplace=True)
        df.fillna('-', inplace=True)
        # Удаляем неразрывные пробелы (NBSP) и заменяем их на обычные пробелы
        df.replace('\u00A0', ' ', regex=True, inplace=True)
        df = df.astype(str)
        print("Данные обработаны.")
        return df

    def _delete_existing_rows(self, df):
        """
        Удаляет строки из базы данных, если talon совпадает с talon из DataFrame.
        """
        try:
            # Приводим значения talon в DataFrame к строковому типу, если они еще не строки
            df['talon'] = df['talon'].astype(str)

            # Получаем список талонов из базы данных
            with self.engine.connect() as connection:
                talons_in_db = connection.execute(text(f"SELECT talon FROM {self.table_name}")).fetchall()
                # Поскольку fetchall возвращает кортежи, берем только первый элемент каждого кортежа
                talons_in_db = {str(row[0]) for row in talons_in_db}  # Приводим к строке для совместимости

            # Получаем список талонов из DataFrame
            talons_in_df = set(df['talon'])

            # Определяем талоны, которые присутствуют и в базе, и в DataFrame
            talons_to_delete = talons_in_df.intersection(talons_in_db)

            if talons_to_delete:
                # Удаляем строки с совпадающими talon из базы данных
                with self.engine.begin() as connection:  # Явная транзакция
                    delete_query = text(f"DELETE FROM {self.table_name} WHERE talon = ANY(:talons)")
                    connection.execute(delete_query, {'talons': list(talons_to_delete)})
                    connection.commit()  # Фиксируем транзакцию
                print(f"Удалены строки с {len(talons_to_delete)} талонами из базы данных.")
            else:
                print("Совпадающие талоны отсутствуют. Удаление не требуется.")

        except Exception as e:
            print(f"Ошибка при удалении существующих строк: {e}")

    def _load_to_db(self, df):
        """
        Загружает данные в базу данных с отслеживанием прогресса.
        """
        total_rows = df.shape[0]
        loaded_rows = 0
        try:
            for chunk_start in range(0, total_rows, 1000):
                chunk = df.iloc[chunk_start:chunk_start + 1000]
                chunk.to_sql(
                    name=self.table_name,
                    con=self.engine,
                    if_exists='append',
                    index=False,
                    method='multi'
                )
                loaded_rows += chunk.shape[0]
                print(f"Загружено {loaded_rows} строк из {total_rows}.")
        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")


if __name__ == "__main__":
    # file_path = fr"C:\DjangoProject\MosaicMedProject\journal_20240917(1).csv"
    file_path = fr"C:\Users\frdro\Downloads\Telegram Desktop\journal_20241004(2).csv"

    loader = DataLoader(engine=engine, table_name="data_loader_omsdata", columns_table=columns_table)
    loader.load_data(file_path)
