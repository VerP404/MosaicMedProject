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
from apps.data_loader.models.kvazar_data import *
from apps.data_loader.models.iszl import *

# Изменение заголовка и подписи панели администратора
admin.site.site_header = "Административная панель МозаикаМед"
admin.site.site_title = "МозаикаМед"
admin.site.index_title = "Админпанели"


@admin.register(OMSSettings)
class OMSSettingsAdmin(admin.ModelAdmin):
    list_display = ('username', 'password')

    # Ограничение на создание только одной записи
    def has_add_permission(self, request):
        # Проверяем, есть ли уже записи в модели
        count = OMSSettings.objects.all().count()
        if count >= 1:
            return False  # Если запись уже существует, запрещаем создание новой
        return True  # Если записей нет, разрешаем создание


# модель для просмотра импортируемых файлов
@admin.register(DataImport)
class DataImportAdmin(admin.ModelAdmin):
    list_display = ('date_added', 'get_category', 'get_data_type', 'added_count', 'updated_count', 'error_count')
    list_filter = ('data_type__category', 'data_type__name', 'date_added')

    def get_category(self, obj):
        return obj.data_type.category.name

    get_category.short_description = 'Категория'

    def get_data_type(self, obj):
        return obj.data_type.name

    get_data_type.short_description = 'Тип данных'

    def get_readonly_fields(self, request, obj=None):
        # Делаем поля только для чтения, кроме csv_file
        return ['added_count', 'updated_count', 'error_count', 'get_category', 'get_data_type']

    def has_add_permission(self, request):
        return False  # Запрещаем добавление записей

    change_list_template = "admin/omsdata_change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('csv-upload/oms/', self.upload_csv_talons, name='oms_talon_csv_upload'),
            path('csv-upload/doctors/', self.upload_csv_doctors, name='oms_doctor_csv_upload'),
            path('csv-upload/detailed/', self.upload_csv_detailed, name='oms_detailed_csv_upload'),

            path('wo-download/', self.download_wo_talon, name='oms_talon_wo_download'),
        ]
        return custom_urls + urls

    def upload_csv_doctors(self, request):
        if request.method == 'POST':
            form = DataImportForm(request.POST, request.FILES)
            if form.is_valid():
                form_object = form.save()
                form_object.type = 'DOCTORS'  # Указываем тип данных "Врачи"
                form_object.category = 'Web-ОМС'
                # Инициализируем счетчики
                added_count = 0
                error_count = 0

                try:
                    # Чтение CSV файла
                    with form_object.csv_file.open('rb') as csv_file:
                        decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
                        reader = csv.DictReader(decoded_file, delimiter=';')

                        # Проверка корректности полей
                        required_fields = set(DOCTOR_DATA_CSV_TO_MODEL_MAPPING.keys())
                        file_fields = set(reader.fieldnames)

                        if not required_fields.issubset(file_fields):
                            messages.error(request, "Файл не содержит всех необходимых столбцов!")
                            return HttpResponseRedirect(reverse('admin:data_loader_omsdataimport_changelist'))

                        # Удаление всех существующих данных перед загрузкой
                        DoctorData.objects.all().delete()

                        # Загрузка новых данных
                        for row in reader:
                            data = {}
                            for csv_field, model_field in DOCTOR_DATA_CSV_TO_MODEL_MAPPING.items():
                                data[model_field] = row.get(csv_field, '')

                            # Создаем новый объект и сохраняем
                            doctor = DoctorData(
                                snils=row['СНИЛС:'],
                                doctor_code=row['Код врача:'],
                                last_name=row['Фамилия:'],
                                first_name=row['Имя:'],
                                middle_name=row['Отчество:'],
                                birth_date=row['Дата рождения:'],
                                gender=row['Пол'],
                                start_date=row['Дата начала работы:'],
                                end_date=row['Дата окончания работы:'],
                                department=row['Структурное подразделение:'],
                                medical_profile_code=row['Код профиля медпомощи:'],
                                specialty_code=row['Код специальности:'],
                                department_code=row['Код отделения:'],
                                comment=row['Комментарий:']
                            )
                            doctor.save()
                            added_count += 1

                except Exception as e:
                    error_count += 1
                    print(f"Ошибка при обработке файла: {e}")

                form_object.added_count = added_count
                form_object.error_count = error_count
                form_object.save()

                messages.success(request,
                                 f'Данные успешно загружены. Добавлено: {added_count}, Ошибок: {error_count}.')
                return HttpResponseRedirect(reverse('admin:data_loader_omsdataimport_changelist'))

        form = DataImportForm()
        return render(request, 'admin/csv_import_page.html', {'form': form})

    def upload_csv_talons(self, request):
        if request.method == 'POST':
            form = DataImportForm(request.POST, request.FILES)
            if form.is_valid():
                form_object = form.save()
                form_object.type = 'OMS'
                form_object.category = 'Web-ОМС'
                # Инициализируем счетчики
                added_count = 0
                updated_count = 0
                error_count = 0

                with form_object.csv_file.open('rb') as csv_file:
                    decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
                    reader = csv.DictReader(decoded_file, delimiter=';')
                    for row in reader:
                        data = {}
                        for csv_field, model_field in OMS_DATA_CSV_TO_MODEL_MAPPING.items():
                            data[model_field] = row.get(csv_field, '')

                        try:
                            # Используем update_or_create для добавления или обновления записи
                            obj, created = OMSData.objects.update_or_create(
                                talon=data['talon'],  # Поле для поиска существующей записи
                                defaults=data  # Поля для обновления или создания новой записи
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

        form = DataImportForm()
        return render(request, 'admin/csv_import_page.html', {'form': form})

    def upload_csv_detailed(self, request):
        if request.method == 'POST':
            form = DataImportForm(request.POST, request.FILES)
            if form.is_valid():
                form_object = form.save()
                form_object.type = 'DETAILED'
                form_object.category = 'Web-ОМС'
                # Инициализируем счетчики
                added_count = 0
                updated_count = 0
                error_count = 0

                with form_object.csv_file.open('rb') as csv_file:
                    decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
                    reader = csv.DictReader(decoded_file, delimiter=';')

                    csv_data = list(reader)
                    unique_talons = set(row["Номер талона"] for row in csv_data)

                    for talon_number in unique_talons:
                        try:
                            # Проверяем, существуют ли записи для данного талона
                            existing_records = DetailedData.objects.filter(talon_number=talon_number)

                            if existing_records.exists():
                                # Если записи существуют, удаляем их и считаем как обновление
                                updated_count += 1
                                existing_records.delete()
                            else:
                                # Если записи не существовали, считаем как добавление
                                added_count += 1

                            # Добавляем новые записи для данного талона
                            for row in [r for r in csv_data if r["Номер талона"] == talon_number]:
                                data = {}
                                for csv_field, model_field in DETAILED_DATA_CSV_TO_MODEL_MAPPING.items():
                                    data[model_field] = row.get(csv_field, '')

                                # Создаем новую запись
                                DetailedData.objects.create(**data)

                        except Exception as e:
                            # Логируем ошибки и увеличиваем счетчик ошибок
                            print(f"Ошибка при обработке талона {talon_number}: {e}")
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

        form = DataImportForm()
        return render(request, 'admin/csv_import_page.html', {'form': form})

    def download_wo_talon(self, request):
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
                oms_data_import = DataImport.objects.create(
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


DOCTOR_DATA_CSV_TO_MODEL_MAPPING = {
    "СНИЛС:": "snils",
    "Код врача:": "doctor_code",
    "Фамилия:": "last_name",
    "Имя:": "first_name",
    "Отчество:": "middle_name",
    "Дата рождения:": "birth_date",
    "Пол": "gender",
    "Дата начала работы:": "start_date",
    "Дата окончания работы:": "end_date",
    "Структурное подразделение:": "department",
    "Код профиля медпомощи:": "medical_profile_code",
    "Код специальности:": "specialty_code",
    "Код отделения:": "department_code",
    "Комментарий:": "comment",
}
OMS_DATA_CSV_TO_MODEL_MAPPING = {
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
DETAILED_DATA_CSV_TO_MODEL_MAPPING = {
    "Номер талона": "talon_number",
    "Счет": "account_number",
    "Дата выгрузки": "upload_date",
    "Статус": "status",
    "МО": "mo",
    "Дата начала": "start_date",
    "Дата окончания": "end_date",
    "Серия полиса": "policy_series",
    "Номер полиса": "policy_number",
    "ЕНП": "enp",
    "Фамилия": "last_name",
    "Имя": "first_name",
    "Отчество": "middle_name",
    "Страховая организация": "insurance_org",
    "Пол": "gender",
    "Дата рождения": "birth_date",
    "Тип талона": "talon_type",
    "Основной диагноз": "main_diagnosis",
    "Сопутствующий диагноз": "additional_diagnosis",
    "Группа здоровья": "health_group",
    "Доктор (Код)": "doctor_code",
    "Доктор (ФИО)": "doctor_name",
    "Стоимость": "cost",
    "Название услуги": "service_name",
    "Номенклатурный код услуги": "service_code",
    "Доктор-Услуги (Код)": "service_doctor_code",
    "Доктор-Услуги (ФИО)": "service_doctor_name",
    "Дата-Услуги": "service_date",
    "Статус-Услуги": "service_status",
    "Маршрут": "route",
    "Подразделение врача-Услуги": "service_department",
    "Код МО (при оказ.услуги в другой МО)": "external_mo_code",
}


@admin.register(OMSData)
class OMSDataAdmin(admin.ModelAdmin):
    list_display = ('talon', 'patient', 'upload_date', 'status')

    def has_add_permission(self, request):
        return False  # Запрещаем добавление записей


@admin.register(DoctorData)
class DoctorDataAdmin(admin.ModelAdmin):
    list_display = ('doctor_code', 'last_name', 'start_date', 'department')

    def has_add_permission(self, request):
        return False  # Запрещаем добавление записей


@admin.register(DetailedData)
class DetailedAdmin(admin.ModelAdmin):
    list_display = ('talon_number', 'talon_type', 'last_name', 'first_name', 'doctor_code', 'service_name', 'route')

    def has_add_permission(self, request):
        return False  # Запрещаем добавление записей


@admin.register(KvazarSettings)
class OMSSettingsAdmin(admin.ModelAdmin):
    list_display = ('username', 'password')

    # Ограничение на создание только одной записи
    def has_add_permission(self, request):
        # Проверяем, есть ли уже записи в модели
        count = KvazarSettings.objects.all().count()
        if count >= 1:
            return False  # Если запись уже существует, запрещаем создание новой
        return True  # Если записей нет, разрешаем создание


# Создаем инлайн для DataType
class DataTypeInline(admin.TabularInline):
    model = DataType
    extra = 1  # Количество пустых строк для добавления новых типов данных
    fields = ('name', 'description')  # Поля для редактирования


# Настраиваем админку для Category
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')  # Отображение полей в списке категорий
    inlines = [DataTypeInline]  # Добавляем инлайн для типов данных


# Создаем инлайн для DataTypeFieldMapping
class DataTypeFieldMappingInline(admin.TabularInline):
    model = DataTypeFieldMapping
    extra = 1  # Количество пустых строк для добавления новых полей
    fields = ('csv_column_name', 'model_field_name')  # Поля для редактирования


# Настраиваем админку для DataType
@admin.register(DataType)
class DataTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'description')  # Отображение полей в списке типов данных
    inlines = [DataTypeFieldMappingInline]  # Добавляем инлайн для соответствий столбцов


@admin.register(ISZLSettings)
class ISZLSettingsAdmin(admin.ModelAdmin):
    list_display = ('username',)
    search_fields = ('username',)

    # Можно добавить возможность скрывать пароль, если это необходимо

    def has_add_permission(self, request):
        # Проверяем, есть ли уже записи в модели
        count = ISZLSettings.objects.all().count()
        if count >= 1:
            return False  # Если запись уже существует, запрещаем создание новой
        return True  # Если записей нет, разрешаем создание


@admin.register(ISZLPeople)
class ISZLPeopleAdmin(admin.ModelAdmin):
    list_display = ('fio', 'dr', 'enp')
    search_fields = ('fio', 'enp', 'pid')
    list_filter = ('lpu', 'smo')


@admin.register(ISZLDisNab)
class ISZLDisNabAdmin(admin.ModelAdmin):
    list_display = ('fio', 'dr', 'enp', 'datebegin', 'dateend', 'enp')
    search_fields = ('fio', 'enp', 'ds')
    list_filter = ('ds', 'datebegin', 'dateend')


@admin.register(ISZLDisNabJob)
class ISZLDisNabJobAdmin(admin.ModelAdmin):
    list_display = ('fio', 'birth_date', 'enp', 'ds', 'date', 'time', 'smo')
    search_fields = ('fio', 'enp', 'ds')
    list_filter = ('date', 'smo', 'fact')


@admin.register(DS168n)
class DS168nAdmin(admin.ModelAdmin):
    list_display = ('ds', 'profile', 'speciality', 'joint_speciality')
    search_fields = ('ds', 'profile', 'speciality')
    list_filter = ('profile', 'speciality', 'joint_speciality')


@admin.register(DataLoaderConfig)
class DataLoaderConfigAdmin(admin.ModelAdmin):
    list_display = ('data_type', 'table_name', 'column_check', 'columns_for_update', 'encoding', 'delimiter')
    search_fields = ('data_type', 'table_name')
    list_filter = ('data_type',)
