from django.contrib import admin
from .models import SQLQuery, CategorySQLQuery, TypeSQLQuery
from django import forms
from django.utils.safestring import mark_safe
import json


# Форма для редактора SQL с использованием CodeMirror
class SQLQueryForm(forms.ModelForm):
    class Meta:
        model = SQLQuery
        fields = ['name', 'category', 'query_type', 'query', 'description']
        widgets = {
            'query': forms.Textarea(attrs={'class': 'codemirror-textarea'}),
        }


@admin.register(SQLQuery)
class SQLQueryAdmin(admin.ModelAdmin):
    form = SQLQueryForm
    list_display = ( 'name', 'id', 'category', 'query_type', 'created_at')
    search_fields = ('name', 'query')
    list_filter = ('category', 'query_type')  # Добавляем фильтры по категориям и типам
    fields = ('name', 'category', 'query_type', 'query', 'description')
    autocomplete_fields = ['category', 'query_type']  # Используем автозаполнение

    class Media:
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.0/codemirror.min.css',),
        }
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.0/codemirror.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.0/mode/sql/sql.min.js',
            'js/codemirror_init.js',  # Путь к нашему JS файлу
        )


@admin.register(CategorySQLQuery)
class CategorySQLQueryAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name']


@admin.register(TypeSQLQuery)
class TypeSQLQueryAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name']
