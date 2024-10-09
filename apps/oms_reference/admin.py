from django.contrib import admin
from django.db.models.functions import Cast
from django import forms
from django.db.models import IntegerField, Case, When, Value

from .models import *
from ..organization.models import MedicalOrganization


@admin.register(GeneralOMSTarget)
class GeneralOMSTargetAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'start_date', 'end_date')
    search_fields = ('code', 'name')
    list_editable = ('name', 'start_date', 'end_date')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            # Пробуем привести к числу, если возможно
            numeric_code=Case(
                When(code__regex=r'^\d+$', then=Cast('code', IntegerField())),  # Если значение — число
                default=Value(None),  # Если не число, ставим None
                output_field=IntegerField(),
            )
        ).order_by('numeric_code', 'code')  # Сначала сортировка по числу, потом по строкам


class MedicalOrganizationOMSTargetForm(forms.ModelForm):
    class Meta:
        model = MedicalOrganizationOMSTarget
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'instance' in kwargs and kwargs['instance']:
            instance = kwargs['instance']
            # Если мы редактируем существующую запись, то не исключаем текущую цель
            used_targets = MedicalOrganizationOMSTarget.objects.filter(
                organization=instance.organization
            ).exclude(general_target=instance.general_target).values_list('general_target', flat=True)
        else:
            # Если создаем новую запись, исключаем все использованные цели для выбранной организации
            used_targets = MedicalOrganizationOMSTarget.objects.filter(
                organization=self.initial.get('organization')
            ).values_list('general_target', flat=True)

        self.fields['general_target'].queryset = GeneralOMSTarget.objects.exclude(id__in=used_targets)


@admin.register(OMSTargetCategory)
class OMSTargetCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(MedicalOrganizationOMSTarget)
class MedicalOrganizationOMSTargetAdmin(admin.ModelAdmin):
    form = MedicalOrganizationOMSTargetForm
    list_display = ('general_target', 'is_active', 'start_date', 'end_date', 'get_categories')
    list_filter = ('is_active', 'categories', 'start_date', 'end_date')
    search_fields = ('general_target__name',)
    autocomplete_fields = ['organization', 'general_target']
    list_editable = ('is_active', 'start_date', 'end_date')
    ordering = ('general_target',)
    filter_horizontal = ('categories',)

    # Метод для отображения категорий
    def get_categories(self, obj):
        return ", ".join([category.name for category in obj.categories.all()])

    get_categories.short_description = "Категории"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if not obj:
            user_org = MedicalOrganization.objects.first()  # Логика для выбора организации
            form.base_fields['organization'].initial = user_org
            form.base_fields['organization'].disabled = True

        return form


@admin.register(StatusWebOMS)
class StatusWebOMSAdmin(admin.ModelAdmin):
    list_display = ('status', 'name',)
    search_fields = ('status', 'name',)
    list_editable = ('name',)
