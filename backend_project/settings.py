"""
Django settings for backend_project project.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================
# SEGURIDAD
# ==============================
SECRET_KEY = 'django-insecure-kjjoj+*2ro8wmv)*@=bpahju2i%avd)dyq0+6btr9fn8+ah5@*'
DEBUG = True
ALLOWED_HOSTS = []

# ==============================
# APPS
# ==============================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    

    # terceros
    'rest_framework',
    'corsheaders',

    # locales
    'accounts',
    'courses',
    'assignments',
    'notifications',
]

# ==============================
# MIDDLEWARE
# ==============================
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

ROOT_URLCONF = 'backend_project.urls'

# ==============================
# TEMPLATES
# ==============================
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

WSGI_APPLICATION = 'backend_project.wsgi.application'

# ==============================
# DATABASE
# ==============================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gimnasio',
        'USER': 'postgres',
        'PASSWORD': 'cafune123',
        'HOST': 'localhost',
        'PORT': '5434',
    }
}

# ==============================
# CORS
# ==============================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200",
    "http://localhost:5173",
]

# ==============================
# AUTH USER
# ==============================
AUTH_USER_MODEL = 'accounts.User'

# ==============================
# PASSWORD VALIDATORS
# ==============================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==============================
# INTERNACIONALIZACIÓN
# ==============================
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# ==============================
# GOOGLE OAUTH
# ⚠️ REEMPLAZA POR EL REAL
# ==============================
GOOGLE_CLIENT_ID = "509271286435-fpgfh78rc1vunkjpeatolrndho8cn96t.apps.googleusercontent.com"

# ==============================
# STATIC & MEDIA
# ==============================
STATIC_URL = 'static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================
# DRF + JWT
# ==============================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

# ==============================
# EMAIL
# ==============================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'branfer60@gmail.com'
EMAIL_HOST_PASSWORD = 'bnla xiox mgzh wjue'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER