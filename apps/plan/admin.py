from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import GroupIndicators, OptionsForReportFilters, FilterCondition
from django.urls import reverse


class FilterConditionInline(admin.TabularInline):
    model = FilterCondition
    extra = 1


class GroupIndicatorsAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'level', 'view_subgroups')
    list_filter = ('level',)
    search_fields = ('name',)
    inlines = [FilterConditionInline]

    def view_subgroups(self, obj):
        """Ссылки на подгруппы"""
        subgroups = obj.subgroups.all()
        if subgroups:
            links = [format_html('<a href="{}">{}</a>',
                                 reverse('admin:plan_groupindicators_change', args=[sub.id]), sub.name)
                     for sub in subgroups]
            return format_html(", ".join(links))
        return "-"

    view_subgroups.short_description = "Вложенные группы"

    def get_readonly_fields(self, request, obj=None):
        """Добавление поля с унаследованными фильтрами на страницу редактирования"""
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj and obj.parent:
            readonly_fields = list(readonly_fields) + ['inherited_filters', 'view_subgroups']
        else:
            readonly_fields = list(readonly_fields) + ['view_subgroups']
        return readonly_fields

    def inherited_filters(self, obj):
        """Отображение унаследованных фильтров на странице редактирования"""
        filters = obj.parent.get_all_filters() if obj.parent else []
        if filters:
            inherited_filters_html = "<h3>Наследуемые фильтры</h3><ul>"
            for filter in filters:
                inherited_filters_html += f"<li>{filter.field_name} ({filter.get_filter_type_display()}): {filter.values}</li>"
            inherited_filters_html += "</ul>"
            return mark_safe(inherited_filters_html)
        return "Нет унаследованных фильтров"

    inherited_filters.short_description = "Наследуемые фильтры"

    def get_fields(self, request, obj=None):
        """Определение стандартных полей без добавления inherited_filters в fields"""
        fields = super().get_fields(request, obj)
        return fields


admin.site.register(GroupIndicators, GroupIndicatorsAdmin)
admin.site.register(OptionsForReportFilters)

