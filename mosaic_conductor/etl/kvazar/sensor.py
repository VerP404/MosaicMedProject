import os
import time
import json
import fnmatch

from dagster import sensor, RunRequest, SkipReason

from config.settings import ORGANIZATIONS
from mosaic_conductor.etl.kvazar import kvazar_job_eln, kvazar_job_emd, kvazar_job_recipes, kvazar_job_death, \
    kvazar_job_reference, iszl_job_dn, wo_old_job_talon, wo_old_job_doctors, wo_job_talon

MIN_FILE_AGE_SECONDS = 60


def _load_state(context) -> dict:
    """Загружаем из cursor словарь вида {filename: run_key}."""
    if context.cursor:
        return json.loads(context.cursor)
    return {}


def _save_state(context, state: dict):
    """Сохраняем словарь {filename: run_key} в cursor сенсора."""
    context.update_cursor(json.dumps(state, ensure_ascii=False))


def create_sensor(job, sensor_name, description, data_folder, table_name, mapping_file):
    @sensor(job=job, name=sensor_name, description=description)
    def _sensor(context):
        sensor_state = _load_state(context)  # {filename: run_key}

        # Проверяем наличие mapping.json
        if not os.path.exists(mapping_file):
            context.log.info(f"❌ Файл маппинга {mapping_file} не найден.")
            yield SkipReason("Mapping file not found.")
            return

        with open(mapping_file, "r", encoding="utf-8") as f:
            mapping = json.load(f)
        table_config = mapping.get("tables", {}).get(table_name)
        if not table_config:
            context.log.info(f"❌ Настройки для таблицы '{table_name}' не найдены в {mapping_file}.")
            yield SkipReason("Mapping config for table not found.")
            return

        # Проверяем наличие папки с данными
        if not os.path.exists(data_folder):
            context.log.info(f"❌ Папка {data_folder} не найдена.")
            yield SkipReason("Data folder not found.")
            return

        files = os.listdir(data_folder)
        if not files:
            context.log.info(f"📂 Папка {data_folder} пуста, пропускаем тик.")
            yield SkipReason("Нет файлов в папке.")
            return

        now = time.time()
        valid_files = []
        invalid_files = []

        # Получаем шаблон файлов
        file_pattern = table_config.get("file", {}).get("file_pattern", "")
        file_format = table_config.get("file", {}).get("file_format", "")
        valid_pattern = f"{file_pattern}.{file_format}"

        for file in files:
            file_path = os.path.join(data_folder, file)
            if fnmatch.fnmatch(file, valid_pattern):
                mod_time = os.path.getmtime(file_path)
                age = now - mod_time
                if age >= MIN_FILE_AGE_SECONDS:
                    valid_files.append(file)
                else:
                    context.log.info(f"Файл {file} ещё не полностью загружен (возраст {age:.0f} сек.).")
            else:
                invalid_files.append(file)

        for file in invalid_files:
            file_path = os.path.join(data_folder, file)
            try:
                os.remove(file_path)
                context.log.info(f"Удалён невалидный файл: {file_path}")
            except Exception as e:
                context.log.error(f"Не удалось удалить файл {file_path}: {e}")

        if not valid_files:
            context.log.info("Нет валидных файлов для запуска обновления.")
            yield SkipReason("Нет валидных файлов.")
            return

        for file in valid_files:
            existing_run_key = sensor_state.get(file)

            if existing_run_key:
                runs = context.instance.get_runs()
                matching_run = next(
                    (r for r in runs if r.tags.get("dagster/run_key") == existing_run_key), None
                )

                if matching_run:
                    if not matching_run.is_finished:
                        context.log.info(f"Файл {file} уже обрабатывается, пропускаем.")
                        continue
                    elif matching_run.is_success:
                        try:
                            os.remove(os.path.join(data_folder, file))
                            context.log.info(f"Файл {file} успешно обработан и удалён.")
                        except Exception as e:
                            context.log.error(f"Ошибка удаления файла {file}: {e}")
                        del sensor_state[file]
                        continue
                    elif matching_run.is_failure:
                        context.log.warning(f"Файл {file} завершился ошибкой. Перезапускаем.")
                        del sensor_state[file]

            if file not in sensor_state:
                new_run_key = f"{file}-{int(time.time())}"
                context.log.info(f"Запуск процесса обновления для файла {file} c run_key={new_run_key}.")

                # ✅ Добавляем ВСЕ блоки в конфиг:
                run_config = {
                    "ops": {
                        "kvazar_db_check": {
                            "config": {
                                "organization": ORGANIZATIONS,  # можно заменить на реальный список
                                "tables": [table_name]
                            }
                        },
                        "kvazar_extract": {
                            "config": {
                                "data_folder": data_folder,
                                "mapping_file": mapping_file,
                                "table_name": table_name,
                            }
                        },
                        "kvazar_transform": {
                            "config": {
                                "mapping_file": mapping_file,
                                "table_name": table_name
                            }
                        },
                        "kvazar_load": {
                            "config": {
                                "table_name": table_name,
                                "data_folder": data_folder,
                                "mapping_file": mapping_file
                            }
                        }
                    }
                }

                yield RunRequest(run_key=new_run_key, run_config=run_config)
                sensor_state[file] = new_run_key

        _save_state(context, sensor_state)

    return _sensor


