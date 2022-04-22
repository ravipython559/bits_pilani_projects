"""
Django settings for qpm project.

Generated by 'django-admin startproject' using Django 3.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure--%43lo6@wl-ffsa*l+_$a=b9gx!(19emd3mn4o-1i2)xff850i'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
TEMPLATE_DEBUG = DEBUG
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Application definition

INSTALLED_APPS = [
    'import_export',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'master',
    'faculty',
    'coordinator',
    'bootstrap3',
    'administrator',
    'table',
    'django_extensions',
    'django_celery_results',
    'shibboleth',
    'rest_framework',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'shibboleth.middleware.ShibbolethRemoteUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'qpm.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'),],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'shibboleth.context_processors.login_link',
                'shibboleth.context_processors.logout_link',
            ],
        },
    },
]

WSGI_APPLICATION = 'qpm.wsgi.application'


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'qpm_2',
        'USER': 'root',
        'PASSWORD': 'P@ssw0rd',
        # 'HOST': '192.168.1.35',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES', innodb_strict_mode=1",
            'charset': 'utf8mb4',
        },
        'TEST': {
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_unicode_ci',
        },
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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

#bits mail settings
EMAIL_USE_TLS = True

EMAIL_HOST = 'smtp-wilp.bits-pilani.ac.in'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'ema-2021-03-01@wilp.bits-pilani.ac.in'
EMAIL_HOST_PASSWORD = '65ee4d69-b963-460e-b512-f87d370bb638'
FROM_EMAIL = 'noreply@wilp.bits-pilani.ac.in'

#EMAIL_HOST = 'smtp.parinati.in'
#EMAIL_PORT = 587
#EMAIL_HOST_USER = 'shivakrishna.konanki@parinati.in'
#EMAIL_HOST_PASSWORD = 'shivakrishna@8722'
#FROM_EMAIL = 'shivakrishna.konanki@parinati.in'

#Shibboleth
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'qpm.backends.ShibbolethRemoteUserBackend',
)

SHIBBOLETH_ATTRIBUTE_MAP = {
    'cname': (True, 'username'),
    'uid': (True, 'email'),
    'role': (True, 'role'),
}
LOGIN_URL = '/Shibboleth.sso/Login'
SHIBBOLETH_LOGOUT_URL = '/Shibboleth.sso/Logout'
SHIBBOLETH_LOGOUT_REDIRECT_URL = 'https://elearn.bits-pilani.ac.in/user/'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True 

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

from pytz import timezone as indiantime
INDIAN_TIME_ZONE = indiantime('Asia/Kolkata')
TIME_ZONE = INDIAN_TIME_ZONE.zone

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/


DEFAULT_FILE_STORAGE = 'qpm.storage.MediaStorage'
# STATICFILES_STORAGE = 'bits.bits_storage.StaticStorage'
AWS_ACCESS_KEY_ID = 'AKIAI2VBEJAEPIDKWYFQ'
AWS_SECRET_ACCESS_KEY = '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'
AWS_STORAGE_BUCKET_NAME = 'qpm-application-bucket'
AWS_QUERYSTRING_AUTH = False
S3_USE_SIGV4 = True
AWS_REGION_NAME = 'ap-south-1'
AWS_S3_CUSTOM_DOMAIN = '{0}.s3.amazonaws.com'.format(AWS_STORAGE_BUCKET_NAME)
AWS_S3_STORAGE = 's3'

S3_URL = '{0}.s3.ap-south-1.amazonaws.com'.format(AWS_STORAGE_BUCKET_NAME)
S3_MEDIA_DIR = 'media'

# PROJECT_DIR = os.path.dirname(BASE_DIR)
# MEDIA_ROOT = os.path.join(PROJECT_DIR, 'qpm','media')
MEDIA_URL = 'https://{0}/{1}/'.format(S3_URL, S3_MEDIA_DIR)
STATIC_URL = '/static/'

# MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(os.environ['HOME'], 'qpm-share-dir', 'qpm','media')
STATIC_ROOT = os.path.join(os.environ['HOME'], 'qpm-share-dir', 'qpm','static')
STATICFILES_DIRS = (os.path.join(BASE_DIR, "qpm", "static"), )

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CELERY_RESULT_BACKEND = 'django-db'

CELERY_BROKER_URL = 'redis://localhost:6379/0'

CELERY_TIMEZONE = indiantime('Asia/Kolkata').zone
CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'
# CELERY_IMPORTS=("master.tasks")
EMA_HOST_URL = 'https://exam-mgmt.bits-pilani.ac.in'