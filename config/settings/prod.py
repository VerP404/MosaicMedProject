from .base import *

# Настройки для продакшена
DEBUG = False
LOGGING['root']['level'] = 'DEBUG'

# ВАЖНО: Для обслуживания статических файлов в продакшене
# В реальном продакшене используйте nginx/Apache, но для разработки можно использовать Django
SERVE_STATIC = True  # Добавляем флаг для обслуживания статических файлов

# Настройки для статических файлов в продакшене
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Для обслуживания статических файлов в продакшене
# В реальном продакшене используйте nginx или Apache для статических файлов
# Но для разработки можно использовать Django
from django.conf.urls.static import static
from django.conf import settings

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('Name'),
        'USER': env('USER'),
        'PASSWORD': env('PASSWORD'),
        'HOST': env('HOST'),
        'PORT': env('PORT'),
    }
}

INSTALLED_APPS += [
    'debug_toolbar',

    'apps.personnel',
    'apps.organization',
    'apps.oms_reference',
    'apps.sql_manager',
    'apps.reports',

    'dal',
    'dal_select2',

]
MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]
INTERNAL_IPS = [
    '127.0.0.1',
]

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

X_FRAME_OPTIONS = 'SAMEORIGIN'  # Использовать X-Frame-Options в браузере для Django-dash
PLOTLY_DASH = {
    "ws_route": "ws/channel",  # Если планируете использовать WebSockets
    "http_route": "dash/app",  # Путь для Dash-приложения
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'celery_debug.log'),  # Корректный путь для Windows
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        '': {  # Корневой логгер
            'handlers': ['console', 'file'],
            'level': 'DEBUG',  # Ставим DEBUG для всех логгеров
        },
    },
}