# ✅ Создание сенсоров
kvazar_sensor_eln = create_sensor(
    kvazar_job_eln,
    "kvazar_sensor_eln",
    "Квазар: Листки нетрудоспособности",
    "mosaic_conductor/etl/data/kvazar/eln",
    "load_data_sick_leave_sheets",
    "mosaic_conductor/etl/config/mapping.json"
)

kvazar_sensor_emd = create_sensor(
    kvazar_job_emd,
    "kvazar_sensor_emd",
    "Квазар: Журнал ЭМД",
    "mosaic_conductor/etl/data/kvazar/emd",
    "load_data_emd",
    "mosaic_conductor/etl/config/mapping.json"
)

kvazar_sensor_recipes = create_sensor(
    kvazar_job_recipes,
    "kvazar_sensor_recipes",
    "Квазар: Выписка рецептов",
    "mosaic_conductor/etl/data/kvazar/recipe",
    "load_data_recipes",
    "mosaic_conductor/etl/config/mapping.json"
)

kvazar_sensor_death = create_sensor(
    kvazar_job_death,
    "kvazar_sensor_death",
    "Квазар: Смертность",
    "mosaic_conductor/etl/data/kvazar/death",
    "load_data_death",
    "mosaic_conductor/etl/config/mapping.json"
)

kvazar_sensor_reference = create_sensor(
    kvazar_job_reference,
    "kvazar_sensor_reference",
    "Квазар: Справки",
    "mosaic_conductor/etl/data/kvazar/reference",
    "load_data_reference",
    "mosaic_conductor/etl/config/mapping.json"
)

iszl_sensor_dn = create_sensor(
    iszl_job_dn,
    "iszl_sensor_dn",
    "ИСЗЛ: Население",
    "mosaic_conductor/etl/data/iszl/dn",
    "load_data_dispansery_iszl",
    "mosaic_conductor/etl/config/mapping.json"
)

wo_old_sensor_talon = create_sensor(
    wo_old_job_talon,
    "wo_old_sensor_talon",
    "ОМС: Талоны. Старая версия",
    "mosaic_conductor/etl/data/weboms/talon/old",
    "data_loader_omsdata",
    "mosaic_conductor/etl/config/oms_old_mapping.json"
)

wo_old_sensor_doctors = create_sensor(
    wo_old_job_doctors,
    "wo_old_sensor_doctors",
    "ОМС: Врачи. Старая версия",
    "mosaic_conductor/etl/data/weboms/doctor",
    "data_loader_doctordata",
    "mosaic_conductor/etl/config/oms_old_mapping.json"
)
wo_sensor_talon = create_sensor(
    wo_job_talon,
    "wo_sensor_talon",
    "ОМС: Талоны.",
    "mosaic_conductor/etl/data/weboms/talon/new",
    "load_data_talons",
    "mosaic_conductor/etl/config/oms_mapping.json"
)
kvazar_sensors = [
    kvazar_sensor_eln,
    kvazar_sensor_emd,
    kvazar_sensor_recipes,
    kvazar_sensor_death,
    kvazar_sensor_reference,
    iszl_sensor_dn,
    wo_old_sensor_talon,
    wo_old_sensor_doctors,
    wo_sensor_talon,

]
