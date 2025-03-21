from django.contrib import admin

from django import forms
from apps.home.models import *
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from unfold.admin import ModelAdmin

# Отменяем стандартную регистрацию
admin.site.unregister(User)
admin.site.unregister(Group)


# Регистрируем заново, используя чистый unfold
@admin.register(User)
class CustomUserAdmin(ModelAdmin, BaseUserAdmin):
    pass


@admin.register(Group)
class CustomGroupAdmin(ModelAdmin, BaseGroupAdmin):
    pass


class MainSettingsForm(forms.ModelForm):
    class Meta:
        model = MainSettings
        fields = '__all__'
        widgets = {
            'dash_ip': forms.TextInput(attrs={'placeholder': 'Введите IP аналитической системы'}),
            'dash_port': forms.NumberInput(attrs={'placeholder': 'Введите порт аналитической системы'}),
            'main_app_ip': forms.TextInput(attrs={'placeholder': 'Введите IP основного приложения'}),
            'main_app_port': forms.NumberInput(attrs={'placeholder': 'Введите порт основного приложения'}),
            'dash_chief_ip': forms.TextInput(attrs={'placeholder': 'Введите IP панели главного врача'}),
            'dash_chief_port': forms.NumberInput(attrs={'placeholder': 'Введите порт панели главного врача'}),
        }


@admin.register(MainSettings)
class MainSettingsAdmin(ModelAdmin):
    form = MainSettingsForm
    list_display = ('__str__',)

    # Ограничение на создание только одной записи
    def has_add_permission(self, request):
        # Проверяем, есть ли уже записи в модели
        count = MainSettings.objects.all().count()
        if count >= 1:
            return False  # Если запись уже существует, запрещаем создание новой
        return True  # Если записей нет, разрешаем создание
