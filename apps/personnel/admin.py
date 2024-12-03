import csv
from datetime import date, datetime

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import path, reverse
from django.contrib import messages
from django.utils.html import format_html
from django.shortcuts import render, redirect

from .forms import *
from .models import *
from ..data_loader.models.oms_data import *
from ..organization.models import MiskauzDepartment, OMSDepartment


class DoctorRecordInline(admin.TabularInline):
    model = DoctorRecord
    form = DoctorRecordForm
    extra = 0
    fields = (
        'doctor_code', 'start_date', 'end_date', 'department', 'specialty', 'profile',)
    verbose_name = "Запись врача"
    verbose_name_plural = "Записи врача"


class RG014Inline(admin.TabularInline):
    model = RG014
    form = RG014Form  # Используем форму с автозаполнением
    extra = 0
    fields = ('spec_issue_date', 'spec_name', 'cert_accred_sign', 'post_name', 'hire_date',
              'dismissal_date')
    verbose_name = "Запись RG014"
    verbose_name_plural = "Записи RG014"


class DigitalSignatureInline(admin.TabularInline):
    model = DigitalSignature
    extra = 0
    fields = (
        'added_at', 'application_date', 'valid_from', 'valid_to', 'issued_date', 'scan', 'scan_uploaded_at',
        'revoked_date')
    readonly_fields = ('scan_uploaded_at', 'added_at')
    verbose_name = "ЭЦП"
    verbose_name_plural = "ЭЦП"


class MaternityLeaveInline(admin.TabularInline):
    model = MaternityLeave
    extra = 0
    fields = ('start_date', 'end_date', 'note')
    verbose_name = "Декрет"
    verbose_name_plural = "Декреты"


class DigitalSignatureFilter(admin.SimpleListFilter):
    title = 'ЭЦП'
    parameter_name = 'digital_signature_status'

    def lookups(self, request, model_admin):
        return (
            ('active', 'С ЭЦП'),
            ('inactive', 'Без ЭЦП'),
        )

    def queryset(self, request, queryset):
        today = date.today()
        if self.value() == 'active':
            return queryset.filter(digital_signatures__valid_from__lte=today,
                                   digital_signatures__valid_to__gte=today).distinct()
        elif self.value() == 'inactive':
            return queryset.exclude(digital_signatures__valid_from__lte=today,
                                    digital_signatures__valid_to__gte=today).distinct()


class MaternityLeaveFilter(admin.SimpleListFilter):
    title = "В декрете"
    parameter_name = "is_on_maternity_leave"

    def lookups(self, request, model_admin):
        return (
            ('yes', "Да"),
            ('no', "Нет"),
        )

    def queryset(self, request, queryset):
        today = datetime.now().date()
        if self.value() == 'yes':
            return queryset.filter(
                maternity_leaves__start_date__lte=today
            ).filter(
                models.Q(maternity_leaves__end_date__isnull=True) |
                models.Q(maternity_leaves__end_date__gte=today)
            ).distinct()
        elif self.value() == 'no':
            # Исключаем записи с активными декретами
            return queryset.exclude(
                maternity_leaves__start_date__lte=today
            ).distinct()





class DoctorCodeFilter(admin.SimpleListFilter):
    title = 'Фильтр по коду врача'
    parameter_name = 'doctor_code_filter'

    def lookups(self, request, model_admin):
        return (
            ('startswith', 'Начинается с'),
            ('contains', 'Содержит'),
        )

    def queryset(self, request, queryset):
        search_value = request.GET.get('q', '')  # Извлечение значения из строки поиска
        if not search_value:
            return queryset

        if self.value() == 'startswith':
            return queryset.filter(doctor_code__startswith=search_value)
        elif self.value() == 'contains':
            return queryset.filter(doctor_code__icontains=search_value)
        return queryset


# Форма для выбора отделения
class DepartmentForm(forms.Form):
    department = forms.CharField(label="Отделение", max_length=255)


