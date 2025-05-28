from django.db import models
from django.conf import settings

# Create your models here.

class BenefitCategory(models.Model):
    name = models.CharField("Название льготной категории", max_length=255, unique=True)
    code = models.CharField("Код категории", max_length=50, blank=True, null=True)
    description = models.TextField("Описание", blank=True, null=True)
    is_active = models.BooleanField("Действует", default=True)

    class Meta:
        verbose_name = "Льготная категория"
        verbose_name_plural = "Льготные категории"

    def __str__(self):
        return f"{self.name} ({self.code})" if self.code else self.name


class Patient(models.Model):
    full_name = models.CharField("ФИО пациента", max_length=255)
    birth_date = models.DateField("Дата рождения пациента")
    snils = models.CharField("СНИЛС пациента", max_length=20, blank=True, null=True)
    enp = models.CharField("ЕНП пациента", max_length=20, blank=True, null=True)
    benefit_category = models.ForeignKey(BenefitCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Льготная категория")
    diagnosis_code = models.CharField("Код диагноза", max_length=50, blank=True, null=True)
    diagnosis_name = models.CharField("Название диагноза", max_length=255, blank=True, null=True)
    address = models.TextField("Адрес", blank=True, null=True)
    phone = models.CharField("Телефон", max_length=20, blank=True, null=True)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Пациент"
        verbose_name_plural = "Пациенты"
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name


class Drug(models.Model):
    name = models.CharField("Наименование ЛП", max_length=255)
    inn = models.CharField("МНН/форма выпуска/дозировка", max_length=255, blank=True, null=True)
    code = models.CharField("Код ЛП", max_length=50, blank=True, null=True)
    description = models.TextField("Описание", blank=True, null=True)
    is_active = models.BooleanField("Действует", default=True)

    class Meta:
        verbose_name = "Лекарственный препарат"
        verbose_name_plural = "Лекарственные препараты"

    def __str__(self):
        return self.name


class PatientDrugSupply(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="drug_supplies", verbose_name="Пациент")
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name="patient_supplies", verbose_name="Лекарство")
    monthly_need = models.CharField("Месячная потребность", max_length=50)
    dose_regimen = models.CharField("Кратность приёма/дозы", max_length=100, blank=True, null=True)
    prescribed = models.CharField("Выписано", max_length=50, blank=True, null=True)
    prescription_date = models.DateField("Выписан рецепт", blank=True, null=True)
    supplied_until = models.DateField("Обеспечен до", blank=True, null=True)
    last_update = models.DateTimeField("Последнее обновление", auto_now=True)
    note = models.TextField("Примечание", blank=True, null=True)

    class Meta:
        verbose_name = "Обеспеченность пациента ЛП"
        verbose_name_plural = "Обеспеченность пациентов ЛП"
        unique_together = ("patient", "drug")

    def __str__(self):
        return f"{self.patient} — {self.drug}"


class DrugStock(models.Model):
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name="stocks", verbose_name="Лекарство")
    quantity = models.PositiveIntegerField("Остаток (ед.)", default=0)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)
    note = models.TextField("Примечание", blank=True, null=True)

    class Meta:
        verbose_name = "Остаток ЛП"
        verbose_name_plural = "Остатки ЛП"
        unique_together = ("drug",)

    def __str__(self):
        return f"{self.drug}: {self.quantity} ед."
