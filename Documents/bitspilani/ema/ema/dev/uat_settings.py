from .local_settings import *
ALLOWED_HOSTS = ['*',]
#Shibboleth
MEDIA_ROOT = os.path.join(os.environ['HOME'], 'ema-share-dir', 'ema','media')

AUTHENTICATION_BACKENDS = (
        'ema.backends.ShibbolethRemoteUserBackend',
        'ema.backends.UserModelEmailBackend',
        'django.contrib.auth.backends.ModelBackend',
)
DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.mysql',
		'NAME': 'ema',
		'USER': 'root',
		'PASSWORD': 'root',
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

BITS_EMAIL_DOMAIN = r'.*\.bits-pilani.ac.in$'

AC_DOMAIN = 'http://admission-uat.x.codeargo.com/'

SDMS_API_URL = "https://sdms-bits.x.codeargo.com/api/v1/student_data/"
SDMS_API_AUTHKEY = "b7791e72-c52e-4eb2-84eb-33d2f6bdc341"
SDMS_API_AUTHHEADER = "AuthToken"
SDMS_STUDENT_URL = "https://sdms.bits-pilani.ac.in/profile/"