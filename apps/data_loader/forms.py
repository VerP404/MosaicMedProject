# apps/data_loader/forms.py

from django.forms import ModelForm
from django import forms
from datetime import datetime, timedelta

from apps.data_loader.models.oms_data import *


class DataImportForm(ModelForm):
    class Meta:
        model = DataImport
        fields = ['csv_file', ]

    def __init__(self, *args, **kwargs):
        super(DataImportForm, self).__init__(*args, **kwargs)
        self.fields['csv_file'].label = "CSV файл"


class WODataDownloadForm(forms.Form):
    username = forms.CharField(label='Логин', max_length=255, required=False, disabled=True)
    password = forms.CharField(label='Пароль', max_length=255, required=False, disabled=True,
                               widget=forms.PasswordInput)
    category = forms.CharField(label='Категория', max_length=255, required=False, disabled=True)
    type = forms.CharField(label='Тип', max_length=255, required=False, disabled=True)
    start_date = forms.DateField(
        label='Дата начала',
        initial=(datetime.now() - timedelta(days=1)).strftime('%d-%m-%y'),
        input_formats=['%d-%m-%y'],
        widget=forms.DateInput(format='%d-%m-%y')
    )
    end_date = forms.DateField(
        label='Дата окончания',
        initial=(datetime.now() - timedelta(days=1)).strftime('%d-%m-%y'),
        input_formats=['%d-%m-%y'],
        widget=forms.DateInput(format='%d-%m-%y')
    )
    start_date_treatment = forms.DateField(
        label='Дата начала лечения',
        initial=datetime(datetime.now().year, 1, 1).strftime('%d-%m-%y'),
        input_formats=['%d-%m-%y'],
        widget=forms.DateInput(format='%d-%m-%y')
    )
