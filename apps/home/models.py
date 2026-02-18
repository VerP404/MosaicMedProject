from django.db import models


class MainSettings(models.Model):
    dash_ip = models.GenericIPAddressField(default='127.0.0.1')
    dash_port = models.PositiveIntegerField(default=5000)
    main_app_ip = models.GenericIPAddressField(default='127.0.0.1')
    main_app_port = models.PositiveIntegerField(default=8000)
    dash_chief_ip = models.GenericIPAddressField(default='127.0.0.1')
    dash_chief_port = models.PositiveIntegerField(default=5010)
    kauz_server_ip = models.GenericIPAddressField(default='127.0.0.1', verbose_name="КАУЗ: IP сервера")
    kauz_database_path = models.CharField(max_length=255, default='-', verbose_name="КАУЗ: Путь к базе данных")
    kauz_port = models.PositiveIntegerField(default=3050, verbose_name="КАУЗ: Порт")
    kauz_user = models.CharField(max_length=255, default='-', verbose_name="КАУЗ: Пользователь")
    kauz_password = models.CharField(max_length=255, default='-', verbose_name="КАУЗ: Пароль")
    api_panel_patients_url = models.URLField(
        max_length=500,
        default='http://10.37.170.101:8000/peopledash/api/registered_patients/',
        verbose_name="URL для обновления панели пациентов"
    )
    api_update_registry_not_hospitalize_url = models.URLField(
        max_length=500,
        default='http://10.37.170.101:8000/api/patient_registry/',
        verbose_name="URL для обновления реестра не госпитализированных пациентов"
    )
    # Поля для Dagster
    dagster_ip = models.GenericIPAddressField(default='127.0.0.1', verbose_name="Dagster IP")
    dagster_port = models.PositiveIntegerField(default=3000, verbose_name="Dagster Port")
    # Поля для FileBrowser
    filebrowser_ip = models.GenericIPAddressField(default='127.0.0.1', verbose_name="FileBrowser IP")
    filebrowser_port = models.PositiveIntegerField(default=8080, verbose_name="FileBrowser Port")

    def get_dash_url(self):
        return f"http://{self.dash_ip}:{self.dash_port}"

    def get_dash_chief_url(self):
        return f"http://{self.dash_chief_ip}:{self.dash_chief_port}"

    def get_filebrowser_url(self):
        return f"http://{self.filebrowser_ip}:{self.filebrowser_port}"

    def __str__(self):
        return (f"Аналитическая система - {self.dash_ip}:{self.dash_port}, "
                f"Основное приложение - {self.main_app_ip}:{self.main_app_port}, "
                f"Панель главного врача - {self.dash_chief_ip}:{self.dash_chief_port}, "
                f"Dagster - {self.dagster_ip}:{self.dagster_port}, "
                f"FileBrowser - {self.filebrowser_ip}:{self.filebrowser_port}")

    class Meta:
        verbose_name = "Настройка"
        verbose_name_plural = "Настройки"


class TelegramBot(models.Model):
    name = models.CharField("Название бота", max_length=100)
    alias = models.CharField("Псевдоним", max_length=50, unique=True, help_text="Уникальный идентификатор бота")
    bot_id = models.CharField("ID бота", max_length=100, unique=True)
    token = models.CharField("Токен/Пароль бота", max_length=255)
    additional_password = models.CharField("Дополнительный пароль", max_length=255, blank=True, null=True)

    # При необходимости можно связать бота с конкретными настройками:
    # settings = models.ForeignKey(MainSettings, on_delete=models.CASCADE, related_name='telegram_bots', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Телеграм бот"
        verbose_name_plural = "Телеграм боты"


class TelegramGroup(models.Model):
    bot = models.ForeignKey(
        TelegramBot,
        on_delete=models.CASCADE,
        related_name='groups',
        verbose_name="Бот"
    )
    group_id = models.CharField("ID группы", max_length=100, unique=True)
    name = models.CharField("Название группы", max_length=100)
    description = models.TextField("Описание группы", blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.group_id})"

    class Meta:
        verbose_name = "Телеграм группа"
        verbose_name_plural = "Телеграм группы"


class MenuItem(models.Model):
    """Пункт меню в боковой панели. Управление видимостью в админке."""
    ICON_FEATHER = 'feather'
    ICON_FA = 'fa'
    ICON_CHOICES = [
        (ICON_FEATHER, 'Feather (data-feather)'),
        (ICON_FA, 'Font Awesome (класс)'),
    ]

    title = models.CharField('Название', max_length=100)
    link = models.CharField(
        'Ссылка',
        max_length=255,
        blank=True,
        help_text='Имя URL (например: home, beneficiaries:home), путь (/admin/) или спец. код: dash_url, dash_chief_url, dash_update'
    )
    icon_type = models.CharField('Тип иконки', max_length=10, choices=ICON_CHOICES, default=ICON_FEATHER)
    icon_name = models.CharField('Иконка', max_length=50, blank=True, help_text='Например: home, bar-chart-2 или fa-heart-pulse')
    order = models.PositiveSmallIntegerField('Порядок', default=0)
    is_visible = models.BooleanField('Показывать', default=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Родитель (для подменю)'
    )
    slug = models.SlugField(
        'Идентификатор (для выпадающего блока)',
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text='Латиница без пробелов, например: patient-registries (для пунктов с подменю)'
    )

    class Meta:
        verbose_name = 'Пункт меню'
        verbose_name_plural = 'Пункты меню'
        ordering = ['order', 'pk']

    def __str__(self):
        return self.title
