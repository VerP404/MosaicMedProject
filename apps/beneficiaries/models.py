from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

# Связь с таблицей рецептов из load_data
# from apps.load_data.models import Recipe

class BenefitCategory(models.Model):
    """Категория льготы (федеральная, региональная и т.д.)"""
    name = models.CharField("Название льготной категории", max_length=255, unique=True)
    code = models.CharField("Код категории", max_length=50, blank=True, null=True)
    description = models.TextField("Описание", blank=True, null=True)
    default_coverage_percentage = models.PositiveIntegerField(
        "Процент покрытия по умолчанию",
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=100
    )
    financing_source = models.CharField("Источник финансирования", max_length=255, blank=True)
    is_for_children = models.BooleanField("Для детей", default=False)
    is_active = models.BooleanField("Действует", default=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Льготная категория"
        verbose_name_plural = "Льготные категории"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})" if self.code else self.name


class Patient(models.Model):
    """Пациент-льготник"""
    full_name = models.CharField("ФИО пациента", max_length=255)
    birth_date = models.DateField("Дата рождения пациента")
    snils = models.CharField("СНИЛС пациента", max_length=20, blank=True, null=True, db_index=True)
    enp = models.CharField("ЕНП пациента", max_length=20, blank=True, null=True, db_index=True)
    benefit_category = models.ForeignKey(
        BenefitCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Льготная категория",
        related_name="patients"
    )
    diagnosis_code = models.CharField("Код диагноза", max_length=50, blank=True, null=True)
    diagnosis_name = models.CharField("Название диагноза", max_length=255, blank=True, null=True)
    address = models.TextField("Адрес", blank=True, null=True)
    phone = models.CharField("Телефон", max_length=20, blank=True, null=True)
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Пациент-льготник"
        verbose_name_plural = "Пациенты-льготники"
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name

    @property
    def age(self):
        """Возраст пациента"""
        today = timezone.now().date()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )


class Drug(models.Model):
    """Лекарственный препарат"""
    name = models.CharField("Наименование ЛП", max_length=255)
    inn = models.CharField("МНН/форма выпуска/дозировка", max_length=255, blank=True, null=True)
    code = models.CharField("Код ЛП", max_length=50, blank=True, null=True, db_index=True)
    active_substance = models.CharField("Действующее вещество", max_length=255, blank=True)
    dosage_form = models.CharField("Лекарственная форма", max_length=100, blank=True)
    dosage = models.CharField("Дозировка", max_length=100, blank=True)
    manufacturer = models.CharField("Производитель", max_length=255, blank=True)
    country = models.CharField("Страна производства", max_length=100, blank=True)
    atc_code = models.CharField("АТХ код", max_length=20, blank=True)
    description = models.TextField("Описание", blank=True, null=True)
    is_active = models.BooleanField("Действует", default=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Лекарственный препарат"
        verbose_name_plural = "Лекарственные препараты"
        ordering = ['name']

    def __str__(self):
        return self.name


class PatientDrugSupply(models.Model):
    """Обеспеченность пациента лекарственными препаратами"""
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('active', 'Активно'),
        ('completed', 'Выполнено'),
        ('cancelled', 'Отменено'),
        ('expired', 'Истекло'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="drug_supplies", verbose_name="Пациент")
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name="patient_supplies", verbose_name="Лекарство")
    monthly_need = models.CharField("Месячная потребность", max_length=50)
    dose_regimen = models.CharField("Кратность приёма/дозы", max_length=100, blank=True, null=True)
    prescribed = models.CharField("Выписано", max_length=50, blank=True, null=True)
    prescription_date = models.DateField("Выписан рецепт", blank=True, null=True)
    issue_date = models.DateField("Дата выдачи", null=True, blank=True)
    supplied_until = models.DateField("Обеспечен до", blank=True, null=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='pending')
    doctor_name = models.CharField("ФИО врача", max_length=255, blank=True)
    recipe_number = models.CharField("Номер рецепта", max_length=100, blank=True)
    last_update = models.DateTimeField("Последнее обновление", auto_now=True)
    note = models.TextField("Примечание", blank=True, null=True)

    class Meta:
        verbose_name = "Обеспеченность пациента ЛП"
        verbose_name_plural = "Обеспеченность пациентов ЛП"
        unique_together = ("patient", "drug")

    def __str__(self):
        return f"{self.patient} — {self.drug}"
    
    @property
    def days_remaining(self):
        """Количество дней до окончания препарата"""
        if not self.supplied_until:
            return None
        today = timezone.now().date()
        delta = self.supplied_until - today
        return delta.days
    
    @property
    def is_urgent(self):
        """Проверка срочности (осталось менее 7 дней)"""
        days = self.days_remaining
        return days is not None and 0 <= days <= 7
    
    @property
    def is_expired(self):
        """Проверка истечения препарата"""
        if not self.supplied_until:
            return False
        return self.supplied_until < timezone.now().date()


class DrugStock(models.Model):
    """Остатки лекарственных препаратов на складе"""
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
