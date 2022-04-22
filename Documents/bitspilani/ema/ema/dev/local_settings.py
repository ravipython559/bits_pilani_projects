import os

from ema.settings import *

DEBUG = True

SECURE_PROXY_SSL_HEADER = None
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
TEMPLATE_DEBUG = DEBUG

ROOT_URLCONF = 'ema.dev.local_urls'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATIC_URL = '/static/'
MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(os.environ['HOME'], 'ema-share-dir', 'ema','static')
MEDIA_ROOT = os.path.join(os.sep, 'media', 'bits', 'ema', 'media')

AUTHENTICATION_BACKENDS = ('ema.backends.UserModelEmailBackend',)

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# DATABASES = {
# 	'default': {
# 		'ENGINE': 'django.db.backends.sqlite3',
# 		'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
# 	}

# }


DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.mysql',
		'NAME': 'ema_prod_dec_2021',
		'USER': 'root',
		# 'PASSWORD': 'P@ssw0rd',
		# 'HOST': '192.168.1.35',
		# 'HOST':'210.212.180.167',
		# 'PORT': '8032',
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

# DATABASES = {
# 	'default': {
# 		'ENGINE': 'django.db.backends.mysql',
# 		'NAME': 'ema',
# 		'USER': 'root',
# 		'PASSWORD': 'root',
# 		'OPTIONS': {
# 			'init_command': "SET sql_mode='STRICT_TRANS_TABLES', innodb_strict_mode=1",
# 			'charset': 'utf8mb4',
# 		},
# 		'TEST': {
# 			'CHARSET': 'utf8mb4',
# 			'COLLATION': 'utf8mb4_unicode_ci',
# 		},
# 	}
# }


ALLOWED_HOSTS = ['*',]

BITS_EMAIL_DOMAIN = r'parinati.in'

# AC_DOMAIN = 'http://192.168.1.11:8005'  # Change the ip with u r system ip for testing
