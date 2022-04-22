from storages.backends.s3boto import S3BotoStorage

class StaticStorage(S3BotoStorage):
	location = 'static'

class MediaStorage(S3BotoStorage):
	location = 'media'
	default_acl = 'private'
	querystring_auth = True
	querystring_expire = 300


try:
    from bits.local_storage import *
except:
    print("No local storage found.")

