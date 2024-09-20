# forms.py
from django import forms


class FileUploadForm(forms.Form):
    file = forms.FileField(label='Выберите CSV файл')
    temp_file_path = forms.CharField(widget=forms.HiddenInput(), required=False)  # Временный путь для сохранения файла
