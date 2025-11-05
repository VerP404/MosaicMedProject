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
