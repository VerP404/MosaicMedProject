from .base import *

LOGGING['root']['level'] = 'DEBUG'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
    }
}

INSTALLED_APPS += [
    'debug_toolbar',
    'import_export',
    'django_plotly_dash.apps.DjangoPlotlyDashConfig',

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
