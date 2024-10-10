from dal import autocomplete
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import render

from .models import *
from ..data_loader.models.oms_data import *
from ..organization.models import *


class SpecialtyAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return SpecialtyRG014.objects.none()

        qs = SpecialtyRG014.objects.all()

        if self.q:
            qs = qs.filter(description__icontains=self.q)

        return qs


class PostAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return PostRG014.objects.none()

        qs = PostRG014.objects.all()

        if self.q:
            qs = qs.filter(description__icontains=self.q)

        return qs


class DepartmentAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Department.objects.none()

        qs = Department.objects.all()

        # Фильтрация по корпусу (параметр 'building' должен быть передан в GET-запросе)
        building_id = self.forwarded.get('building', None)
        if building_id:
            qs = qs.filter(building_id=building_id)

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs


def update_doctor_records_view(request):
    # Ищем записи в DoctorData
    doctor_data_records = DoctorData.objects.all()

    # Список для СНИЛСов, которые есть в DoctorData, но нет в DoctorRecord
    missing_snils = []
    updated_count = 0

    for doctor_data in doctor_data_records:
        try:
            # Поиск физического лица по СНИЛС
            person = Person.objects.get(snils=doctor_data.snils)

            # Проверка, существует ли запись с таким doctor_code в DoctorRecord
            if not DoctorRecord.objects.filter(doctor_code=doctor_data.doctor_code, person=person).exists():
                # Создание новой записи в DoctorRecord
                DoctorRecord.objects.create(
                    person=person,
                    doctor_code=doctor_data.doctor_code,
                )
                updated_count += 1
        except Person.DoesNotExist:
            # Если физическое лицо с данным СНИЛС не найдено, добавляем в список
            missing_snils.append(doctor_data.snils)

    # Добавляем сообщение с результатами
    messages.success(request, f"Обновлено {updated_count} записей врачей.")

    if missing_snils:
        messages.warning(request, f"Следующие СНИЛС отсутствуют в Person: {', '.join(missing_snils)}")

    return render(request, 'personnel/update_doctor_records.html',
                  {'missing_snils': missing_snils, 'updated_count': updated_count})
