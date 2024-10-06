from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, text
from config.settings import DATABASES

# Настройка подключения к базе данных
postgres_settings = DATABASES['default']
engine = create_engine(
    f'postgresql://{postgres_settings["USER"]}:{postgres_settings["PASSWORD"]}@{postgres_settings["HOST"]}:{postgres_settings["PORT"]}/{postgres_settings["NAME"]}'
)

columns_table_oms = {
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
columns_table_detailed = {
    "Номер талона": "talon_number",
    "Счет": "account_number",
    "Дата выгрузки": "upload_date",
    "Статус": "status",
    "МО": "mo",
    "Дата начала": "start_date",
    "Дата окончания": "end_date",
    "Серия полиса": "policy_series",
    "Номер полиса": "policy_number",
    "ЕНП": "enp",
    "Фамилия": "last_name",
    "Имя": "first_name",
    "Отчество": "middle_name",
    "Страховая организация": "insurance_org",
    "Пол": "gender",
    "Дата рождения": "birth_date",
    "Тип талона": "talon_type",
    "Основной диагноз": "main_diagnosis",
    "Сопутствующий диагноз": "additional_diagnosis",
    "Группа здоровья": "health_group",
    "Доктор (Код)": "doctor_code",
    "Доктор (ФИО)": "doctor_name",
    "Стоимость": "cost",
    "Название услуги": "service_name",
    "Номенклатурный код услуги": "service_code",
    "Доктор-Услуги (Код)": "service_doctor_code",
    "Доктор-Услуги (ФИО)": "service_doctor_name",
    "Дата-Услуги": "service_date",
    "Статус-Услуги": "service_status",
    "Маршрут": "route",
    "Подразделение врача-Услуги": "service_department",
    "Код МО (при оказ.услуги в другой МО)": "external_mo_code"
}


class DataLoader:
    def __init__(self,
                 engine,
                 table_name,
                 data_type_name,
                 column_check,
                 columns_for_update,
                 file_format='csv',
                 sep=';', dtype='str'):
        """
        Инициализация загрузчика данных.

        :param engine: SQLAlchemy engine для подключения к базе данных
        :param table_name: Название таблицы, в которую будут загружены данные.
        :param data_type_name: Экземпляр модели DataType, для которого выполняется загрузка данных (ОМС, Квазар и тд).
                          Смотреть в админке.
        :param column_check: Название столбца для проверки на null, чтобы убрать ошибки чтения файла
        :param columns_for_update: Список столбцов для поиска в df и таблице, чтобы обновить строки
        :param file_format: Формат файла (по умолчанию CSV)
        :param sep: Разделитель для CSV файлов (по умолчанию ; )
        :param dtype: Тип данных для чтения (по умолчанию строки)
        """
        self.engine = engine
        self.table_name = table_name
        self.data_type_name = data_type_name
        self.columns_mapping = self._get_columns_mapping()
        self.column_check = column_check
        self.columns_for_update = columns_for_update
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
        df = self._load_file_to_df(file_path)
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

        # Шаг 4: Удаление существующих строк по уникальному столбцу
        self._delete_existing_rows(df)

        # Шаг 5: Загрузка данных в базу
        self._load_data_to_db(df)

        # Финальное время
        total_end_time = datetime.now()
        elapsed_time = total_end_time - total_start_time
        print(f"Общее время выполнения: {elapsed_time}")

    def _get_columns_mapping(self):
        """
        Загружает соответствия столбцов для типа данных через SQL запрос, основываясь на имени типа данных.
        """
        sql_query = """
            SELECT fm.csv_column_name, fm.model_field_name
            FROM data_loader_datatypefieldmapping fm
            JOIN data_loader_datatype dt ON fm.data_type_id = dt.id
            WHERE dt.name = :data_type_name
        """

        # Выполняем SQL запрос и возвращаем результат как список кортежей
        with self.engine.connect() as connection:
            result = connection.execute(text(sql_query), {'data_type_name': self.data_type_name}).fetchall()

        # Преобразуем результат запроса в словарь {csv_column_name: model_field_name}
        columns_mapping = {row[0]: row[1] for row in result}  # Используем индексы вместо строк

        return columns_mapping

    def _load_file_to_df(self, file_path):
        """Загрузка файла в DataFrame."""
        if self.file_format == 'csv':
            df = pd.read_csv(file_path, sep=self.sep, low_memory=False, dtype=self.dtype)
        elif self.file_format == 'excel':
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Неподдерживаемый формат файла")
        return df

    def _check_columns(self, df):
        """
        Проверяет наличие и соответствие столбцов.
        """
        file_columns = set(df.columns)
        expected_columns = set(self.columns_mapping.keys())

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
        df.rename(columns=self.columns_mapping, inplace=True)
        print("Столбцы переименованы.")

    def _process_dataframe(self, df):
        """
        Обрабатывает DataFrame: удаляет NaN и преобразует данные в строки.
        """
        # Удаляем строки, содержащие NaN на основании столбца column_check
        df.dropna(subset=[self.column_check], inplace=True)
        # Заменяем NaN на '-' в датафрейме
        df.fillna('-', inplace=True)
        # Удаляем неразрывные пробелы (NBSP) и заменяем их на обычные пробелы
        df.replace('\u00A0', ' ', regex=True, inplace=True)
        # Проверяем что тип данных у всех столбцов "текстовый"
        df = df.astype(str)
        print("Данные обработаны.")
        return df

    def _delete_existing_rows(self, df):
        """
        Удаляет строки из базы данных, если значения в столбцах из columns_for_update совпадают между DataFrame и базой данных.
        """
        try:
            # Приводим значения всех столбцов в DataFrame к строковому типу, если они еще не строки
            for column in self.columns_for_update:
                df[column] = df[column].astype(str)

            # Создаем новый столбец в DataFrame с объединенными значениями столбцов из columns_for_update
            df['combined_key'] = df[self.columns_for_update].apply(lambda row: '_'.join(row.values.astype(str)), axis=1)

            # Получаем записи из базы данных, которые соответствуют указанным столбцам
            with self.engine.connect() as connection:
                # Объединяем столбцы в запросе SQL, чтобы создать такой же "ключ"
                query = f"SELECT {', '.join(self.columns_for_update)} FROM {self.table_name}"
                rows_in_db = connection.execute(text(query)).fetchall()

            # Преобразуем результат из базы данных в множество с объединенными значениями столбцов
            rows_in_db_set = {'_'.join(map(str, row)) for row in rows_in_db}

            # Получаем комбинированные ключи из DataFrame
            combined_keys_in_df = set(df['combined_key'])

            # Определяем ключи, которые присутствуют и в базе данных, и в DataFrame
            keys_to_delete = combined_keys_in_df.intersection(rows_in_db_set)

            if keys_to_delete:
                # Удаляем строки с совпадающими ключами
                with self.engine.begin() as connection:
                    # Используем IN для пакетного удаления строк
                    delete_query = text(
                        f"DELETE FROM {self.table_name} WHERE ('{', '.join(self.columns_for_update)}') IN :keys")
                    connection.execute(delete_query, {'keys': list(keys_to_delete)})

                print(f"Удалены строки с {len(keys_to_delete)} совпадающими значениями.")

            else:
                print("Совпадающие строки отсутствуют. Удаление не требуется.")
            # Удаляем временный столбец combined_key
            df.drop(columns=['combined_key'], inplace=True)
        except Exception as e:
            print(f"Ошибка при удалении существующих строк: {e}")

    def _load_data_to_db(self, df):
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
    # file_path = fr"C:\Users\frdro\Downloads\Telegram Desktop\journal_20241004(2).csv"
    # file_path = fr"C:\Users\frdro\Downloads\Telegram Desktop\journal_Detailed_Medical_Examination_20241006.csv"
    file_path = fr"C:\Users\frdro\Downloads\Telegram Desktop\journal_Doctors_20241006.csv"

    loader = DataLoader(engine=engine,
                        table_name="data_loader_doctordata",
                        data_type_name='DOCTORS',
                        column_check="snils",
                        columns_for_update=['snils', 'doctor_code'],
                        )
    loader.load_data(file_path)
