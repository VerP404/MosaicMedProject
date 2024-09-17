from .base import *

DEBUG = True
LOGGING['root']['level'] = 'DEBUG'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
INSTALLED_APPS += [
    'debug_toolbar',
    'apps.data_loader'
]
MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]
