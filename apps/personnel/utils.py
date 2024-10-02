from apps.data_loader.models.oms_data import *
from apps.personnel.models import *


def update_doctor_records():
    doctor_data_records = DoctorData.objects.all()

    for doctor_data in doctor_data_records:
        try:
            # Поиск физического лица по СНИЛС
            person = Person.objects.get(snils=doctor_data.snils)

            # Проверка, существует ли запись с таким doctor_code
            if not DoctorRecord.objects.filter(doctor_code=doctor_data.doctor_code, person=person).exists():
                # Создание новой записи в DoctorRecord, остальные поля остаются пустыми
                DoctorRecord.objects.create(
                    person=person,
                    doctor_code=doctor_data.doctor_code,
                )
        except Person.DoesNotExist:
            # Если физическое лицо не найдено, можно залогировать или игнорировать
            print(f"Person with SNILS {doctor_data.snils} not found")
