from django import forms


class ExportPortalStructureForm(forms.Form):
    region_code = forms.CharField(
        label="Код региона",
        max_length=10,
        initial="36",
        help_text="Для Portal: region_code (Воронеж = 36)",
    )
    region_name = forms.CharField(
        label="Название региона",
        max_length=255,
        initial="Воронеж",
    )
    org_code = forms.CharField(
        label="Код организации (org_code)",
        max_length=20,
        required=False,
        help_text="Короткий код для Portal (001, 003…). Пусто — из code_mo МО",
    )
    merge_file = forms.FileField(
        label="Эталонный medical_structure.json Portal (опционально)",
        required=False,
        widget=forms.FileInput(attrs={"accept": ".json,application/json"}),
        help_text=(
            "Если загрузить текущий medical_structure.json из Portal — "
            "сохранятся существующие external_id и коды (без дубликатов)."
        ),
    )


class ImportNativeStructureForm(forms.Form):
    file = forms.FileField(
        label="Файл структуры MedProject (JSON)",
        widget=forms.FileInput(attrs={"accept": ".json,application/json"}),
    )
    clear_tree = forms.BooleanField(
        label="Очистить корпуса/отделения перед импортом",
        required=False,
        initial=False,
        help_text="Удалит все корпуса текущей МО и загрузит дерево заново",
    )
    link_doctors = forms.BooleanField(
        label="Привязывать врачей по doctor_code",
        required=False,
        initial=True,
        help_text="Если врача с таким кодом нет — участок импортируется без врача",
    )
