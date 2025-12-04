from django import forms
from datetime import datetime


class DNCSVUploadForm(forms.Form):
    """Форма для загрузки CSV файлов диспансерного наблюдения"""
    csv_file = forms.FileField(
        label="CSV файл",
        help_text="Выберите CSV файл с данными диспансерного наблюдения",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        })
    )
    year = forms.IntegerField(
        label="Год данных",
        min_value=2000,
        max_value=2100,
        initial=datetime.now().year,
        help_text="Год, за который загружаются данные",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': str(datetime.now().year)
        })
    )
    
    def clean_csv_file(self):
        csv_file = self.cleaned_data.get('csv_file')
        if csv_file:
            if not csv_file.name.endswith('.csv'):
                raise forms.ValidationError("Файл должен иметь расширение .csv")
            if csv_file.size > 100 * 1024 * 1024:  # 100 MB
                raise forms.ValidationError("Размер файла не должен превышать 100 МБ")
        return csv_file


