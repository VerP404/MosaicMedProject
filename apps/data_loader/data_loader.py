from abc import abstractmethod, ABC
from datetime import datetime

import fdb
import pandas as pd
from sqlalchemy import create_engine, text

from apps.data_loader.selenium.oms import selenium_oms, logger
from config.settings import DATABASES

# Настройка подключения к базе данных
postgres_settings = DATABASES['default']
engine = create_engine(
    f'postgresql://{postgres_settings["USER"]}:{postgres_settings["PASSWORD"]}@{postgres_settings["HOST"]}:{postgres_settings["PORT"]}/{postgres_settings["NAME"]}'
)


class BaseDataLoader(ABC):
    """
    Базовый класс для ETL-процесса. Содержит:
    - Общие поля для логирования: message, import_record_id, added_count и т.д.
    - Методы для записи в DataImport: _create_initial_data_import_record, _update_data_import_record
    - run_etl(), который последовательно вызывает:
        1) _create_initial_data_import_record()
        2) extract()
        3) transform()
        4) load()
        5) финальное обновление записи
    - Общая логика transform() и load() (через временную таблицу и MERGE).
    """

    def __init__(self,
                 engine,
                 table_name,
                 table_name_temp,
                 data_type_name,
                 column_mapping,
                 column_check,
                 columns_for_update,
                 file_format='csv',
                 sep=';',
                 dtype=str,
                 encoding='utf-8',
                 clear_all_rows=False):
        """
        :param engine: SQLAlchemy engine для подключения к базе
        :param table_name: Название основной таблицы (например, data_loader_omsdata)
        :param table_name_temp: Название временной таблицы (например, temp_oms_data)
        :param data_type_name: Название типа данных (OMS, Квазар и т.д.) — для записи в DataImport
        :param column_mapping: dict { 'CSV_колонка': 'DB_поле' } для переименования
        :param column_check: Название обязательного столбца (убираем NaN)
        :param columns_for_update: Список полей, по которым делаем MERGE ON CONFLICT
        :param file_format: Формат входных данных (csv, excel и т.п.) — если надо
        :param sep: Разделитель для CSV
        :param dtype: Тип данных (по умолчанию str)
        :param encoding: Кодировка (utf-8, cp1251 и т.д.)
        :param clear_all_rows: При True можем очищать основную таблицу, если это нужно (опционально)
        """

        # -- Параметры и настройки --
        self.engine = engine
        self.table_name = table_name
        self.table_name_temp = table_name_temp
        self.data_type_name = data_type_name
        self.column_mapping = column_mapping
        self.column_check = column_check
        self.columns_for_update = columns_for_update
        self.file_format = file_format
        self.sep = sep
        self.dtype = dtype
        self.encoding = encoding
        self.clear_all_rows = clear_all_rows

        # -- Поля для логирования / статистики (из старого класса) --
        self.message = ''
        self.import_record_id = None
        self.added_count = 0
        self.updated_count = 0
        self.error_count = 0

        # -- Счётчики строк для вывода статистики --
        self.row_counts = {
            "before_processing": 0,
            "after_reading_csv": 0,
            "to_update": 0,
            "to_insert": 0,
            "after_processing": 0,
        }

    # =========================================================================
    # Главный метод, который запускает ETL
    # =========================================================================
    def run_etl(self, source_name: str):
        """
        Общий «шаблон» процесса:
          1. Записываем в DataImport (начало)
          2. extract() – извлечь данные (дочерние классы переопределяют)
          3. transform() – обработка
          4. load() – загрузка (через temp + MERGE)
          5. финальное логирование
        :param source_name: либо путь к файлу, либо что-то ещё (URL, login, etc.)
        """
        start_time = datetime.now()
        self.message += f"[{start_time}] Начало загрузки данных.\n"

        # 1) Создаём запись DataImport (при желании)
        self._create_initial_data_import_record(source_name)

        # 2) EXTRACT (дочерние классы будут реализовывать)
        try:
            logger.info("Начинается этап EXTRACT")
            df = self.extract(source_name)
            self.row_counts["after_reading_csv"] = len(df)
            self.message += f"EXTRACT: получено {len(df)} строк.\n"

            # 3) TRANSFORM
            logger.info("Начинается этап TRANSFORM")
            df = self.transform(df)
            self.message += f"TRANSFORM: осталось {len(df)} строк после очистки.\n"

            # 4) LOAD
            logger.info("Начинается этап LOAD")
            self.load(df)

        except Exception as e:
            logger.error(f"Ошибка во время выполнения ETL: {e}", exc_info=True)
            self.error_count += 1
            self.message += f"ОШИБКА: {e}\n"
            self._update_data_import_record()
            raise

        # Финальное обновление
        end_time = datetime.now()
        elapsed = end_time - start_time
        self.message += f"Готово. Общее время: {elapsed}\n"
        self._update_data_import_record()

    # =========================================================================
    # Методы, которые будут переопределены или уже в базовом классе
    # =========================================================================
    @abstractmethod
    def extract(self, source_name) -> pd.DataFrame:
        """
        Метод извлечения данных. Переопределяется в дочерних классах:
         - если CSV -> читаем CSV
         - если Selenium -> запускаем робот и читаем результат
         - если DB -> запрос к другой БД
        """
        pass

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Общая логика для преобразования DataFrame:
         - выбираем нужные столбцы по column_mapping
         - переименовываем
         - dropna по column_check
         - fillna('-'), убираем лишние символы
         - удаляем дубликаты по columns_for_update
        """
        # Переименование и фильтрация
        df = df[list(self.column_mapping.keys())].rename(columns=self.column_mapping)

        # Удаляем строки, где нет column_check
        df.dropna(subset=[self.column_check], inplace=True)

        # Заполняем пустые
        df.fillna("-", inplace=True)
        df.replace('`', '', regex=True, inplace=True)
        df.replace('\u00A0', ' ', regex=True, inplace=True)

        # Приводим к строкам
        df = df.astype(str)

        # Обрабатываем дубли для "Стационарно"
        if 'goal' in df.columns and 'talon' in df.columns:
            # Фильтруем только строки, где goal == "Стационарно"
            mask = df['goal'] == 'Стационарно'
            stationary_df = df[mask]

            # Для дубликатов добавляем суффиксы _1, _2 и т.д.
            stationary_df['talon'] = stationary_df.groupby('talon').cumcount().add(1).astype(str).radd(
                stationary_df['talon'] + '_')

            # Обновляем исходный DataFrame
            df.loc[mask, 'talon'] = stationary_df['talon']

        # Удаляем дубликаты
        df.drop_duplicates(subset=self.columns_for_update, inplace=True)

        return df

    def load(self, df: pd.DataFrame):
        """
        Новая логика загрузки:
         - Подсчитать строки "до"
         - Создать/очистить временную таблицу
         - to_sql(df) -> temp
         - создать индексы
         - посчитать to_update/to_insert
         - MERGE
         - посчитать строки "после"
        """
        # Подсчёт "до"
        with self.engine.connect() as conn:
            q = f"SELECT COUNT(*) FROM {self.table_name};"
            self.row_counts["before_processing"] = conn.execute(text(q)).scalar()
            self.message += f"Количество строк до обработки: {self.row_counts['before_processing']}\n"
        # Очистка временной таблицы
        with self.engine.connect() as conn:
            exists = conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = '{self.table_name_temp}'
                )
            """)).scalar()
            if exists:
                conn.execute(text(f"TRUNCATE TABLE {self.table_name_temp}"))
            else:
                self.message += f"Таблица {self.table_name_temp} будет создана автоматически.\n"

        # Загрузка во временную таблицу
        df.to_sql(self.table_name_temp, self.engine, if_exists="replace", index=False)

        # Создаём индексы
        self._create_index(self.table_name)
        self._create_index(self.table_name_temp)

        # Считаем строки на update/insert
        with self.engine.connect() as conn:
            rows_to_update_query = f"""
            SELECT COUNT(*)
            FROM {self.table_name_temp} AS temp
            INNER JOIN {self.table_name} AS target
            ON {' AND '.join([f'temp.{col} = target.{col}' for col in self.columns_for_update])}
            """
            self.row_counts["to_update"] = conn.execute(text(rows_to_update_query)).scalar()
            rows_to_insert_query = f"""
            SELECT COUNT(*)
            FROM {self.table_name_temp} AS temp
            LEFT JOIN {self.table_name} AS target
            ON {' AND '.join([f'temp.{col} = target.{col}' for col in self.columns_for_update])}
            WHERE target.{self.columns_for_update[0]} IS NULL
            """
            self.row_counts["to_insert"] = conn.execute(text(rows_to_insert_query)).scalar()

        self.message += f"LOAD: для обновления {self.row_counts['to_update']}, для добавления {self.row_counts['to_insert']}.\n"

        # Проверяем недостающие столбцы
        missing_columns = self._get_missing_columns()

        # Формируем MERGE
        merge_query = self._build_merge_query(missing_columns)

        # Выполняем MERGE
        try:
            with self.engine.begin() as conn:
                conn.execute(text(merge_query))
            self.message += f"Данные успешно вставлены/обновлены в {self.table_name}.\n"
        except Exception as e:
            self.error_count += 1
            raise ValueError(f"Ошибка при MERGE: {e}")

        # Подсчёт "после"
        with self.engine.connect() as conn:
            after_count = conn.execute(text(q)).scalar()
            self.row_counts["after_processing"] = after_count
            self.message += f"Количество строк после обработки: {after_count}\n"
        # Обновляем счётчики
        self.added_count += self.row_counts["to_insert"]
        self.updated_count += self.row_counts["to_update"]

    # =========================================================================
    # Вспомогательные методы (из старого класса, немного доработанные)
    # =========================================================================
    def _create_initial_data_import_record(self, source_name):
        """
        Создаём запись в data_loader_dataimport (если нужно).
        """
        sql_query = """
        INSERT INTO data_loader_dataimport
        (csv_file, date_added, added_count, updated_count, error_count,
         data_type_id, message)
        VALUES (
          :csv_file,
          NOW(),
          0, 0, 0,
          (SELECT id FROM data_loader_datatype WHERE name = :data_type_name),
          :message
        )
        RETURNING id
        """
        with self.engine.begin() as connection:
            result = connection.execute(
                text(sql_query),
                {
                    'csv_file': source_name[:100],
                    'data_type_name': self.data_type_name,
                    'message': 'Начало загрузки.'
                }
            )
            self.import_record_id = result.fetchone()[0]

    def _update_data_import_record(self):
        """
        Обновляем запись в data_loader_dataimport (если нужно).
        """
        if not self.import_record_id:
            return
        sql_update = """
        UPDATE data_loader_dataimport
        SET added_count = :added_count,
            updated_count = :updated_count,
            error_count = :error_count,
            message = :message
        WHERE id = :import_record_id
        """
        with self.engine.begin() as connection:
            connection.execute(text(sql_update), {
                'added_count': self.added_count,
                'updated_count': self.updated_count,
                'error_count': self.error_count,
                'message': self.message,
                'import_record_id': self.import_record_id
            })

    def _create_index(self, table_name: str):
        """
        Создаёт индекс по self.columns_for_update, если не существует.
        """
        index_name = f"idx_{table_name}_update"
        create_index_query = f"""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 
                FROM pg_indexes 
                WHERE schemaname = 'public' 
                  AND tablename = '{table_name}' 
                  AND indexname = '{index_name}'
            ) THEN
                CREATE INDEX {index_name}
                ON {table_name} ({', '.join(self.columns_for_update)});
            END IF;
        END $$;
        """
        with self.engine.connect() as conn:
            conn.execute(text(create_index_query))

    def _get_missing_columns(self):
        """
        Выясняет, какие столбцы есть в основной таблице, но нет во временной.
        """
        with self.engine.connect() as conn:
            main_cols_q = f"SELECT column_name FROM information_schema.columns WHERE table_name = '{self.table_name}'"
            main_cols = [r[0] for r in conn.execute(text(main_cols_q)).fetchall()]

            temp_cols_q = f"SELECT column_name FROM information_schema.columns WHERE table_name = '{self.table_name_temp}'"
            temp_cols = [r[0] for r in conn.execute(text(temp_cols_q)).fetchall()]

        missing = [c for c in main_cols if (c not in temp_cols and c != 'id')]
        return missing

    def _build_merge_query(self, missing_columns):
        """
        Генерируем запрос MERGE:
        INSERT INTO table_name (...)
        SELECT ...
        FROM table_name_temp
        ON CONFLICT (columns_for_update)
        DO UPDATE SET ...
        """
        # Все столбцы, которые вставляем
        insert_cols = list(self.column_mapping.values()) + missing_columns
        insert_cols_sql = ", ".join(insert_cols)

        # Часть SELECT
        select_cols_sql = ", ".join(self.column_mapping.values())
        if missing_columns:
            missing_sql = ", ".join([f"'-' AS {c}" for c in missing_columns])
            select_all_for_insert = f"{select_cols_sql}, {missing_sql}"
        else:
            select_all_for_insert = select_cols_sql

        # ON CONFLICT
        conflict_sql = ", ".join(self.columns_for_update)

        # DO UPDATE
        update_parts = []
        for col in self.column_mapping.values():
            if col not in self.columns_for_update:
                update_parts.append(f"{col} = EXCLUDED.{col}")
        for col in missing_columns:
            update_parts.append(f"{col} = COALESCE(EXCLUDED.{col}, '-')")

        update_sql = ", ".join(update_parts)

        merge_query = f"""
        INSERT INTO {self.table_name} ({insert_cols_sql})
        SELECT {select_all_for_insert}
        FROM {self.table_name_temp}
        ON CONFLICT ({conflict_sql})
        DO UPDATE SET {update_sql};
        """
        # Удалим лишние переносы строк
        merge_query = " ".join(merge_query.split())
        return merge_query


