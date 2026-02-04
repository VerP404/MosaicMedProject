from datetime import datetime
from django import forms
from .models import GroupIndicators


class GroupIndicatorsForm(forms.ModelForm):
    class Meta:
        model = GroupIndicators
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Используем наш метод get_hierarchy_display для отображения записи в поле parent
        self.fields['parent'].label_from_instance = lambda obj: obj.get_hierarchy_display()


class YearSelectForm(forms.Form):
    """Форма для выбора года при экспорте планов"""
    year = forms.IntegerField(
        label='Год',
        min_value=2000,
        max_value=2100,
        initial=datetime.now().year,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class ImportPlansForm(forms.Form):
    """Форма для импорта планов из файла"""
    year = forms.IntegerField(
        label='Год',
        min_value=2000,
        max_value=2100,
        initial=datetime.now().year,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    file = forms.FileField(
        label='Файл Excel',
        widget=forms.FileInput(attrs={'accept': '.xlsx,.xls'})
    )


class ExportStructureForm(forms.Form):
    """Форма экспорта структуры: опции для условий фильтрации"""
    include_filters = forms.BooleanField(
        label='Включить условия фильтрации',
        initial=True,
        required=False,
        help_text='Экспортировать условия фильтрации (FilterCondition) для каждой группы',
    )
    filter_year = forms.IntegerField(
        label='Год фильтров',
        min_value=2000,
        max_value=2100,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Все годы'}),
        help_text='Оставьте пустым, чтобы выгрузить условия за все годы; укажите год — только за этот год',
    )


class ImportStructureForm(forms.Form):
    """Пустая форма для подтверждения импорта"""
    pass


class CopyPlansForm(forms.Form):
    """Форма для копирования планов с одного года на другой"""
    source_year = forms.IntegerField(
        label='Год-источник',
        min_value=2000,
        max_value=2100,
        initial=datetime.now().year,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text='С какого года копировать планы (значения по месяцам)',
    )
    target_year = forms.IntegerField(
        label='Год-назначение',
        min_value=2000,
        max_value=2100,
        initial=datetime.now().year + 1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text='На какой год скопировать планы',
    )

    def clean(self):
        data = super().clean()
        if data.get('source_year') == data.get('target_year'):
            raise forms.ValidationError('Год-источник и год-назначение должны отличаться.')
        return data


class CopyFiltersForm(forms.Form):
    """Форма для копирования условий фильтрации с одного года на другой"""
    source_year = forms.IntegerField(
        label='Год-источник',
        min_value=2000,
        max_value=2100,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text='С какого года копировать условия фильтрации',
    )
    target_year = forms.IntegerField(
        label='Год-назначение',
        min_value=2000,
        max_value=2100,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text='На какой год скопировать условия',
    )

    def __init__(self, *args, source_year=None, target_year=None, **kwargs):
        super().__init__(*args, **kwargs)
        if source_year is not None:
            self.fields['source_year'].initial = source_year
        if target_year is not None:
            self.fields['target_year'].initial = target_year

    def clean(self):
        data = super().clean()
        if data.get('source_year') == data.get('target_year'):
            raise forms.ValidationError('Год-источник и год-назначение должны отличаться.')
        return data