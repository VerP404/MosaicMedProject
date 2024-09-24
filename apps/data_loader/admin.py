# admin.py
from django.contrib import admin
import csv
from django.urls import path
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone

from apps.data_loader.forms import *
from apps.data_loader.selenium_script import logger
from apps.data_loader.models.oms_data import *


@admin.register(OMSSettings)
class OMSSettingsAdmin(admin.ModelAdmin):
    list_display = ('username', 'password')


# модель для просмотра импортируемых файлов
@admin.register(OMSDataImport)
class OMSDataImportAdmin(admin.ModelAdmin):
    list_display = ('date_added', 'added_count', 'updated_count', 'error_count')

    def has_add_permission(self, request):
        return False  # Запрещаем добавление вручную

    change_list_template = "admin/omsdata_change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('csv-upload/', self.upload_csv, name='omsdataimport_csv-upload'),
            path('wo-download/', self.download_from_wo, name='omsdataimport_wo-download'),
        ]
        return custom_urls + urls

    def upload_csv(self, request):
        # Ваш код для обработки ручного импорта CSV
        pass

    def download_from_wo(self, request):
        # Вызываем тот же метод, что и в OMSDataAdmin
        return OMSDataAdmin(self.model, self.admin_site).download_from_wo(request)


OMSDATA_CSV_TO_MODEL_MAPPING = {
    "Талон": "talon",
    "Источник": "source",
    "ID источника": "source_id",
    "Номер счёта": "account_number",
    "Дата выгрузки": "upload_date",
    "Причина аннулирования": "cancellation_reason",
    "Статус": "status",
    "Тип талона": "talon_type",
    "Цель": "goal",
    "Фед. цель": "federal_goal",
    "Пациент": "patient",
    "Дата рождения": "birth_date",
    "Возраст": "age",
    "Пол": "gender",
    "Полис": "policy",
    "Код СМО": "smo_code",
    "Страховая": "insurance",
    "ЕНП": "enp",
    "Начало лечения": "treatment_start",
    "Окончание лечения": "treatment_end",
    "Врач": "doctor",
    "Врач (Профиль МП)": "doctor_profile",
    "Должность мед.персонала (V021)": "staff_position",
    "Подразделение": "department",
    "Условия оказания помощи": "care_conditions",
    "Вид мед. помощи": "medical_assistance_type",
    "Тип заболевания": "disease_type",
    "Характер основного заболевания": "main_disease_character",
    "Посещения": "visits",
    "Посещения в МО": "mo_visits",
    "Посещения на Дому": "home_visits",
    "Случай": "case",
    "Диагноз основной (DS1)": "main_diagnosis",
    "Сопутствующий диагноз (DS2)": "additional_diagnosis",
    "Профиль МП": "mp_profile",
    "Профиль койки": "bed_profile",
    "Диспансерное наблюдение": "dispensary_monitoring",
    "Специальность": "specialty",
    "Исход": "outcome",
    "Результат": "result",
    "Оператор": "operator",
    "Первоначальная дата ввода": "initial_input_date",
    "Дата последнего изменения": "last_change_date",
    "Тариф": "tariff",
    "Сумма": "amount",
    "Оплачено": "paid",
    "Тип оплаты": "payment_type",
    "Санкции": "sanctions",
    "КСГ": "ksg",
    "КЗ": "kz",
    "Код схемы лекарственной терапии": "therapy_schema_code",
    "УЕТ": "uet",
    "Классификационный критерий": "classification_criterion",
    "ШРМ": "shrm",
    "МО, направившая": "directing_mo",
    "Код способа оплаты": "payment_method_code",
    "Новорожденный": "newborn",
    "Представитель": "representative",
    "Доп. инф. о статусе талона": "additional_status_info",
    "КСЛП": "kslp",
    "Источник оплаты": "payment_source",
    "Отчетный период выгрузки": "report_period",
}


