import os
from pathlib import Path
import environ
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env(
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY', default='default-secret-key')
DEBUG = env.bool('DEBUG_DJ')
DEBUG_DASH = env.bool('DEBUG_DASH')
PORT_DASH = env.int('PORT_DASH', default=5000)
PORT_DASH_CHIEF = env.int('PORT_DASH_CHIEF', default=5001)

ALLOWED_HOSTS = ['*']

# Редиректы после аутентификации
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

INSTALLED_APPS = [
    'unfold',
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "unfold.contrib.import_export",
    "unfold.contrib.guardian",
    "unfold.contrib.simple_history",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 'apps.custom_auth',
    'apps.home',
    'apps.data_loader',
    'apps.peopledash',
    'apps.people',
    'apps.plan',
    'apps.api',
    'apps.data',
    'apps.load_data',
    'apps.journal',
    'apps.person',
    'apps.talon',
    'apps.dn_app',
    'apps.beneficiaries',
    'apps.references',


    'import_export',
    'channels',
    'rest_framework',
    'django_json_widget'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.home.context_processors.portal_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True
USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Логирование
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

MEDIA_URL = '/uploads/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads/')

ASGI_APPLICATION = 'config.asgi.application'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# Для того чтобы при экспорте выводились чекбоксы полей
EXPORT_RESOURCE_FIELDS = True

# При импорте/экспорте в транзакции
IMPORT_EXPORT_USE_TRANSACTIONS = True

# Настройка Дагстер.
# Получаем значение из .env (относительный путь)
relative_dagster_home = os.getenv('DAGSTER_HOME', 'mosaic_conductor/dagster_home')
# Преобразуем его в абсолютный путь
absolute_dagster_home = BASE_DIR / relative_dagster_home
# Обновляем переменную окружения
os.environ['DAGSTER_HOME'] = str(absolute_dagster_home)
# для работы с дагстером загрузки в базу данных
ORGANIZATIONS = os.environ.get('ORGANIZATIONS', 'МозаикаМед')

# Настройка Unfold: аккуратный сайдбар с группами и сворачиваемыми разделами
UNFOLD = {
    "SITE_TITLE": "Панель МозаикаМед",
    "SITE_HEADER": "Панель МозаикаМед",
    "SITE_SUBHEADER": ORGANIZATIONS,
    "SITE_URL": "/",
    "DASHBOARD_CALLBACK": "config.dashboard.dashboard_callback",
    "SIDEBAR": {
        "show_search": False,
        "command_search": False,
        # Показываем выпадающий список со всеми приложениями по умолчанию
        "show_all_applications": True,
        # Основная навигация и группы приложений
        "navigation": [
            {
                "title": _("Навигация"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Главная админки"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": _("Доступ"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("Пользователи"),
                        "icon": "person",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                    },
                    {
                        "title": _("Группы"),
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
            {
                "title": _("Настройки системы"),
                "collapsible": True,
                "items": [
                    {"title": "Система", "icon": "settings", "link": "/admin/home/"},
                ],
            },
            {
                "title": _("Кадры"),
                "collapsible": True,
                "items": [
                    {"title": "Сотрудники", "icon": "settings", "link": "/admin/personnel/"},
                    {"title": "Организация", "icon": "domain", "link": "/admin/organization/"},
                ],
            },
            {
                "title": _("Пациенты и население"),
                "collapsible": True,
                "items": [
                    {"title": "Население (ИСЗЛ)", "icon": "groups", "link": "/admin/people/"},
                    {"title": "Персоны", "icon": "person_search", "link": "/admin/person/"},
                ],
            },
            {
                "title": _("Льготное лекарственное обеспечение"),
                "collapsible": True,
                "items": [
                    {"title": "Льготники", "icon": "medication", "link": "/admin/beneficiaries/"},
                ],
            },
            {
                "title": _("ОМС и талоны"),
                "collapsible": True,
                "items": [
                    {"title": "Талоны ОМС", "icon": "assignment", "link": "/admin/talon/"},
                    {"title": "Справочники ОМС", "icon": "menu_book", "link": "/admin/oms_reference/"},
                ],
            },
            {
                "title": _("Данные и загрузка"),
                "collapsible": True,
                "items": [
                    {"title": "Оперативные данные", "icon": "table", "link": "/admin/data/"},
                    {"title": "Загрузка данных", "icon": "history", "link": "/admin/load_data/"},
                    {"title": "Загрузчики", "icon": "upload", "link": "/admin/data_loader/"},
                    {"title": "SQL-конструктор", "icon": "dataset", "link": "/admin/sql_manager/"},
                ],
            },
            {
                "title": _("Диспансерное наблюдение"),
                "collapsible": True,
                "items": [
                    {"title": "ДН-модуль", "icon": "monitor_heart", "link": "/admin/dn_app/"},
                ],
            },
            {
                "title": _("Планирование"),
                "collapsible": True,
                "items": [
                    {"title": "План", "icon": "event_note", "link": "/admin/plan/"},
                ],
            },
            {
                "title": _("Отчёты и журналы"),
                "collapsible": True,
                "items": [
                    {"title": "Отчёты", "icon": "bar_chart", "link": "/admin/reports/"},
                    {"title": "Обращения граждан", "icon": "article", "link": "/admin/journal/"},
                ],
            },
            {
                "title": _("Справочники"),
                "collapsible": True,
                "items": [
                    {"title": "Общие справочники", "icon": "library_books", "link": "/admin/references/"},
                ],
            },
        ],
    },
}
