import datetime
import pandas as pd
from sqlalchemy import create_engine, text
from config.settings import DATABASES

# ------------------------------------------------------------------------------
# Настройки
# ------------------------------------------------------------------------------
FILE_PATH = r'C:\Users\frdro\Downloads\Telegram Desktop\journal_20241004(2).csv'

# Названия таблиц в БД
TABLE_NAME = "data_loader_omsdata"
TABLE_NAME_TEMP = "temp_oms_data"

# Настройки для чтения CSV
CSV_SEP = ';'
CSV_DTYPE = str
CSV_ENCODING = 'utf-8'

# Ключевой столбец, по которому проверяем наличие обязательных данных
COLUMN_CHECK = "patient"

# Список столбцов, по которым происходит поиск совпадений (update/insert)
COLUMNS_FOR_UPDATE = ['talon', 'source']

# Сопоставление названий столбцов CSV и полей в БД
COLUMN_MAPPING = {
    "Талон": "talon",
    "Источник": "source",
    "Статус": "status",
    "Цель": "goal",
    "Пациент": "patient",
    "Дата рождения": "birth_date",
    "Пол": "gender",
    "Код СМО": "smo_code",
    "ЕНП": "enp",
    "Начало лечения": "treatment_start",
    "Окончание лечения": "treatment_end",
    "Врач": "doctor",
    "Посещения": "visits",
    "Посещения в МО": "mo_visits",
    "Посещения на Дому": "home_visits",
    "Диагноз основной (DS1)": "main_diagnosis",
    "Сопутствующий диагноз (DS2)": "additional_diagnosis",
    "Первоначальная дата ввода": "initial_input_date",
    "Дата последнего изменения": "last_change_date",
    "Сумма": "amount",
    "Санкции": "sanctions",
    "КСГ": "ksg",
    "Отчетный период выгрузки": "report_period",
}

# ------------------------------------------------------------------------------
# Подключение к базе данных PostgreSQL
# ------------------------------------------------------------------------------
postgres_settings = DATABASES['default']
engine = create_engine(
    f'postgresql://{postgres_settings["USER"]}:'
    f'{postgres_settings["PASSWORD"]}@{postgres_settings["HOST"]}:'
    f'{postgres_settings["PORT"]}/{postgres_settings["NAME"]}'
)

def run_etl_process():
    """
    Запуск ETL-процесса: Extract -> Transform -> Load.
    """
    # ------------------------------------------------------------------------------
    # Логирование времени
    # ------------------------------------------------------------------------------
    start_time = datetime.datetime.now()
    print(f"Начало процесса загрузки данных: {start_time}")

    # ------------------------------------------------------------------------------
    # EXTRACT (E) - Извлечение данных
    # ------------------------------------------------------------------------------
    df_raw = extract_data_from_csv(
        file_path=FILE_PATH,
        sep=CSV_SEP,
        dtype=CSV_DTYPE,
        encoding=CSV_ENCODING
    )

    # ------------------------------------------------------------------------------
    # TRANSFORM (T) - Преобразование данных
    # ------------------------------------------------------------------------------
    df_transformed = transform_data(
        df_raw=df_raw,
        column_mapping=COLUMN_MAPPING,
        column_check=COLUMN_CHECK,
        columns_for_update=COLUMNS_FOR_UPDATE
    )

    # ------------------------------------------------------------------------------
    # LOAD (L) - Загрузка данных в БД
    # ------------------------------------------------------------------------------
    load_data_to_db(
        df_transformed=df_transformed,
        engine=engine,
        table_name=TABLE_NAME,
        temp_table_name=TABLE_NAME_TEMP,
        column_mapping=COLUMN_MAPPING,
        columns_for_update=COLUMNS_FOR_UPDATE
    )

    end_time = datetime.datetime.now()
    print(f"Общее время выполнения: {end_time - start_time}")


# ==============================================================================
# Функции для ETL
# ==============================================================================
def extract_data_from_csv(file_path, sep, dtype, encoding):
    """
    Считывает данные из CSV-файла и возвращает DataFrame.
    """
    print("=== EXTRACT ===")
    print("Читаем CSV-файл...")

    try:
        df = pd.read_csv(file_path, sep=sep, dtype=dtype, encoding=encoding)
        print(f"Количество строк в файле: {len(df)}")
        print(f"Успешно прочитан файл: {file_path}")
    except Exception as e:
        print(f"Ошибка при чтении CSV: {e}")
        raise

    return df


