"""Configuración del servidor de Bus Portoviejo.

Los valores sensibles salen de variables de entorno. Los que vienen por defecto
sirven solo para desarrollo en la computadora de cada uno.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# En producción se define DJANGO_SECRET_KEY. Esta clave solo sirve para desarrollo.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'solo-para-desarrollo-no-usar-en-produccion')
DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1'

# En desarrollo se acepta cualquier host, para que el celular entre por la IP de la computadora.
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*' if DEBUG else '').split(',')

INSTALLED_APPS = [
    'daphne',                       # servidor ASGI: tiene que ir antes de staticfiles
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'channels',
    'transporte',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Para la demo basta la capa en memoria (un solo proceso, sin Redis). Redis llega en la fase 9.
CHANNEL_LAYERS = {
    'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'},
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-ec'
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# La app móvil no usa cookies, así que en desarrollo se acepta cualquier origen.
CORS_ALLOW_ALL_ORIGINS = DEBUG

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer']
    + (['rest_framework.renderers.BrowsableAPIRenderer'] if DEBUG else []),
}
