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
from apps.organization.models import OMSDepartment, MiskauzDepartment


@op(
    ins={"load_result": In()},  # op ожидает вход load_result для зависимости от успешного выполнения kvazar_load
    config_schema={}
)
def update_personnel_op(context: OpExecutionContext, load_result):
    """
    Оптимизированная версия опа, которая:
      - Обновляет/создаёт записи Person и DoctorRecord на основе данных из модели Doctor.
      - Не выводит в лог никаких построчных сообщений о "успешных" действиях.
      - Все ошибки (не найден профиль, специальность, отделение) и общая статистика собираются
        в один список и выводятся одним вызовом логирования (одна запись лога).
      - Если поле end_date в данных содержит "-" или пустую строку, оно трактуется как отсутствие даты (None).
    """

    # Счётчики
    total_doctors = 0
    new_persons = 0
    updated_persons = 0
    set_departments = 0
    set_profiles = 0
    set_specialties = 0

    # Списки для ошибок
    profile_errors = []
    specialty_errors = []
    department_errors = []

    with transaction.atomic():
        doctor_qs = Doctor.objects.all()
        for doctor in doctor_qs:
            total_doctors += 1

            snils = doctor.snils

            # 1. Обработка даты рождения
            birth_date = None
            if isinstance(doctor.birth_date, str):
                try:
                    birth_date = datetime.datetime.strptime(doctor.birth_date, "%d-%m-%Y").date()
                except ValueError:
                    # Если формат даты рождения неверный - пропускаем
                    continue
            else:
                birth_date = doctor.birth_date

            # 2. Person get_or_create
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
            if created:
                new_persons += 1
            else:
                # Обновляем данные Person, если запись уже существовала
                person.last_name = doctor.last_name
                person.first_name = doctor.first_name
                person.patronymic = doctor.middle_name
                person.date_of_birth = birth_date
                person.gender = doctor.gender
                person.save()
                updated_persons += 1

            # 3. Преобразование дат начала и окончания работы
            start_date = None
            end_date = None

            # start_date
            if isinstance(doctor.start_date, str):
                try:
                    start_date = datetime.datetime.strptime(doctor.start_date, "%d-%m-%Y").date()
                except ValueError:
                    pass
            else:
                start_date = doctor.start_date

            # end_date
            if isinstance(doctor.end_date, str):
                # Если значение равно "-" или пустой строке, считаем что даты увольнения нет
                if doctor.end_date.strip() in {"-", ""}:
                    end_date = None
                else:
                    try:
                        end_date = datetime.datetime.strptime(doctor.end_date, "%d-%m-%Y").date()
                    except ValueError:
                        end_date = None
            else:
                end_date = doctor.end_date

            # 4. DoctorRecord get_or_create
            record, rec_created = DoctorRecord.objects.get_or_create(
                person=person,
                doctor_code=doctor.doctor_code,
                defaults={
                    "start_date": start_date,
                    "end_date": end_date,
                    "structural_unit": doctor.department,
                }
            )
            if not rec_created:
                record.start_date = start_date
                record.end_date = end_date
                record.structural_unit = doctor.department

            # 5. Обновляем профиль (только если указан doctor.medical_profile_code)
            if doctor.medical_profile_code:
                profile_code = doctor.medical_profile_code.split(maxsplit=1)[0]
                try:
                    profile = Profile.objects.get(code=profile_code)
                    record.profile = profile
                    set_profiles += 1
                except Profile.DoesNotExist:
                    profile_errors.append(
                        f"{person.last_name} {person.first_name} {person.patronymic}, "
                        f"СНИЛС: {snils}, КОД: {doctor.doctor_code}, "
                        f"Профиль не найден: {profile_code}"
                    )

            # 6. Обновляем специальность (только если указано doctor.specialty_code)
            if doctor.specialty_code:
                specialty_code = doctor.specialty_code.split(maxsplit=1)[0]
                try:
                    specialty = Specialty.objects.get(code=specialty_code)
                    record.specialty = specialty
                    set_specialties += 1
                except Specialty.DoesNotExist:
                    specialty_errors.append(
                        f"{person.last_name} {person.first_name} {person.patronymic}, "
                        f"СНИЛС: {snils}, КОД: {doctor.doctor_code}, "
                        f"Специальность не найдена: {specialty_code}"
                    )

            # 7. Обновляем отделение, только если оно не установлено (None)
            if record.department is None:
                matched_department = None
                if doctor.department:
                    oms_dep = OMSDepartment.objects.filter(name__iexact=doctor.department).first()
                    if oms_dep:
                        matched_department = oms_dep.department
                    else:
                        misk_dep = MiskauzDepartment.objects.filter(name__iexact=doctor.department).first()
                        if misk_dep:
                            matched_department = misk_dep.department

                if matched_department:
                    record.department = matched_department
                    set_departments += 1
                else:
                    department_errors.append(
                        f"{person.last_name} {person.first_name} {person.patronymic}, "
                        f"СНИЛС: {snils}, КОД: {doctor.doctor_code}, "
                        f"Отделение не найдено: '{doctor.department or ''}'"
                    )

            record.save()

    # -- Формируем единый отчёт (одна запись лога) --

    report_lines = []
    report_lines.append("=== РЕЗУЛЬТАТ СИНХРОНИЗАЦИИ ВРАЧЕЙ ===")
    report_lines.append(f"Всего обработано врачей: {total_doctors}")
    report_lines.append(f"Новых персон: {new_persons}")
    report_lines.append(f"Обновлено персон: {updated_persons}")
    report_lines.append(f"Установлено отделений: {set_departments}")
    report_lines.append(f"Установлено профилей: {set_profiles}")
    report_lines.append(f"Установлено специальностей: {set_specialties}")
    report_lines.append(f"Ошибок профилей: {len(profile_errors)}")
    report_lines.append(f"Ошибок специальностей: {len(specialty_errors)}")
    report_lines.append(f"Ошибок отделений: {len(department_errors)}")

    # Формируем блок ошибок профилей, если есть
    if profile_errors:
        report_lines.append("\n=== Ошибки профилей ===")
        for err in profile_errors:
            report_lines.append(err)

    # Формируем блок ошибок специальностей, если есть
    if specialty_errors:
        report_lines.append("\n=== Ошибки специальностей ===")
        for err in specialty_errors:
            report_lines.append(err)

    # Формируем блок ошибок отделений, если есть
    if department_errors:
        report_lines.append("\n=== Ошибки отделений ===")
        for err in department_errors:
            report_lines.append(err)

    # Собираем все строчки в одну большую многострочную строку
    final_report = "\n".join(report_lines)

    # Выводим всё одной записью
    context.log.info(final_report)

    # Также можно вернуть счётчики
    return {
        "total_doctors": total_doctors,
        "new_persons": new_persons,
        "updated_persons": updated_persons,
        "set_departments": set_departments,
        "set_profiles": set_profiles,
        "set_specialties": set_specialties,
        "profile_errors_count": len(profile_errors),
        "specialty_errors_count": len(specialty_errors),
        "department_errors_count": len(department_errors),
    }
