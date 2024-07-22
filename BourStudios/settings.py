"""
Django settings for BourStudios project.

Generated by 'django-admin startproject' using Django 5.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path
import os
import environ
import dj_database_url

env = environ.Env()
environ.Env.read_env()
ENVIRONMENT= env('ENVIRONMENT')

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = os.path.join(BASE_DIR, 'galsen/templates')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')
# SECURITY WARNING: don't run with debug turned on in production!
if ENVIRONMENT == 'development':
    DEBUG = True
else:
    DEBUG = False

ALLOWED_HOSTS = ['.vercel.app', '127.0.0.1']

AUTH_USER_MODEL = 'galsen.CustomUser'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'galsen',
    # 'pwa',
    'rest_framework',
    #'admin_honeypot',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'galsen.middleware.MarqueDispositifMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

ROOT_URLCONF = 'BourStudios.urls'

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_DIR, os.path.join(BASE_DIR, 'templates')], # Ajoutez le chemin vers le dossier templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'BourStudios.wsgi.app'

# settings.py
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # Par défaut
    'galsen.backends.EmailBackend',  # Ajustez le nom de votre application et de votre fichier
]


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        # 'ENGINE': 'django.db.backends.postgresql',
        # 'URL': os.environ.get('DATABASE_URL'),
        # 'NAME': os.environ.get('PGDATABASE'),
        # 'USER': os.environ.get('PGUSER'),
        # 'PASSWORD': os.environ.get('PGPASSWORD'),
        # 'HOST': os.environ.get('PGHOST'),
        # 'PORT': os.environ.get('PGPORT'),
    }
}

# POSTGRES_LOCALLY = False
# if ENVIRONMENT =='production' or POSTGRES_LOCALLY == True:
#     DATABASES['default'] = dj_database_url.parse(env("DATABASE_URL"))

 
# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'fr'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


#Django envoie Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST ="smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/galsen/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'galsen/static')]
MEDIA_URL = '/galsen/images/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'galsen/images/')

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Configuration django pwa
# PWA_APP_NAME = "Galsem"
# PWA_APP_DESCRIPTION = "environnement Professionnel"
# PWA_APP_THEME_COLOR = "#007bff"
# PWA_APP_BACKGROUND_COLOR = "#ffffff"
# PWA_APP_DISPLAY = 'standalone'
# PWA_APP_SCOPE = '/'
# PWA_APP_ORIENTATION = 'portrait'
# PWA_APP_START_URL = '/'
# PWA_APP_ICONS = [
#     {
#         'src': '/static/assets/logo/galsen.jpg',
#         'sizes': '160x160'
#     }
# ]
# PWA_APP_ICONS_APPLE = [
#     {
#         'src': '/static/assets/logo/galsen.jpg',
#         'sizes': '160x160'
#     }
# ]
# PWA_SERVICE_WORKER_PATH = os.path.join(BASE_DIR, 'static/assets/ressources/pwa_js', 'serviceworker.js')

ACCOUNT_USERNAME_BLACKLIST =['admin', 'accounts', 'profile', 'poste', 'post','ecol', 'bandit']