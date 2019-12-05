"""Django settings for tests."""
from __future__ import absolute_import, unicode_literals, division

import os
import sys
import imp

import django

try:
    imp.find_module('grappelli')
except ImportError:
    GRAPPELLI_INSTALLED = False
else:
    GRAPPELLI_INSTALLED = True


BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
SECRET_KEY = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
DEBUG = True


# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'locking',
)

if GRAPPELLI_INSTALLED:
    INSTALLED_APPS = ('grappelli', ) + INSTALLED_APPS

MEDIA_URL = '/media/'   # Avoids https://code.djangoproject.com/ticket/21451

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'tests.urls'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, os.path.pardir, 'assets', 'static'))

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': (
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ),
        }
    },
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}
if 'test' in sys.argv:
    DATABASES['default']['NAME'] = ':memory:'


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCKING_PING_SECONDS = 1
