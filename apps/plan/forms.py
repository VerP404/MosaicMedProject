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
