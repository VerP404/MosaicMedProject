from django.contrib import admin

from apps.home.models import *
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from unfold.admin import ModelAdmin, forms

# Отменяем стандартную регистрацию
admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    # подтягиваем из BaseUserAdmin все секции для отображения в change_view
    fieldsets = BaseUserAdmin.fieldsets
    # и секции для отображения в add_view
    add_fieldsets = BaseUserAdmin.add_fieldsets

    # можно дополнительно настроить отображение списка
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')


@admin.register(Group)
class CustomGroupAdmin(BaseGroupAdmin, ModelAdmin):
    fieldsets = BaseGroupAdmin.fieldsets
    list_display = BaseGroupAdmin.list_display
    search_fields = BaseGroupAdmin.search_fields


class MainSettingsForm(forms.ModelForm):
    class Meta:
        model = MainSettings
        fields = '__all__'


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


@admin.register(TelegramBot)
class TelegramBotAdmin(ModelAdmin):
    list_display = ('name', 'bot_id', 'token', 'additional_password')
    search_fields = ('name', 'bot_id')
    list_filter = ()


@admin.register(TelegramGroup)
class TelegramGroupAdmin(ModelAdmin):
    list_display = ('name', 'group_id', 'bot')
    search_fields = ('name', 'group_id')
    list_filter = ('bot',)
