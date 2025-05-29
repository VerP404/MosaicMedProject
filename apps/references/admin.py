from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin


from .models import MKB10, InsuranceCompany


@admin.register(MKB10)
class MKB10Admin(ModelAdmin):
    list_display = ('code', 'name', 'parent_code', 'level', 'is_active', 'is_final', 'children_count', 'created_at')
    list_filter = (
        'is_active',
        'is_final',
        'level'
    )
    search_fields = ('code', 'name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'is_final')

    fieldsets = (
        ('Основная информация', {
            'fields': ('code', 'name', 'parent', 'level', 'is_active', 'is_final'),
            'classes': ('card',)
        }),
        ('Дополнительная информация', {
            'fields': ('description', 'created_at', 'updated_at'),
            'classes': ('card', 'collapse')
        }),
    )

    def parent_code(self, obj):
        return obj.parent.code if obj.parent else '-'

    parent_code.short_description = 'Родительский код'

    def children_count(self, obj):
        count = obj.get_children_count()
        return format_html(
            '<span class="text-{}">{}</span>',
            'success' if count > 0 else 'gray',
            count
        )

    children_count.short_description = 'Количество подкодов'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent')


@admin.register(InsuranceCompany)
class InsuranceCompanyAdmin(ModelAdmin):
    list_display = ('smocod', 'nam_smok', 'inn', 'is_active', 'is_default', 'insured_count', 'created_at')
    list_filter = ('is_active', 'is_default', 'year_work')
    search_fields = ('smocod', 'nam_smok', 'nam_smop', 'inn', 'ogrn')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Основная информация', {
            'fields': ('smocod', 'nam_smok', 'nam_smop', 'inn', 'ogrn', 'kpp', 'okopf', 'org_type'),
            'classes': ('card',)
        }),
        ('Адреса', {
            'fields': (
                ('jur_address_index', 'jur_address'),
                ('pst_address_index', 'pst_address')
            ),
            'classes': ('card',)
        }),
        ('Руководитель', {
            'fields': ('head_lastname', 'head_firstname', 'head_middlename'),
            'classes': ('card',)
        }),
        ('Контакты', {
            'fields': ('phone', 'fax', 'hot_line', 'email', 'website'),
            'classes': ('card',)
        }),
        ('Лицензия', {
            'fields': ('license_number', 'license_start_date', 'license_end_date'),
            'classes': ('card',)
        }),
        ('Статистика', {
            'fields': ('year_work', 'last_update', 'insured_count'),
            'classes': ('card',)
        }),
        ('Статус', {
            'fields': ('is_active', 'is_default'),
            'classes': ('card',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('card', 'collapse')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request)
