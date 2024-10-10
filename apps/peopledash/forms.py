from django import forms


class UploadDataForm(forms.Form):
    file_today = forms.FileField(label="Сегодня")
    file_14_days = forms.FileField(label="14 дней")
    report_datetime = forms.DateTimeField(label="Укажите дату и время отчета",
                                          widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
