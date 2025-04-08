import os
import datetime

# Убедитесь, что переменная DJANGO_SETTINGS_MODULE установлена
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from dagster import op, OpExecutionContext, In
from django.db import transaction
from apps.personnel.models import Person, DoctorRecord, Profile, Specialty
from apps.load_data.models import Doctor  # сырые данные врачей (поля даты как текст)
# Импортируем модели для сопоставления отделений
from apps.organization.models import OMSDepartment, MiskauzDepartment


@op(
    ins={"load_result": In()},  # op ожидает вход load_result для зависимости от успешного выполнения kvazar_load
    config_schema={}
)
def update_personnel_op(context: OpExecutionContext, load_result):
    """
    Обновление или создание записей в моделях Person и DoctorRecord на основе сырых данных из модели Doctor.

    Логика:
      - Для каждого врача из таблицы load_data_doctor (данные как текст в формате DD-MM-YYYY)
        производится поиск по СНИЛС.
      - Если Person с заданным СНИЛС не существует, создаётся новая запись с преобразованием даты рождения.
      - Если запись существует, обновляются данные.
      - Для DoctorRecord выполняется get_or_create по Person и doctor_code,
        при этом поля start_date и end_date преобразуются из строкового значения.
      - Дополнительно:
          * Поля profile и specialty обновляются на основе doctor.medical_profile_code и doctor.specialty_code.
            Из строки извлекается первый элемент (код) и производится поиск соответствующего объекта.
          * Поле department обновляется. По значению doctor.department (название отделения) ищется
            сначала в OMSDepartment, затем в MiskauzDepartment. Если находится совпадение,
            извлекается связанное поле department (FK на модель Department) и записывается в DoctorRecord.
            Если отделение не найдено, выводится информационное сообщение, а поле department остается пустым.

    Входной параметр load_result используется для создания зависимости:
    этот op запускается только после успешного выполнения этапа kvazar_load.
    """
    context.log.info("Начало синхронизации данных: обновление Person и DoctorRecord.")
    updated_persons = 0
    updated_records = 0

    with transaction.atomic():
        doctor_qs = Doctor.objects.all()
        for doctor in doctor_qs:
            snils = doctor.snils

            # Преобразуем дату рождения из строки формата DD-MM-YYYY в объект date.
            birth_date = doctor.birth_date
            if isinstance(birth_date, str):
                try:
                    birth_date = datetime.datetime.strptime(birth_date, "%d-%m-%Y").date()
                except ValueError:
                    context.log.error(f"Неверный формат даты рождения {birth_date} для врача с СНИЛС {snils}")
                    continue

            # Получаем или создаём запись Person с корректной датой рождения
            person, created = Person.objects.get_or_create(
                snils=snils,
                defaults={
                    "last_name": doctor.last_name,
                    "first_name": doctor.first_name,
                    "patronymic": doctor.middle_name,
                    "date_of_birth": birth_date,
                    "gender": doctor.gender,
                }
            )
            if not created:
                person.last_name = doctor.last_name
                person.first_name = doctor.first_name
                person.patronymic = doctor.middle_name
                person.date_of_birth = birth_date
                person.gender = doctor.gender
                person.save()
                updated_persons += 1

            # Преобразуем start_date
            start_date = doctor.start_date
            if isinstance(start_date, str):
                try:
                    start_date = datetime.datetime.strptime(start_date, "%d-%m-%Y").date()
                except ValueError:
                    context.log.error(f"Неверный формат start_date {start_date} для врача с СНИЛС {snils}")
                    start_date = None

            # Преобразуем end_date
            end_date = doctor.end_date
            if isinstance(end_date, str):
                try:
                    end_date = datetime.datetime.strptime(end_date, "%d-%m-%Y").date()
                except ValueError:
                    context.log.error(f"Неверный формат end_date {end_date} для врача с СНИЛС {snils}")
                    end_date = None

            # Получаем или создаём запись DoctorRecord с преобразованными датами
            record, rec_created = DoctorRecord.objects.get_or_create(
                person=person,
                doctor_code=doctor.doctor_code,
                defaults={
                    "start_date": start_date,
                    "end_date": end_date,
                    "structural_unit": doctor.department,  # можно оставить для справки
                }
            )
            if not rec_created:
                record.start_date = start_date
                record.end_date = end_date
                record.structural_unit = doctor.department

            # Обновляем профиль
            if doctor.medical_profile_code:
                parts = doctor.medical_profile_code.split(maxsplit=1)
                profile_code = parts[0]
                try:
                    profile = Profile.objects.get(code=profile_code)
                    record.profile = profile
                    context.log.info(f"Заполнен профиль '{profile}' для врача с СНИЛС {snils}.")
                except Profile.DoesNotExist:
                    record.profile = None
                    context.log.info(
                        f"Профиль с кодом {profile_code} не найден для врача с СНИЛС {snils}. Поле profile оставлено пустым.")
            else:
                context.log.info(f"Медицинский профиль отсутствует для врача с СНИЛС {snils}.")

            # Обновляем специальность
            if doctor.specialty_code:
                parts = doctor.specialty_code.split(maxsplit=1)
                specialty_code = parts[0]
                try:
                    specialty = Specialty.objects.get(code=specialty_code)
                    record.specialty = specialty
                    context.log.info(f"Заполнена специальность '{specialty}' для врача с СНИЛС {snils}.")
                except Specialty.DoesNotExist:
                    record.specialty = None
                    context.log.info(
                        f"Специальность с кодом {specialty_code} не найдена для врача с СНИЛС {snils}. Поле specialty оставлено пустым.")
            else:
                context.log.info(f"Специальность отсутствует для врача с СНИЛС {snils}.")

            # Обновляем отделение.
            # Ищем в OMSDepartment по имени (без учёта регистра)
            matched_department = None
            if doctor.department:
                oms_dep = OMSDepartment.objects.filter(name__iexact=doctor.department).first()
                if oms_dep:
                    matched_department = oms_dep.department  # связанный объект Department
                else:
                    misk_dep = MiskauzDepartment.objects.filter(name__iexact=doctor.department).first()
                    if misk_dep:
                        matched_department = misk_dep.department

            if matched_department:
                record.department = matched_department
                context.log.info(f"Отделение для врача с СНИЛС {snils} установлено: {matched_department}.")
            else:
                record.department = None
                context.log.info(
                    f"Отделение для врача с СНИЛС {snils} не найдено среди OMSDepartment и MiskauzDepartment. Поле department оставлено пустым.")

            record.save()
            updated_records += 1

    context.log.info(
        f"Синхронизация завершена: обновлено {updated_persons} записей Person, {updated_records} записей DoctorRecord.")
    return {"updated_persons": updated_persons, "updated_records": updated_records}