@admin.register(OMSData)
class OMSDataAdmin(admin.ModelAdmin):
    list_display = ('talon', 'patient', 'upload_date', 'status')
    change_list_template = "admin/omsdata_change_list.html"  # Подключаем кастомный шаблон

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('csv-upload/', self.upload_csv, name='learn_omsdata_csv-upload'),
            path('wo-download/', self.download_from_wo, name='learn_omsdata_wo-download'),

        ]
        return custom_urls + urls

    def upload_csv(self, request):
        if request.method == 'POST':
            form = OMSDataImportForm(request.POST, request.FILES)
            if form.is_valid():
                # Сохраняем информацию о загрузке файла
                form_object = form.save()

                # Инициализируем счетчики
                added_count = 0
                updated_count = 0
                error_count = 0

                # Чтение файла как байты
                with form_object.csv_file.open('rb') as csv_file:
                    # Декодируем вручную используя нужную кодировку
                    decoded_file = csv_file.read().decode('utf-8-sig').splitlines()

                    # Теперь используем DictReader для обработки CSV данных
                    reader = csv.DictReader(decoded_file, delimiter=';')
                    for row in reader:
                        oms_data = {}
                        for csv_field, model_field in OMSDATA_CSV_TO_MODEL_MAPPING.items():
                            oms_data[model_field] = row.get(csv_field, '')

                        try:
                            # Используем update_or_create для добавления или обновления записи
                            obj, created = OMSData.objects.update_or_create(
                                talon=oms_data['talon'],  # Поле для поиска существующей записи
                                defaults=oms_data  # Поля для обновления или создания новой записи
                            )
                            if created:
                                added_count += 1
                            else:
                                updated_count += 1
                        except Exception as e:
                            # Если произошла ошибка, увеличиваем счетчик ошибок
                            print(f"Ошибка при обработке строки: {row}")
                            print(f"Ошибка: {e}")
                            error_count += 1

                # Обновляем статистику в модели OMSDataImport
                form_object.added_count = added_count
                form_object.updated_count = updated_count
                form_object.error_count = error_count
                form_object.save()

                # Сообщение для пользователя
                messages.success(request,
                                 f'Данные успешно импортированы. Добавлено: {added_count}, Обновлено: {updated_count}, Ошибки: {error_count}.')
                return HttpResponseRedirect(reverse('admin:index'))

        form = OMSDataImportForm()
        return render(request, 'admin/csv_import_page.html', {'form': form})

    def download_from_wo(self, request):
        # Получаем настройки из базы данных
        try:
            oms_settings = OMSSettings.objects.latest('id')
        except OMSSettings.DoesNotExist:
            messages.error(request,
                           'Настройки OMS не найдены в базе данных. Пожалуйста, добавьте настройки через админку.')
            return redirect('..')  # Перенаправляем обратно на страницу списка

        if request.method == 'POST':
            form = WODataDownloadForm(request.POST)
            if form.is_valid():
                logger.info("Начинаем выполнение run_selenium_script")
                start_date = form.cleaned_data['start_date'].strftime('%d-%m-%y')
                end_date = form.cleaned_data['end_date'].strftime('%d-%m-%y')
                start_date_treatment = form.cleaned_data['start_date_treatment'].strftime('%d-%m-%y')

                # Запускаем скрипт Selenium с указанными параметрами
                from .selenium_script import run_selenium_script

                success, added_count, updated_count, error_count = run_selenium_script(
                    username=oms_settings.username,
                    password=oms_settings.password,
                    start_date=start_date,
                    end_date=end_date,
                    start_date_treatment=start_date_treatment
                )
                # Сохраняем информацию в OMSDataImport
                oms_data_import = OMSDataImport.objects.create(
                    csv_file=None,  # Если файл не сохраняется, оставьте None
                    date_added=timezone.now(),
                    added_count=added_count,
                    updated_count=updated_count,
                    error_count=error_count
                )

                logger.info("Выполнение run_selenium_script завершено")

                if success:
                    messages.success(request, 'Данные успешно загружены и обработаны.')
                else:
                    messages.error(request, 'Произошла ошибка при загрузке данных.')
                logger.info("Завершаем метод download_from_wo")
                return redirect('..')  # Перенаправляем обратно на страницу списка
        else:
            form = WODataDownloadForm(initial={
                'username': oms_settings.username,
                'password': oms_settings.password,
            })

        context = {
            'form': form,
            'opts': self.model._meta,
        }
        return render(request, 'admin/wo_data_download.html', context)
