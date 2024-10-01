import csv

from django.contrib import admin
from django.http import HttpResponse

from .forms import *
from .models import *


class DoctorRecordInline(admin.TabularInline):
    model = DoctorRecord
    form = DoctorRecordForm
    extra = 1  # Количество пустых строк для добавления новых записей врача
    fields = (
        'doctor_code', 'start_date', 'end_date', 'department', 'specialty', 'profile',)
    verbose_name = "Запись врача"
    verbose_name_plural = "Записи врача"


class RG014Inline(admin.TabularInline):
    model = RG014
    form = RG014Form  # Используем форму с автозаполнением
    extra = 1
    fields = ('spec_issue_date', 'spec_name', 'cert_accred_sign', 'post_name', 'hire_date',
              'dismissal_date')
    verbose_name = "Запись RG014"
    verbose_name_plural = "Записи RG014"


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'snils', 'email', 'phone_number', 'telegram')
    search_fields = ('last_name', 'first_name', 'snils')
    list_filter = ('citizenship',)
    fieldsets = (
        (None, {
            'fields': ('snils', 'last_name', 'first_name', 'patronymic', 'date_of_birth', 'gender', 'citizenship')
        }),
        ('Контакты', {
            'fields': ('email', 'phone_number', 'telegram')
        }),
    )
    inlines = [DoctorRecordInline, RG014Inline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related('doctor_records')  # Для оптимизации запросов
        return queryset


@admin.register(RG014)
class RG014Admin(admin.ModelAdmin):
    list_display = (
        'person', 'organization', 'spec_issue_date',  'spec_name', 'cert_accred_sign',
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
