import json
from datetime import date
from dagster import asset, Field, String, OpExecutionContext, AssetIn
from config.settings import ORGANIZATIONS
from mosaic_conductor.etl.common.connect_db import connect_to_db


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
      1. Загружает маппинг из mapping.json, переименовывает столбцы согласно mapping_fields.
      2. Проверяет наличие обязательных столбцов.
      3. Ограничивает DataFrame только ожидаемыми столбцами.
      4. Если в mapping.json задано новое поле "check_fields", удаляет строки, в которых
         отсутствуют значения в указанных столбцах.
      5. Заполняет отсутствующие столбцы из БД дефолтным значением "-".
      6. Если данные талонов (is_talon=True или table_name в талонных таблицах),
         то гарантированно добавляет столбец is_complex с булевым значением,
         а затем, на основе группировки по (talon, source), для групп с более чем одной записью
         устанавливает is_complex = True.
      7. Если обрабатываются талоны, дополнительно вычисляются report_year и report_month.
      8. Возвращает либо единый DataFrame, либо словарь с ветками "normal" и "complex".
    """
    config = context.op_config
    mapping_file = config["mapping_file"]
    table_name = config["table_name"]

    df = kvazar_extract.get("data")
    if df is None:
        context.log.info("⚠️ Нет данных для трансформации!")
        raise ValueError("❌ Нет данных для трансформации.")

    # Загружаем маппинг и переименовываем столбцы
    with open(mapping_file, "r", encoding="utf-8") as f:
        mappings = json.load(f)
    table_config = mappings.get("tables", {}).get(table_name, {})
    column_mapping = table_config.get("mapping_fields", {})

    expected_original_cols = list(column_mapping.keys())
    actual_cols = list(df.columns)

    # Проверка обязательных столбцов в исходном CSV
    missing_in_csv = set(expected_original_cols) - set(actual_cols)
    if missing_in_csv:
        context.log.info(f"❌ Отсутствуют следующие столбцы в CSV: {missing_in_csv}")
        raise KeyError(f"Отсутствуют обязательные столбцы в CSV: {missing_in_csv}")
    extra_in_csv = set(actual_cols) - set(expected_original_cols)
    if extra_in_csv:
        context.log.info(f"⚠️ Лишние столбцы в CSV: {extra_in_csv}. Они будут проигнорированы.")

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

    # ФИЛЬТРАЦИЯ: если в mapping задано поле "check_fields", удаляем строки,
    # где в указанных столбцах отсутствуют значения.
    check_fields = table_config.get("check_fields", [])
    if check_fields:
        original_len = len(df)
        # Здесь предполагается, что в check_fields указаны именно имена, после переименования (new names)
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

    # очистка датафрейма
    df = df.replace('`', '', regex=True)

    # Если обрабатываются талоны, гарантируем заполнение столбца is_complex булевым значением.
    if config.get("is_talon", False) or table_name in ["load_data_talons", "load_data_complex_talons"]:
        context.log.info("ℹ️ Обработка данных талонов – гарантируем наличие столбца is_complex как boolean.")
        df["is_complex"] = False

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

        df['report_year'] = df.apply(lambda row: compute_report_year(row['report_period'], row['treatment_end']),
                                     axis=1)
        df['report_month'] = df.apply(lambda row: compute_report_month(row['report_period'], row['treatment_end']),
                                      axis=1)

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
