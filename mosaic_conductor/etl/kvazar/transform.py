import json
from datetime import date
from collections import Counter
from dagster import asset, Field, String, OpExecutionContext, AssetIn
from config.settings import ORGANIZATIONS
from mosaic_conductor.etl.common.connect_db import connect_to_db

# Словарь (набор) таблиц, для которых проверка наличия обязательных столбцов будет пропущена.
SKIP_CHECK_TABLES = {"load_data_journal_appeals"}  # добавьте сюда имена таблиц, для которых нужно пропускать проверку


def make_columns_unique(columns):
    """Возвращает список столбцов с уникальными именами (добавляет суффиксы при повторениях)."""
    counts = {}
    new_cols = []
    for col in columns:
        if col in counts:
            counts[col] += 1
            new_cols.append(f"{col}_{counts[col]}")
        else:
            counts[col] = 0
            new_cols.append(col)
    return new_cols


def normalize(col: str) -> str:
    """
    Удаляет автоматически добавленный суффикс вида _<число> из названия столбца.
    Например, 'Фамилия_1' -> 'Фамилия'
    """
    parts = col.split("_")
    if len(parts) > 1 and parts[-1].isdigit():
        return "_".join(parts[:-1])
    return col


@asset(
    config_schema={
        "mapping_file": Field(String),
        "table_name": Field(String),
        "is_talon": Field(bool, default_value=False)
    },
    ins={"kvazar_extract": AssetIn()}
)
def kvazar_transform(context: OpExecutionContext, kvazar_extract: dict) -> dict:
    """
    Трансформация данных:
      1. Загружает маппинг из mapping.json.
      2. Делает имена столбцов уникальными.
      3. Если таблица не указана в SKIP_CHECK_TABLES, проверяет наличие обязательных столбцов с учётом нормализации.
      4. Переименовывает столбцы согласно mapping_fields.
      5. Оставляет только ожидаемые столбцы.
      6. Если задано "check_fields" в маппинге, удаляет строки с пустыми значениями.
      7. Заполняет отсутствующие столбцы дефолтным значением "-".
      8. При обработке талонов вычисляет is_complex, report_year и report_month.
      9. Возвращает либо единый DataFrame, либо словарь с ветками "normal" и "complex".
    """
    config = context.op_config
    mapping_file = config["mapping_file"]
    table_name = config["table_name"]

    df = kvazar_extract.get("data")
    if df is None:
        context.log.info("⚠️ Нет данных для трансформации!")
        raise ValueError("❌ Нет данных для трансформации.")
    # Делаем имена столбцов уникальными
    df.columns = make_columns_unique(df.columns)
    actual_cols = list(df.columns)
    # Загружаем маппинг
    with open(mapping_file, "r", encoding="utf-8") as f:
        mappings = json.load(f)
    table_config = mappings.get("tables", {}).get(table_name, {})
    column_mapping = table_config.get("mapping_fields", {})

    # Список ожидаемых столбцов согласно маппингу (ключи)
    expected_original_cols = list(column_mapping.keys())

    # Если таблица не в SKIP_CHECK_TABLES, выполняем проверку обязательных столбцов.
    if table_name not in SKIP_CHECK_TABLES:
        # Группируем ожидаемые столбцы по нормализованному имени
        expected_counts = Counter(normalize(col) for col in expected_original_cols)
        actual_counts = Counter(normalize(col) for col in actual_cols)

        missing_in_csv = {key: expected_counts[key] - actual_counts.get(key, 0)
                          for key in expected_counts if actual_counts.get(key, 0) < expected_counts[key]}
        if missing_in_csv:
            context.log.info(f"❌ Отсутствуют следующие столбцы в CSV (нормализовано): {missing_in_csv}")
            raise KeyError(f"Отсутствуют обязательные столбцы в CSV: {missing_in_csv}")

        extra_in_csv = {normalize(col) for col in actual_cols} - {normalize(col) for col in expected_original_cols}
        if extra_in_csv:
            context.log.info(f"⚠️ Лишние столбцы (нормализованные) в CSV: {extra_in_csv}. Они будут проигнорированы.")
    else:
        context.log.info(f"Пропускаем проверку обязательных столбцов для таблицы {table_name}.")

    # Переименовываем столбцы согласно mapping_fields
    df = df.rename(columns=column_mapping)
    expected_cols = list(column_mapping.values())
    actual_transformed_cols = list(df.columns)
    missing_after_rename = set(expected_cols) - set(actual_transformed_cols)
    if missing_after_rename:
        context.log.info(f"❌ Отсутствуют после переименования: {missing_after_rename}")
        raise KeyError(f"Отсутствуют обязательные столбцы после переименования: {missing_after_rename}")
    extra_after_rename = set(actual_transformed_cols) - set(expected_cols)
    if extra_after_rename:
        context.log.info(f"⚠️ Лишние после переименования: {extra_after_rename}. Они будут проигнорированы.")
    df = df[expected_cols]
    # Фильтрация: если в mapping задано поле "check_fields", удаляем строки с пустыми значениями
    check_fields = table_config.get("check_fields", [])
    if check_fields:
        original_len = len(df)
        df = df.dropna(subset=check_fields)
        context.log.info(
            f"⚠️ Отфильтровано строк: {original_len - len(df)} (удалены строки с пустыми значениями в столбцах: {check_fields})"
        )
    else:
        context.log.info("Поле 'check_fields' не задано – пропускаем фильтрацию по пустым значениям.")

    # Заполнение отсутствующих столбцов из БД дефолтным значением "-"
    engine, conn = connect_to_db(organization=ORGANIZATIONS, context=context)
    sql = f"""
          SELECT column_name 
          FROM information_schema.columns 
          WHERE table_name = '{table_name}' 
            AND data_type = 'character varying';
        """
    with conn.cursor() as cursor:
        cursor.execute(sql)
        db_columns = [row[0] for row in cursor.fetchall()]
    conn.close()
    if not db_columns:
        context.log.info(f"❌ Не удалось получить список обязательных столбцов для таблицы {table_name}.")
        raise ValueError(f"❌ Нет обязательных столбцов для таблицы {table_name}.")
    for col in db_columns:
        if col not in df.columns:
            context.log.info(f"⚠️ Добавляем отсутствующий столбец '{col}' со значением '-' по умолчанию.")
            df[col] = "-"

    # Очистка DataFrame от лишних символов
    df = df.replace('`', '', regex=True)
    # Если обрабатываются талоны, вычисляем is_complex, report_year и report_month
    if config.get("is_talon", False) or table_name in ["load_data_talons", "load_data_complex_talons"]:
        context.log.info("ℹ️ Обработка данных талонов – гарантируем наличие столбца is_complex как boolean.")
        df["is_complex"] = False
        df.drop(columns=['report_year', 'report_month'], errors='ignore', inplace=True)

        def compute_report_year(report_period, treatment_end):
            return treatment_end[-4:] if report_period == '-' else report_period[-4:]

        def compute_report_month(report_period, treatment_end):
            current_date = date.today()
            if report_period == '-':
                if current_date.day <= 4:
                    month_from_treatment = int(treatment_end[3:5]) if len(treatment_end) >= 6 else current_date.month
                    return current_date.month if month_from_treatment == current_date.month else (
                        12 if current_date.month == 1 else current_date.month - 1)
                else:
                    return current_date.month
            else:
                month_mapping = {
                    'Января': 1, 'Февраля': 2, 'Марта': 3, 'Апреля': 4,
                    'Мая': 5, 'Июня': 6, 'Июля': 7, 'Августа': 8,
                    'Сентября': 9, 'Октября': 10, 'Ноября': 11, 'Декабря': 12
                }
                month_str = report_period.split()[0].strip()
                return month_mapping.get(month_str, None)

        years = [
            compute_report_year(rp, te)
            for rp, te in zip(df['report_period'], df['treatment_end'])
        ]
        months = [
            compute_report_month(rp, te)
            for rp, te in zip(df['report_period'], df['treatment_end'])
        ]

        df['report_year'] = years
        df['report_month'] = months

        grouped = df.groupby(["talon", "source"])
        for (talon, source), group in grouped:
            if len(group) > 1:
                df.loc[group.index, "is_complex"] = True
        df["is_complex"] = df["is_complex"].fillna(False).astype(bool)

        normal_df = df[df["is_complex"] == False].copy()
        complex_df = df[df["is_complex"] == True].copy()
        context.log.info(
            f"🔄 Трансформация завершена. Всего строк: {len(df)}. Нормальных: {len(normal_df)}, Комплексных: {len(complex_df)}."
        )
        return {
            "normal": {"table_name": "load_data_talons", "data": normal_df},
            "complex": {"table_name": "load_data_complex_talons", "data": complex_df}
        }
    else:
        context.log.info(f"✅ Трансформация для {table_name} завершена. Всего строк: {len(df)}")
        return {"table_name": table_name, "data": df}