class CsvDataLoader(BaseDataLoader):
    """
    Наследник BaseDataLoader, где метод extract()
    читает CSV-файл из локального пути (source_name).
    """

    def extract(self, source_name) -> pd.DataFrame:
        if self.file_format.lower() == 'csv':
            df = pd.read_csv(
                source_name,
                sep=self.sep,
                dtype=self.dtype,
                encoding=self.encoding,
                na_values="-",
                low_memory=False
            )
            # Убираем Unnamed-столбцы, если есть
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            return df
        elif self.file_format.lower() == 'excel':
            return pd.read_excel(source_name)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {self.file_format}")


class SeleniumDataLoader(BaseDataLoader):
    """
    Наследник, в котором extract() сначала вызывает selenium_oms,
    а потом читает скачанный файл как CSV.
    """

    def __init__(self, engine, table_name, table_name_temp,
                 data_type_name, column_mapping, column_check, columns_for_update,
                 username, password, start_date, end_date, start_date_treatment,
                 file_format='csv', sep=';', dtype=str, encoding='utf-8',
                 clear_all_rows=False):
        super().__init__(
            engine=engine,
            table_name=table_name,
            table_name_temp=table_name_temp,
            data_type_name=data_type_name,
            column_mapping=column_mapping,
            column_check=column_check,
            columns_for_update=columns_for_update,
            file_format=file_format,
            sep=sep,
            dtype=dtype,
            encoding=encoding,
            clear_all_rows=clear_all_rows
        )
        # Данные для selenium
        self.username = username
        self.password = password
        self.start_date = start_date
        self.end_date = end_date
        self.start_date_treatment = start_date_treatment

    def extract(self, source_name) -> pd.DataFrame:
        """
        1) Вызываем selenium_oms, получаем success, file_path
        2) Если success, читаем CSV-файл
        3) Возвращаем DataFrame
        """
        success, downloaded_path = selenium_oms(
            self.username,
            self.password,
            self.start_date,
            self.end_date,
            self.start_date_treatment
        )
        logger.info("Success: %s, Downloaded path: %s", success, downloaded_path)

        if not success or not downloaded_path:
            raise ValueError("Selenium не смог скачать файл / путь пуст.")

        # Теперь читаем CSV/Excel по логике, аналогичной CsvDataLoader
        if self.file_format.lower() == 'csv':
            df = pd.read_csv(
                downloaded_path,
                sep=self.sep,
                dtype=self.dtype,
                encoding=self.encoding,
                na_values="-",
                low_memory=False
            )
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            return df
        elif self.file_format.lower() == 'excel':
            return pd.read_excel(downloaded_path)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {self.file_format}")