@admin.register(DoctorRecord)
class DoctorRecordAdmin(admin.ModelAdmin):
    change_list_template = "admin/doctor_change_list.html"
    list_display = ('person', 'doctor_code', 'start_date', 'end_date', 'department',)
    list_filter = ('start_date', 'end_date', 'department', DoctorCodeFilter)
    list_editable = ('start_date', 'end_date', 'department')

    # Настройка поиска по doctor_code (начинается с и содержит)
    search_fields = ('doctor_code',)
    actions = ['set_department']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('update-doctor-records/', self.admin_site.admin_view(self.update_doctor_records),
                 name='update_doctor_records'),
            path('insert-doctors-into-person/', self.admin_site.admin_view(self.insert_doctors_into_person),
                 name='insert_doctors_into_person'),
            path('match-departments/', self.admin_site.admin_view(self.match_departments), name='match_departments'),

        ]
        return custom_urls + urls

    def match_departments(self, request):
        updated_count = 0

        # Получаем все записи DoctorRecord
        doctor_records = DoctorRecord.objects.all()

        for record in doctor_records:
            # Сначала ищем совпадение в OMSDepartment
            oms_department = OMSDepartment.objects.filter(name=record.structural_unit).first()
            if oms_department:
                record.department = oms_department.department
                record.save()
                updated_count += 1
                continue  # Переходим к следующей записи

            # Если не найдено в OMSDepartment, ищем в MiskauzDepartment
            miskauz_department = MiskauzDepartment.objects.filter(name=record.structural_unit).first()
            if miskauz_department:
                record.department = miskauz_department.department
                record.save()
                updated_count += 1

        # Выводим сообщение об обновленных записях
        messages.success(request, f'Обновлено {updated_count} записей в DoctorRecord.')
        return redirect('admin:personnel_doctorrecord_changelist')

    def insert_doctors_into_person(self, request):
        inserted_count = 0
        existing_snils = []

        # Получаем все записи из DoctorData
        doctor_data_records = DoctorData.objects.all()

        for doctor_data in doctor_data_records:
            # Проверяем, существует ли Person с таким СНИЛС
            if not Person.objects.filter(snils=doctor_data.snils).exists():
                # Преобразуем дату рождения в формат YYYY-MM-DD
                try:
                    birth_date = datetime.strptime(doctor_data.birth_date, '%d-%m-%Y').date()
                except ValueError:
                    messages.error(request,
                                   f"Неверный формат даты для СНИЛС {doctor_data.snils}: {doctor_data.birth_date}")
                    continue

                # Если такого физлица нет, создаём новое
                Person.objects.create(
                    snils=doctor_data.snils,
                    last_name=doctor_data.last_name,
                    first_name=doctor_data.first_name,
                    patronymic=doctor_data.middle_name,
                    date_of_birth=birth_date,
                    gender=doctor_data.gender[0].upper()  # предполагается, что гендер представлен буквой (M/F)
                )
                inserted_count += 1
            else:
                existing_snils.append(doctor_data.snils)

        messages.success(request, f'Вставлено {inserted_count} новых записей в Person.')
        if existing_snils:
            messages.warning(request, f"Следующие СНИЛС уже существуют: {', '.join(existing_snils)}")

        return redirect('admin:personnel_doctorrecord_changelist')

    def update_doctor_records(self, request):
        updated_count = 0
        missing_snils = []

        # Получаем все записи из DoctorData
        doctor_data_records = DoctorData.objects.all()

        for doctor_data in doctor_data_records:
            try:
                # Ищем соответствующее лицо по СНИЛС
                person = Person.objects.get(snils=doctor_data.snils)

                # Проверка наличия записи в DoctorRecord для данного лица
                doctor_record, created = DoctorRecord.objects.get_or_create(
                    person=person,
                    doctor_code=doctor_data.doctor_code,
                )

                # Обновляем профиль и специальность, если они заданы
                if doctor_data.medical_profile_code:
                    # Извлекаем код профиля до пробела
                    profile_code = doctor_data.medical_profile_code.split(' ')[0]
                    try:
                        # Находим профиль по коду
                        profile = Profile.objects.get(code=profile_code)
                        doctor_record.profile = profile
                    except Profile.DoesNotExist:
                        messages.warning(request, f"Профиль с кодом {profile_code} не найден для врача {person}")

                if doctor_data.specialty_code:
                    # Извлекаем код специальности до пробела
                    specialty_code = doctor_data.specialty_code.split(' ')[0]
                    try:
                        # Находим специальность по коду
                        specialty = Specialty.objects.get(code=specialty_code)
                        doctor_record.specialty = specialty
                    except Specialty.DoesNotExist:
                        messages.warning(request,
                                         f"Специальность с кодом {specialty_code} не найдена для врача {person}")

                # Заполняем поле структурного подразделения (structural_unit)
                doctor_record.structural_unit = doctor_data.department  # Прямое заполнение текстом

                # Сохраняем запись
                doctor_record.save()
                updated_count += 1

            except Person.DoesNotExist:
                missing_snils.append(doctor_data.snils)

        # Вывод сообщений об успешном обновлении и предупреждениях
        messages.success(request, f'Обновлено {updated_count} записей врачей.')
        if missing_snils:
            messages.warning(request, f"СНИЛС отсутствуют в Person: {', '.join(missing_snils)}")

        return redirect('admin:personnel_doctorrecord_changelist')

    # Функция для массового присвоения отделений
    def set_department(self, request, queryset):
        debug_info = []  # Список для отладочной информации

        if 'apply' in request.POST:
            debug_info.append("POST-запрос получен.")
            form = DepartmentActionForm(request.POST)

            if form.is_valid():
                debug_info.append("Форма валидна.")
                department = form.cleaned_data['department']
                try:
                    # Обновляем записи в базе данных
                    updated_count = queryset.update(department=department)
                    messages.success(request, f'{updated_count} записей было обновлено.')
                    debug_info.append(f"Успешно обновлено {updated_count} записей.")
                    return redirect('admin:personnel_doctorrecord_changelist')  # Редирект после успешного обновления
                except Exception as e:
                    messages.error(request, f'Ошибка при обновлении записей: {str(e)}')
                    debug_info.append(f"Ошибка при обновлении: {str(e)}")
            else:
                messages.error(request, 'Форма неверна, проверьте введённые данные.')
                debug_info.append("Форма не валидна.")
        else:
            debug_info.append("Форма не была отправлена.")
            form = DepartmentActionForm()

        # Возвращаем отладочную информацию на страницу
        return render(request, 'admin/set_department_action.html', {
            'form': form,
            'records': queryset,
            'debug_info': '\n'.join(debug_info)
        })


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'snils', 'email', 'phone_number', 'telegram', 'digital_signature_status',
                    'maternity_leave_status')
    search_fields = ('last_name', 'first_name', 'snils')
    list_filter = ('citizenship', DigitalSignatureFilter, MaternityLeaveFilter)
    fieldsets = (
        (None, {
            'fields': ('snils', 'last_name', 'first_name', 'patronymic', 'date_of_birth', 'gender', 'citizenship')
        }),
        ('Контакты', {
            'fields': ('email', 'phone_number', 'telegram')
        }),
    )
    inlines = [DoctorRecordInline, RG014Inline, DigitalSignatureInline, MaternityLeaveInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related('doctor_records')  # Для оптимизации запросов
        return queryset

    def digital_signature_status(self, obj):
        today = date.today()
        digital_signature = obj.digital_signatures.filter(valid_from__lte=today, valid_to__gte=today).first()
        if digital_signature:
            return format_html('<span style="color: green;">✔</span>')
        else:
            return format_html('<span style="color: red;">✘</span>')

    digital_signature_status.short_description = 'ЭЦП'

    def maternity_leave_status(self, obj):
        if obj.is_on_maternity_leave:
            return format_html('<span style="color: green;">✔</span>')
        return format_html('<span style="color: red;">✘</span>')

    maternity_leave_status.short_description = "В декрете"


@admin.register(RG014)
class RG014Admin(admin.ModelAdmin):
    list_display = (
        'person', 'organization', 'spec_issue_date', 'spec_name', 'cert_accred_sign',
        'post_name',
        'hire_date', 'dismissal_date')
    actions = ['export_as_csv']

    search_fields = ('person__last_name', 'person__first_name',)
    list_filter = ('spec_name', 'post_name', 'organization', 'cert_accred_sign')
    autocomplete_fields = ['organization', 'spec_name', 'post_name']
    ordering = ['person']

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export Selected"


class SpecialtyInline(admin.TabularInline):
    model = Specialty
    extra = 1  # Количество пустых строк для добавления новых записей
    fields = ('code', 'description')  # Поля для редактирования


class ProfileInline(admin.TabularInline):
    model = Profile
    extra = 1
    fields = ('code', 'description')


class SpecialtyRG014Inline(admin.TabularInline):
    model = SpecialtyRG014
    extra = 1
    fields = ('code', 'description')


class PostRG014Inline(admin.TabularInline):
    model = PostRG014
    extra = 1
    fields = ('code', 'description')


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('code', 'description')
    search_fields = ('code', 'description')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('code', 'description')
    search_fields = ('code', 'description')


@admin.register(SpecialtyRG014)
class SpecialtyRG014Admin(admin.ModelAdmin):
    list_display = ('code', 'description')
    search_fields = ('code', 'description')


@admin.register(PostRG014)
class PostRG014Admin(admin.ModelAdmin):
    list_display = ('code', 'description')
    search_fields = ('code', 'description')


# Определяем кастомный фильтр
class StatusFilter(SimpleListFilter):
    title = 'Статус'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('active', 'Действует'),
            ('inactive', 'Не действует'),
        )

    def queryset(self, request, queryset):
        today = date.today()
        if self.value() == 'active':
            return queryset.filter(valid_from__lte=today, valid_to__gte=today)
        if self.value() == 'inactive':
            return queryset.exclude(valid_from__lte=today, valid_to__gte=today)


@admin.register(DigitalSignature)
class DigitalSignatureAdmin(admin.ModelAdmin):
    list_display = ('person', 'valid_from', 'valid_to', 'scan', 'scan_uploaded_at', 'added_at', 'status')
    search_fields = ('person__last_name', 'person__first_name')
    list_filter = ('valid_from', 'valid_to', 'scan_uploaded_at', StatusFilter)

    def status(self, obj):
        today = date.today()
        if obj.valid_from <= today <= obj.valid_to:
            return format_html('<span style="color: green;">✔</span>')
        else:
            return format_html('<span style="color: red;">✘</span>')

    status.short_description = 'Статус'
