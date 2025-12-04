from django.db import models


class GarAddress(models.Model):
    """
    Модель для хранения адресных данных из ГАР (Государственный адресный реестр)
    Основные таблицы ГАР: ADDR_OBJ, HOUSES, APARTMENTS
    """
    # Иерархия адреса
    region_code = models.CharField(max_length=2, db_index=True, verbose_name="Код региона")
    area = models.CharField(max_length=255, blank=True, null=True, db_index=True, verbose_name="Район")
    city = models.CharField(max_length=255, blank=True, null=True, db_index=True, verbose_name="Город")
    settlement = models.CharField(max_length=255, blank=True, null=True, verbose_name="Населенный пункт")
    street = models.CharField(max_length=255, blank=True, null=True, db_index=True, verbose_name="Улица")
    house = models.CharField(max_length=50, blank=True, null=True, verbose_name="Дом")
    apartment = models.CharField(max_length=50, blank=True, null=True, verbose_name="Квартира")
    
    # Дополнительные данные
    postal_code = models.CharField(max_length=10, blank=True, null=True, verbose_name="Почтовый индекс")
    full_address = models.TextField(blank=True, null=True, verbose_name="Полный адрес")
    
    # ГАР идентификаторы
    gar_object_id = models.BigIntegerField(unique=True, db_index=True, verbose_name="ID объекта ГАР")
    parent_id = models.BigIntegerField(null=True, blank=True, db_index=True, verbose_name="ID родительского объекта")
    object_level = models.IntegerField(null=True, blank=True, verbose_name="Уровень объекта")
    
    # Метаданные
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")
    
    class Meta:
        verbose_name = "Адрес ГАР"
        verbose_name_plural = "Адреса ГАР"
        indexes = [
            models.Index(fields=['region_code', 'city', 'street']),
            models.Index(fields=['gar_object_id']),
            models.Index(fields=['parent_id']),
        ]
    
    def __str__(self):
        parts = [p for p in [self.area, self.city, self.settlement, self.street, self.house, self.apartment] if p]
        return ', '.join(parts) if parts else f"Адрес #{self.gar_object_id}"


class GarLoadHistory(models.Model):
    """
    История загрузок данных ГАР
    """
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('processing', 'Обрабатывается'),
        ('completed', 'Завершена'),
        ('failed', 'Ошибка'),
    ]
    
    region_code = models.CharField(max_length=2, verbose_name="Код региона")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    records_loaded = models.IntegerField(default=0, verbose_name="Загружено записей")
    records_total = models.IntegerField(null=True, blank=True, verbose_name="Всего записей")
    
    source_file = models.CharField(max_length=500, blank=True, null=True, verbose_name="Исходный файл")
    output_file = models.CharField(max_length=500, blank=True, null=True, verbose_name="Выходной файл")
    
    error_message = models.TextField(blank=True, null=True, verbose_name="Сообщение об ошибке")
    
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Начало загрузки")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Окончание загрузки")
    
    class Meta:
        verbose_name = "История загрузки ГАР"
        verbose_name_plural = "История загрузок ГАР"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Загрузка региона {self.region_code} - {self.get_status_display()}"