def transform_data(df_raw, column_mapping, column_check, columns_for_update):
    """
    Преобразует DataFrame:
      - Переименование столбцов
      - Удаление пустых записей
      - Удаление дубликатов
      - Другие необходимые преобразования
    """
    print("=== TRANSFORM ===")

    # Выбираем и переименовываем необходимые столбцы
    df = df_raw[list(column_mapping.keys())].rename(columns=column_mapping)

    # Удаляем строки, где нет ключевого поля (patient, и т. д.)
    df.dropna(subset=[column_check], inplace=True)

    # Заполняем пропущенные значения символом '-'
    df.fillna('-', inplace=True)

    # Дополнительная замена символов
    df.replace('`', '', regex=True, inplace=True)
    df.replace('\u00A0', ' ', regex=True, inplace=True)

    # Приводим все к строковому формату на всякий случай
    df = df.astype(str)

    # Удаляем дубликаты по столбцам для обновления
    initial_length = len(df)
    df.drop_duplicates(subset=columns_for_update, inplace=True)

    print(f"Итоговое количество строк после трансформации: {len(df)}")
    return df


def load_data_to_db(df_transformed, engine, table_name, temp_table_name, column_mapping, columns_for_update):
    """
    Загружает данные во временную таблицу, затем мёрджит (insert/update) в основную.
    Выводит статистику по изменениям в базе.
    """
    print("=== LOAD ===")

    # Счётчики строк
    row_counts = {}

    # Подсчёт строк в основной таблице до обработки
    with engine.connect() as connection:
        initial_count_query = f"SELECT COUNT(*) FROM {table_name};"
        row_counts["before_processing"] = connection.execute(text(initial_count_query)).scalar()
    print(f"Количество строк в таблице {table_name} до обработки: {row_counts['before_processing']}")

    # Подсчёт строк в преобразованном DataFrame
    row_counts["after_reading_csv"] = len(df_transformed)
    print(f"Количество строк в фрейме данных после чтения и обработки: {row_counts['after_reading_csv']}")

    # Проверка существования временной таблицы, её очистка (или создание)
    with engine.connect() as connection:
        exists_temp = connection.execute(
            text(
                f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{temp_table_name}')"
            )
        ).scalar()

        if exists_temp:
            connection.execute(text(f"TRUNCATE TABLE {temp_table_name};"))
            print(f"Таблица {temp_table_name} очищена.")
        else:
            print(f"Таблица {temp_table_name} отсутствует, будет создана автоматически при загрузке данных.")

    # Запись DataFrame во временную таблицу
    df_transformed.to_sql(temp_table_name, engine, if_exists='replace', index=False)
    print(f"Данные загружены во временную таблицу {temp_table_name}.")

    # Создание индекса в основной и временной таблицах (для ускорения JOIN)
    create_index_in_db(engine, table_name, columns_for_update)
    create_index_in_db(engine, temp_table_name, columns_for_update)

    # Подсчёт строк для обновления и вставки
    with engine.connect() as connection:
        rows_to_update_query = f"""
            SELECT COUNT(*)
            FROM {temp_table_name} AS temp
            INNER JOIN {table_name} AS target
              ON { ' AND '.join([f'temp.{col} = target.{col}' for col in columns_for_update]) }
        """
        row_counts["to_update"] = connection.execute(text(rows_to_update_query)).scalar()

        rows_to_insert_query = f"""
            SELECT COUNT(*)
            FROM {temp_table_name} AS temp
            LEFT JOIN {table_name} AS target
              ON { ' AND '.join([f'temp.{col} = target.{col}' for col in columns_for_update]) }
            WHERE target.{columns_for_update[0]} IS NULL
        """
        row_counts["to_insert"] = connection.execute(text(rows_to_insert_query)).scalar()

    print(f"Количество строк для обновления: {row_counts['to_update']}")
    print(f"Количество строк для добавления: {row_counts['to_insert']}")

    # Получение недостающих столбцов (если в основной таблице есть поля, которых нет во временной)
    missing_columns = get_missing_columns(engine, table_name, temp_table_name)

    # Формирование MERGE-запроса (PostgreSQL-style через ON CONFLICT)
    merge_query = build_merge_query(
        table_name=table_name,
        temp_table_name=temp_table_name,
        column_mapping=column_mapping,
        columns_for_update=columns_for_update,
        missing_columns=missing_columns
    )

    # Выполнение запроса
    try:
        with engine.begin() as connection:
            connection.execute(text(merge_query))
        print(f"Данные успешно вставлены/обновлены в таблице {table_name}.")
    except Exception as e:
        print(f"Ошибка при выполнении merge-запроса: {e}")

    # Подсчёт строк после обработки
    with engine.connect() as connection:
        final_count_query = f"SELECT COUNT(*) FROM {table_name};"
        row_counts["after_processing"] = connection.execute(text(final_count_query)).scalar()

    print(f"Количество строк в {table_name} после загрузки и обновления: {row_counts['after_processing']}")

    # Итоговая статистика
    print("=== Итоговые показатели обработки ===")
    print(f"1. Количество строк в {table_name} до обработки: {row_counts['before_processing']}")
    print(f"2. Количество строк в DataFrame после чтения и обработки: {row_counts['after_reading_csv']}")
    print(f"3. Количество строк обновленных в {table_name}: {row_counts['to_update']}")
    print(f"4. Количество строк добавленных в {table_name}: {row_counts['to_insert']}")
    print(f"5. Количество строк в {table_name} после загрузки и обновления: {row_counts['after_processing']}")


