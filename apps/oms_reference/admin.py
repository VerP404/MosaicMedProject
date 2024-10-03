from django.contrib import admin
from django.db.models.functions import Cast
from django.db.models import IntegerField
from django import forms

from .models import *
from ..organization.models import MedicalOrganization


@admin.register(GeneralOMSTarget)
class GeneralOMSTargetAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'start_date', 'end_date')
    search_fields = ('code', 'name')
    list_editable = ('name', 'start_date', 'end_date')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Преобразуем часть кода в число для сортировки
        return qs.annotate(
            numeric_code=Cast('code', IntegerField())
        ).order_by('numeric_code', 'code')


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


@admin.register(MedicalOrganizationOMSTarget)
class MedicalOrganizationOMSTargetAdmin(admin.ModelAdmin):
    form = MedicalOrganizationOMSTargetForm
    list_display = ('general_target', 'is_active', 'start_date', 'end_date')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('general_target__name',)
    autocomplete_fields = ['organization', 'general_target']
    list_editable = ('is_active', 'start_date', 'end_date')
    ordering = ('general_target',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if not obj:
            # Если создаем новую запись, заполняем поле организации
            user_org = MedicalOrganization.objects.first()  # Пример: укажите логику для выбора организации
            form.base_fields['organization'].initial = user_org
            form.base_fields['organization'].disabled = True

        return form