class FirebirdDataLoader(BaseDataLoader):
    """
    Загрузчик данных из Firebird.
    Использует подключение к базе Firebird для извлечения данных и загрузки в PostgreSQL.
    """

    def __init__(self, engine, table_name, table_name_temp, data_type_name, column_mapping, column_check,
                 columns_for_update,
                 firebird_dsn, firebird_user, firebird_password, firebird_charset='WIN1251', firebird_port=3050,
                 file_format='db', sep=';', dtype=str, encoding='utf-8', clear_all_rows=False):
        super().__init__(engine, table_name, table_name_temp, data_type_name, column_mapping, column_check,
                         columns_for_update,
                         file_format, sep, dtype, encoding, clear_all_rows)
        # Firebird-specific connection details
        self.firebird_dsn = firebird_dsn
        self.firebird_user = firebird_user
        self.firebird_password = firebird_password
        self.firebird_charset = firebird_charset
        self.firebird_port = firebird_port

    def extract(self, query: str) -> pd.DataFrame:
        """
        Метод для извлечения данных из Firebird.
        Выполняет SQL-запрос и преобразует результат в DataFrame.
        :param query: SQL-запрос для извлечения данных
        :return: DataFrame с результатами запроса
        """
        try:
            # Подключаемся к базе Firebird
            conn = fdb.connect(
                dsn=self.firebird_dsn,
                user=self.firebird_user,
                password=self.firebird_password,
                charset=self.firebird_charset,
                port=self.firebird_port
            )
            cursor = conn.cursor()

            # Выполняем запрос
            cursor.execute(query)
            data = cursor.fetchall()

            # Получаем имена столбцов из курсора
            columns = [desc[0] for desc in cursor.description]

            # Закрываем соединение
            conn.close()

            # Преобразуем результаты в DataFrame
            df = pd.DataFrame(data, columns=columns)
            return df

        except Exception as e:
            raise ValueError(f"Ошибка при подключении к Firebird или выполнении запроса: {e}")