def create_index_in_db(engine, table_name, columns_for_update):
    """
    Создаёт индекс в таблице `table_name` по столбцам из `columns_for_update`,
    если он ещё не существует.
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
            ON {table_name} ({', '.join(columns_for_update)});
        END IF;
    END $$;
    """

    with engine.connect() as connection:
        connection.execute(text(create_index_query))
    print(f"Индекс '{index_name}' проверен/создан для таблицы '{table_name}'.")


def get_missing_columns(engine, main_table, temp_table):
    """
    Возвращает список столбцов, присутствующих в основной таблице, но отсутствующих во временной.
    """
    with engine.connect() as connection:
        table_columns_query = f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{main_table}'
        """
        main_columns = [row[0] for row in connection.execute(text(table_columns_query)).fetchall()]

        temp_table_columns_query = f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{temp_table}'
        """
        tmp_columns = [row[0] for row in connection.execute(text(temp_table_columns_query)).fetchall()]

    # Исключаем поле 'id', если оно автогенерируется
    missing_cols = [col for col in main_columns if col not in tmp_columns and col != 'id']
    return missing_cols


def build_merge_query(table_name, temp_table_name, column_mapping, columns_for_update, missing_columns):
    """
    Строит SQL-запрос для вставки/обновления (MERGE-подобный сценарий) через ON CONFLICT (PostgreSQL).
    """
    # Поля, которые нужно вставлять (все из COLUMN_MAPPING + missing_columns)
    insert_columns = list(column_mapping.values()) + missing_columns

    # Формирование части INSERT
    insert_columns_sql = ", ".join(insert_columns)
    select_columns_sql = ", ".join(column_mapping.values())
    # Для недостающих столбцов добавляем вставку значения '-'
    select_missing_cols_sql = ", ".join([f"'-' AS {col}" for col in missing_columns])
    if select_missing_cols_sql:
        select_all_for_insert = f"{select_columns_sql}, {select_missing_cols_sql}"
    else:
        select_all_for_insert = f"{select_columns_sql}"

    # Формирование части ON CONFLICT
    conflict_cols_sql = ", ".join(columns_for_update)

    # Формирование части DO UPDATE
    # - все поля из column_mapping, кроме тех, что в columns_for_update
    update_set_cols = []
    for col in column_mapping.values():
        if col not in columns_for_update:
            update_set_cols.append(f"{col} = EXCLUDED.{col}")

    # - все missing_columns тоже вставляются, но если вдруг EXCLUDED пустое — ставим '-'
    for col in missing_columns:
        update_set_cols.append(f"{col} = COALESCE(EXCLUDED.{col}, '-')")

    update_set_sql = ", ".join(update_set_cols)

    merge_query = f"""
    INSERT INTO {table_name} ({insert_columns_sql})
    SELECT {select_all_for_insert}
    FROM {temp_table_name}
    ON CONFLICT ({conflict_cols_sql})
    DO UPDATE SET {update_set_sql};
    """

    # Удалим лишние переносы строк, чтобы избежать SyntaxError
    merge_query = " ".join(merge_query.split())
    return merge_query


# ------------------------------------------------------------------------------
# Точка входа
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    run_etl_process()
