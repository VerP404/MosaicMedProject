from django.db import models


class Building(models.Model):
    name = models.CharField(max_length=250, unique=True,
                            verbose_name='Названия корпуса для группировки подразделений из Статистики Квазар')

    class Meta:
        verbose_name = "Корпус"
        verbose_name_plural = "Корпуса"

    def __str__(self):
        return self.name


class Subdivision(models.Model):
    name = models.CharField(max_length=500, unique=True)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='subdivisions')

    class Meta:
        verbose_name = "Подразделение"
        verbose_name_plural = "Подразделения"

    def __str__(self):
        return self.name


class Specialty(models.Model):
    name = models.CharField(max_length=500, unique=True)

    class Meta:
        verbose_name = "Специальность"
        verbose_name_plural = "Специальности"

    def __str__(self):
        return self.name


class Page(models.Model):
    title = models.CharField(max_length=250,
                             verbose_name='Заголовок. Показывает то что будет написано в списке подразделений на главной странице')
    path = models.CharField(max_length=250, unique=True,
                            verbose_name='Путь отображаемый в браузерной ссылке на страницу(на английском)')
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='pages',
                                 verbose_name='Подключаем созданный корпус к страницу для отображения')
    subdivision = models.CharField(max_length=250,
                                   verbose_name='Подпись на странице корпуса. Должно быть такое же как и в подключенном корпусе выше!')

    class Meta:
        verbose_name = "Страница"
        verbose_name_plural = "Страницы"

    def __str__(self):
        return self.title


class TodayData(models.Model):
    organization = models.CharField(max_length=255)
    subdivision = models.CharField(max_length=255)
    speciality = models.CharField(max_length=255)
    doctor_name = models.CharField(max_length=255)
    reception_type = models.CharField(max_length=255)
    total_slots = models.IntegerField()
    epgu_slots = models.IntegerField()
    free_slots = models.IntegerField()
    free_epgu_slots = models.IntegerField()
    report_datetime = models.DateTimeField()

    class Meta:
        verbose_name = "Данные за сегодня"
        verbose_name_plural = "Данные за сегодня"


class FourteenDaysData(models.Model):
    organization = models.CharField(max_length=255)
    subdivision = models.CharField(max_length=255)
    speciality = models.CharField(max_length=255)
    doctor_name = models.CharField(max_length=255)
    reception_type = models.CharField(max_length=255)
    total_slots = models.IntegerField()
    epgu_slots = models.IntegerField()
    free_slots = models.IntegerField()
    free_epgu_slots = models.IntegerField()
    report_datetime = models.DateTimeField()

    class Meta:
        verbose_name = "Данные за 14 дней"
        verbose_name_plural = "Данные за 14 дней"


class RegisteredPatients(models.Model):
    subdivision = models.CharField(max_length=255)
    speciality = models.CharField(max_length=255)
    slots_today = models.IntegerField()
    free_slots_today = models.IntegerField()
    slots_14_days = models.IntegerField()
    free_slots_14_days = models.IntegerField()
    report_datetime = models.CharField(max_length=50, default='-')
    organization = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Загруженные данные"
        verbose_name_plural = "Загруженные данные"

    def __str__(self):
        return f"{self.subdivision} - {self.speciality}"


class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True,
                            verbose_name='Название из файла Статистики Квазар для фильтрации')
    full_name = models.CharField(max_length=255, verbose_name='Название для отображения в заголовке дашборда')
    logo = models.ImageField(upload_to='organization_logos/', verbose_name='Логотип')
    # Кастомизация страниц
    background_color = models.CharField(max_length=7, default='#4c4bc0', verbose_name='Цвет фона сайта')
    text_color = models.CharField(max_length=7, default='white', verbose_name='Цвет текста в таблицах и блоке header')
    main_container_color = models.CharField(max_length=7, default='#1f2c56',
                                            verbose_name='Цвет фона контейнера с данными')
    info_container_color = models.CharField(max_length=7, default='#1f2c56',
                                            verbose_name='Цвет фона контейнера с доп. информацией')
    info_container_texy_color = models.CharField(max_length=7, default='#02ff35',
                                                 verbose_name='Цвет текста контейнера с доп. информацией')
    header_background_color = models.CharField(max_length=7, default='#3fa134',
                                               verbose_name='Цвет текста названий таблиц')
    table_header_color = models.CharField(max_length=7, default='red', verbose_name='Цвет заголовков таблиц')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Организация'
        verbose_name_plural = 'Организация'
