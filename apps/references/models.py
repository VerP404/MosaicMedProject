from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone

# Create your models here.

class MKB10(models.Model):
    code = models.CharField(
        "Код МКБ-10",
        max_length=16,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]\d{2}(\.\d{1,2})?$',
                message='Код должен соответствовать формату МКБ-10 (например: A01.1)'
            )
        ]
    )
    name = models.CharField("Наименование", max_length=512)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children', verbose_name="Родительский код")
    level = models.PositiveIntegerField("Уровень иерархии", default=1)
    is_active = models.BooleanField("Активен", default=True)
    is_final = models.BooleanField("Конечный диагноз", default=False)
    description = models.TextField("Описание/Примечание", blank=True, null=True)
    created_at = models.DateTimeField("Дата создания", default=timezone.now)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "МКБ-10: диагноз"
        verbose_name_plural = "МКБ-10: диагнозы"
        ordering = ["code"]
        unique_together = ("code", "parent")
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"

    def get_full_path(self):
        """Возвращает полный путь диагноза в иерархии"""
        path = [self.code]
        current = self.parent
        while current:
            path.append(current.code)
            current = current.parent
        return ' / '.join(reversed(path))

    def get_children_count(self):
        """Возвращает количество дочерних элементов"""
        return self.children.count()

    def save(self, *args, **kwargs):
        if self.parent:
            self.level = self.parent.level + 1
        self.is_final = not self.children.exists()
        super().save(*args, **kwargs)

class InsuranceCompany(models.Model):
    """Страховая медицинская организация (СМО)"""
    tf_okato = models.CharField('ОКАТО', max_length=5)
    smocod = models.CharField('Код СМО', max_length=5)
    nam_smop = models.CharField('Полное наименование', max_length=255)
    nam_smok = models.CharField('Краткое наименование', max_length=255)
    inn = models.CharField('ИНН', max_length=12)
    ogrn = models.CharField('ОГРН', max_length=13)
    kpp = models.CharField('КПП', max_length=9)
    
    # Юридический адрес
    jur_address_index = models.CharField('Индекс юр. адреса', max_length=6)
    jur_address = models.TextField('Юридический адрес')
    
    # Почтовый адрес
    pst_address_index = models.CharField('Индекс почт. адреса', max_length=6)
    pst_address = models.TextField('Почтовый адрес')
    
    okopf = models.CharField('ОКОПФ', max_length=5)
    
    # Руководитель
    head_lastname = models.CharField('Фамилия руководителя', max_length=100)
    head_firstname = models.CharField('Имя руководителя', max_length=100)
    head_middlename = models.CharField('Отчество руководителя', max_length=100)
    
    # Контакты
    phone = models.CharField('Телефон', max_length=20)
    fax = models.CharField('Факс', max_length=20)
    hot_line = models.CharField('Горячая линия', max_length=20)
    email = models.EmailField('Email')
    website = models.URLField('Сайт', blank=True, null=True)
    
    # Лицензия
    license_number = models.CharField('Номер лицензии', max_length=20)
    license_start_date = models.DateField('Дата начала лицензии')
    license_end_date = models.DateField('Дата окончания лицензии')
    
    # Дополнительная информация
    org_type = models.CharField('Тип организации', max_length=2)
    is_active = models.BooleanField('Активна', default=True)
    is_default = models.BooleanField('СМО по умолчанию', default=False)
    
    # Статистика
    year_work = models.IntegerField('Год работы')
    last_update = models.DateField('Дата последнего обновления')
    insured_count = models.IntegerField('Количество застрахованных')
    
    created_at = models.DateTimeField('Дата создания', default=timezone.now)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Страховая медицинская организация'
        verbose_name_plural = 'Страховые медицинские организации'
        ordering = ['nam_smok']
        indexes = [
            models.Index(fields=['smocod']),
            models.Index(fields=['inn']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_default']),
        ]

    def __str__(self):
        return f"{self.nam_smok} ({self.smocod})"

    def save(self, *args, **kwargs):
        # Если устанавливаем СМО по умолчанию, сбрасываем флаг у других
        if self.is_default:
            InsuranceCompany.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
