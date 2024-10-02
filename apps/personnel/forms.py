from dal import autocomplete
from django import forms
from .models import *
from ..organization.models import Department


class RG014Form(forms.ModelForm):
    class Meta:
        model = RG014
        fields = (
            'spec_issue_date', 'spec_name', 'cert_accred_sign', 'post_name', 'hire_date',
            'dismissal_date')
        widgets = {
            'spec_name': autocomplete.ModelSelect2(url='specialty-autocomplete'),
            'post_name': autocomplete.ModelSelect2(url='post-autocomplete'),
        }

    def __init__(self, *args, **kwargs):
        super(RG014Form, self).__init__(*args, **kwargs)
        # Автозаполнение поля организации кодом МО
        if 'organization' in self.fields and self.instance.organization:
            self.fields['organization'].initial = self.instance.organization.code_mo


class DoctorRecordForm(forms.ModelForm):
    class Meta:
        model = DoctorRecord
        fields = ('doctor_code', 'start_date', 'end_date', 'structural_unit', 'profile', 'specialty', 'department')
        widgets = {
            'department': autocomplete.ModelSelect2(url='department-autocomplete'),
        }


class DigitalSignatureForm(forms.ModelForm):
    class Meta:
        model = DigitalSignature
        fields = ('valid_from', 'valid_to', 'issued_date', 'revoked_date')


class DepartmentActionForm(forms.Form):
    department = forms.ModelChoiceField(queryset=Department.objects.all(), label="Выберите отделение")

