from django.contrib import admin

from apps.home.models import *
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from unfold.admin import ModelAdmin, forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from apps.reports.models import UserGroupAccess
from apps.reports.models import Group as PatientGroup, UserGroupAccess
from django.contrib.auth.forms import UserCreationForm


class UserGroupsForm(forms.ModelForm):
    patient_groups = forms.ModelMultipleChoiceField(
        queryset=PatientGroup.objects.all(),
        required=False,
        widget=FilteredSelectMultiple('Группы пациентов', is_stacked=False),
        label='Группы пациентов'
    )

    class Meta:
        model = User
        # перечисляем все нужные поля + patient_groups
        fields = (
            'username', 'password', 'first_name', 'last_name', 'email',
            'is_active', 'is_staff', 'is_superuser', 'user_permissions',
            'patient_groups',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # загружаем из UserGroupAccess уже назначенные группы
            self.fields['patient_groups'].initial = (
                UserGroupAccess.objects
                .filter(user=self.instance)
                .values_list('group_id', flat=True)
            )

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        selected = self.cleaned_data['patient_groups']
        # удаляем старые доступы, которых нет в выбранном списке
        UserGroupAccess.objects.filter(user=user).exclude(group__in=selected).delete()
        # создаём новые доступы
        for g in selected:
            UserGroupAccess.objects.get_or_create(user=user, group=g)
        return user


class CustomUserCreationForm(UserCreationForm, forms.ModelForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "password1", "password2")


# Отменяем стандартную регистрацию
admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class CustomUserAdmin(ModelAdmin, BaseUserAdmin):
    form = UserGroupsForm
    add_form = CustomUserCreationForm  # теперь Unfold-стиль для создания
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Доступ к группам пациентов', {
            'classes': ('collapse',),
            'fields': ('patient_groups',),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_patient_groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    def get_patient_groups(self, obj):
        return ", ".join(
            obj.usergroupaccess_set.values_list('group__name', flat=True)
        )

    get_patient_groups.short_description = 'Группы пациентов'


@admin.register(Group)
class CustomGroupAdmin(ModelAdmin, BaseGroupAdmin):
    form = BaseGroupAdmin.form
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
