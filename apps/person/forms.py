import datetime
from django.forms.models import BaseInlineFormSet
from django.core.exceptions import ValidationError


class InsurancePolicyInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        intervals = []
        active_policy_count = 0
        today = datetime.date.today()
        for form in self.forms:
            # Пропускаем пустые формы и формы, помеченные на удаление
            if not form.cleaned_data or form.cleaned_data.get('DELETE', False):
                continue
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            if not start_date:
                raise ValidationError("Дата начала страхования обязательна.")
            # Если end_date не указан, считаем его максимально возможной датой для проверки пересечений.
            effective_end = end_date if end_date is not None else datetime.date.max
            # Проверяем пересечение интервалов
            for s, e in intervals:
                if start_date <= e and s <= effective_end:
                    raise ValidationError("Периоды страхования не должны пересекаться.")
            intervals.append((start_date, effective_end))
            # Проверяем, является ли данный полис действующим: сегодня входит в интервал [start_date, end_date]
            if start_date <= today and (end_date is None or end_date >= today):
                active_policy_count += 1
        if active_policy_count != 1:
            raise ValidationError("У физического лица должен быть ровно один действующий полис.")
