import os

from qpm.settings import *

DEBUG = True

SECURE_PROXY_SSL_HEADER = None
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
TEMPLATE_DEBUG = DEBUG
SESSION_EXPIRE_AT_BROWSER_CLOSE = True


ROOT_URLCONF = 'qpm.dev.local_urls'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATIC_URL = '/static/'
MEDIA_URL = '/media/'


MEDIA_ROOT = os.path.join(os.environ['HOME'], 'qpm-share-dir', 'qpm','media')
STATIC_ROOT = os.path.join(os.environ['HOME'], 'qpm-share-dir', 'qpm','static')

#AUTHENTICATION_BACKENDS = ('qpm.backends.UserModelEmailBackend',)
AUTHENTICATION_BACKENDS = (
        'qpm.backends.ShibbolethRemoteUserBackend',
        'qpm.backends.UserModelEmailBackend',
        'django.contrib.auth.backends.ModelBackend',
)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True



DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'qpm_prod_dec_15_2021',
        'USER': 'root',
        # 'PASSWORD': 'root',
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

ALLOWED_HOSTS = ['*',]

# EMA_HOST_URL = 'http://127.0.0.1:8001'
