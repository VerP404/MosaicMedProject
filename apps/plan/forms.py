# admin.py (или forms.py — где вам удобнее)
from django import forms
from .models import GroupIndicators


class GroupIndicatorsForm(forms.ModelForm):
    class Meta:
        model = GroupIndicators
        fields = '__all__'  # или перечислите нужные поля

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Указываем, как формировать название для каждого объекта в списке parent
        self.fields['parent'].label_from_instance = lambda obj: obj.get_hierarchy_display()
