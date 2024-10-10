from django.contrib import admin

from django import forms
from apps.home.models import *


class MainSettingsForm(forms.ModelForm):
    class Meta:
        model = MainSettings
        fields = '__all__'
        widgets = {
            'dash_ip': forms.TextInput(attrs={'placeholder': 'Введите IP аналитической системы'}),
            'dash_port': forms.NumberInput(attrs={'placeholder': 'Введите порт аналитической системы'}),
            'main_app_ip': forms.TextInput(attrs={'placeholder': 'Введите IP основного приложения'}),
            'main_app_port': forms.NumberInput(attrs={'placeholder': 'Введите порт основного приложения'}),
        }


@admin.register(MainSettings)
class MainSettingsAdmin(admin.ModelAdmin):
    form = MainSettingsForm
    list_display = ('__str__',)

    # Ограничение на создание только одной записи
    def has_add_permission(self, request):
        # Проверяем, есть ли уже записи в модели
        count = MainSettings.objects.all().count()
        if count >= 1:
            return False  # Если запись уже существует, запрещаем создание новой
        return True  # Если записей нет, разрешаем создание
