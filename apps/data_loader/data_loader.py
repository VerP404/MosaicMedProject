from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, text

from apps.data_loader.selenium_scripts_auto import run_selenium_script_auto
from config.settings import DATABASES

# Настройка подключения к базе данных
postgres_settings = DATABASES['default']
engine = create_engine(
    f'postgresql://{postgres_settings["USER"]}:{postgres_settings["PASSWORD"]}@{postgres_settings["HOST"]}:{postgres_settings["PORT"]}/{postgres_settings["NAME"]}'
)


def time_it(stage_name):
    def decorator(method):
        def timed(*args, **kw):
            start_time = datetime.now()
            result = method(*args, **kw)
            end_time = datetime.now()
            elapsed_time = end_time - start_time
            if hasattr(args[0], 'message'):
                args[0].message += f"Этап '{stage_name}' выполнен за: {elapsed_time}\n"
            return result

        return timed

    return decorator


class DataLoader:
    def __init__(self,
                 engine,
                 table_name,
                 data_type_name,
                 column_check,
                 columns_for_update,
                 file_format='csv',
                 sep=';',
                 dtype='str',
                 encoding='utf-8'
                 ):
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
        :param encoding: Кодировка для чтения (по умолчанию cp1251)
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
        self.encoding = encoding
        # Инициализируем переменные для статистики
        self.added_count = 0
        self.updated_count = 0
        self.error_count = 0
        self.message = ''

    @time_it("Общее время загрузки данных")
    def load_data(self, file_path):
        """
        Основной метод для загрузки данных из файла в таблицу.
        :param file_path: Путь к файлу
        """
        total_start_time = datetime.now()

        # Шаг 1: Загрузка данных
        df = self._load_file_to_df(file_path)

        # Проверка столбцов
        self._check_columns(df)

        # Шаг 2: Переименование столбцов
        self._rename_columns(df)

        # Шаг 3: Обработка DataFrame
        df = self._process_dataframe(df)

        # Шаг 4: Удаление существующих строк по уникальному столбцу
        self._delete_existing_rows(df)

        # Шаг 5: Загрузка данных в базу
        self._load_data_to_db(df)

        # Шаг 6: Создаем запись в DataImport
        self._create_data_import_record()

        # Финальное время
        total_end_time = datetime.now()
        elapsed_time = total_end_time - total_start_time

    @time_it("Загрузка списка столбцов из БД")
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

    @time_it("Загрузка файла в DataFrame")
    def _load_file_to_df(self, file_path):
        """Загрузка файла в DataFrame."""
        if self.file_format == 'csv':
            df = pd.read_csv(file_path, sep=self.sep, low_memory=False, na_values="-", dtype=self.dtype,
                             encoding=self.encoding)
        elif self.file_format == 'excel':
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Неподдерживаемый формат файла")
        self.message += f" Файл загружен. Строк: {df.shape[0]}, Столбцов: {df.shape[1]}\n"
        return df

    @time_it("Проверка столбцов в DataFrame")
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
                self.message += f" Отсутствующие столбцы: {missing_columns}\n"
            if extra_columns:
                self.message += f" Лишние столбцы: {extra_columns}\n"
            raise ValueError("Структура файла не соответствует ожиданиям.")

    def _rename_columns(self, df):
        """
        Переименовывает столбцы DataFrame на основе словаря.
        """
        df.rename(columns=self.columns_mapping, inplace=True)

    @time_it("Очистка DataFrame")
    def _process_dataframe(self, df):
        """
        Обрабатывает DataFrame: удаляет NaN и преобразует данные в строки.
        """
        try:
            # Удаляем строки, содержащие NaN на основании столбца column_check
            df.dropna(subset=[self.column_check], inplace=True)
        except KeyError as e:
            self.message += f" Ошибка: столбец '{self.column_check}' не найден в данных. Проверьте наличие столбца в базе.\n"
            self.message += f" Доступные столбцы: {list(df.columns)}\n"
            raise e  # Повторное возбуждение исключения для остановки выполнения, если необходимо

        # Заменяем NaN на '-' в датафрейме
        df.fillna('-', inplace=True)

        # Убираем ` из датафрейма при наличии
        df = df.replace('`', '', regex=True)

        # Удаляем неразрывные пробелы (NBSP) и заменяем их на обычные пробелы
        df.replace('\u00A0', ' ', regex=True, inplace=True)

        # Проверяем что тип данных у всех столбцов "текстовый"
        df = df.astype(str)
        return df

    @time_it("Удаление строк в БД для обновления записей")
    def _delete_existing_rows(self, df):
        """Удаляет строки из базы данных порциями, чтобы избежать переполнения параметров."""
        total_deleted = 0  # Счетчик удаленных строк

        try:
            for column in self.columns_for_update:
                df[column] = df[column].astype(str)

            keys_in_df = df[self.columns_for_update].drop_duplicates()

            # Разделяем данные на чанки по 500 строк, чтобы не превышать лимит параметров
            chunk_size = 500
            chunks = [keys_in_df[i:i + chunk_size] for i in range(0, len(keys_in_df), chunk_size)]

            for chunk in chunks:
                conditions = []
                params = {}
                for idx, row in chunk.iterrows():
                    condition = ' AND '.join([f"{col} = :{col}_{idx}" for col in self.columns_for_update])
                    conditions.append(f"({condition})")

                    for col in self.columns_for_update:
                        params[f"{col}_{idx}"] = row[col]

                condition_str = ' OR '.join(conditions)

                if condition_str:
                    delete_query = text(f"DELETE FROM {self.table_name} WHERE {condition_str}")
                    with self.engine.begin() as connection:
                        result = connection.execute(delete_query, params)
                        total_deleted += result.rowcount  # Увеличиваем счетчик удаленных строк

            self.message += f" Всего удалено строк: {total_deleted}.\n"

        except Exception as e:
            self.message += f" Ошибка при удалении существующих строк: {e}\n"

    @time_it("Загрузка данных в БД")
    def _load_data_to_db(self, df):
        """
        Загружает данные в базу данных с отслеживанием прогресса.
        """
        # Удаляем столбец combined_key, который используется только для внутренней обработки
        if 'combined_key' in df.columns:
            df.drop(columns=['combined_key'], inplace=True)

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
                self.added_count += chunk.shape[0]

            self.message += f"Всего загружено {loaded_rows} строк из {total_rows}.\n"
        except Exception as e:
            self.error_count += 1
            self.message += f" Ошибка при загрузке данных: {e}\n"

    @time_it("Сохранение информации о загрузке в БД")
    def _create_data_import_record(self):
        """
        Создает запись в таблице DataImport с информацией о загрузке через SQL-запрос.
        """
        sql_query = """
        INSERT INTO data_loader_dataimport (csv_file, date_added, added_count, updated_count, error_count, data_type_id)
        VALUES (:csv_file, NOW(), :added_count, :updated_count, :error_count, :data_type_id)
        """

        with self.engine.begin() as connection:
            data_type_query = "SELECT id FROM data_loader_datatype WHERE name = :data_type_name"
            data_type_id_result = connection.execute(
                text(data_type_query),
                {'data_type_name': self.data_type_name}
            ).fetchone()

            if data_type_id_result:
                data_type_id = data_type_id_result[0]
                try:
                    # Выполняем основной запрос, используя фактический data_type_id
                    connection.execute(text(sql_query), {
                        'csv_file': '-',  # Укажите путь к файлу или значение
                        'added_count': self.added_count,
                        'updated_count': self.updated_count,
                        'error_count': self.error_count,
                        'data_type_id': data_type_id
                    })
                    self.message += "Запись в таблице DataImport успешно создана.\n"
                except Exception as e:
                    self.message += f" Ошибка при вставке записи в DataImport: {e}\n"
            else:
                self.message += f" Ошибка: Тип данных с именем '{self.data_type_name}' не найден.\n"

    def load_data_via_selenium(self, username, password, start_date, end_date, start_date_treatment):
        # Запускаем скрипт Selenium для загрузки файла
        success, file_path = run_selenium_script_auto(username, password, start_date, end_date, start_date_treatment)

        if success and file_path:
            # После успешной загрузки файла, передаем его в метод load_data
            return self.load_data(file_path)  # Метод load_data будет обрабатывать CSV
        else:
            self.message += "Ошибка при выполнении скрипта Selenium или файл не был загружен."
            return False, 0, 0, 0
