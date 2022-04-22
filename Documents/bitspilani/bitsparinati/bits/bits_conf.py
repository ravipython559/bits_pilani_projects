import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bits.settings")
import django
django.setup()
from django.utils import timezone
from django.conf import settings
import pytz
kolkatta = pytz.timezone('Asia/Kolkata')
 
SENDER = '<{0}>'.format(settings.FROM_EMAIL)
EMAIL_FROM =  'backup@wilp.bits-pilani.ac.in'

EMAIL_TO = ['shantanu@hyderabad.bits-pilani.ac.in',]
EMAIL_Cc = ['bits.wilp@parinati.in']
FOLDER_NAME = 'PROD-AC_folder_id.txt'
DRIVE_FOLDER_NAME = 'AWS-PROD-AC-BITS-BKUP'

CLOUD_FILENAME = 'AWS_prod_AC_backup{0}.sql'
cloud_filename = lambda x: CLOUD_FILENAME.format(x)

DRIVE_FILE_TITLE = 'AWS_PROD_DB_backup_{0}.sql'
drive_file_title = lambda x: DRIVE_FILE_TITLE.format(x)
FILE_ROOT = os.path.join(settings.BASE_DIR, FOLDER_NAME)

DB_PATH = os.path.join(settings.BASE_DIR,'bits_db_bk_up','backup.sql.gz')

DB_CMD = r"mysqldump --user={user} --password='{password}' --host={host} --port={port} {db_name} |gzip -9 > {path}".format(
		user = settings.DATABASES['default']['USER'],
		password = settings.DATABASES['default']['PASSWORD'],
		host = settings.DATABASES['default']['HOST'],
		port = settings.DATABASES['default']['PORT'],
		db_name = settings.DATABASES['default']['NAME'],
		path = DB_PATH,
		)

SUBJECT = 'BITS AC AWS Database backup {0}'
subject = lambda x:SUBJECT.format(x)


MSG = '''
Hello Shantanu,


The PROD DB Backup have been taken and uploaded in the drive . PFB the link to download.
{0}
Please check and verify.

Thanks and Regards,
Admission Cell
Work Integrated Learning Programmes
Birla Institute of Technology & Science, Pilani

'''
msg = lambda x:MSG.format(x)






