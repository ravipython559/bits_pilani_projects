import os

#os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bits.settings")
#import django
#django.setup()

from datetime import datetime
from django.conf import settings
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from bits.bits_conf import * 

def db_bkup():
	os.system(DB_CMD)

	gauth = GoogleAuth()
	# Try to load saved client credentials
	gauth.LoadCredentialsFile()
	if gauth.credentials is None:
		# Authenticate if they're not there
		gauth.LocalWebserverAuth()
	elif gauth.access_token_expired:
		# Refresh them if expired
		print "Google Drive Token Expired, Refreshing"
		gauth.Refresh()
	else:
		# Initialize the saved creds
		gauth.Authorize()
	# Save the current credentials to a file
	# gauth.SaveCredentialsFile()
	drive = GoogleDrive(gauth)

	folder_id = None
	try:
		with open(FILE_ROOT) as f:
			folder_id = f.read()
	except IOError: pass

	files_id = map(lambda x: x['id'], 
		drive.ListFile({
			'q': "'root' in parents and trashed=false"
			}).GetList())

	if not folder_id in files_id:
		folder = drive.CreateFile({'name':DRIVE_FOLDER_NAME,
			'mimeType':'application/vnd.google-apps.folder',
			'title':DRIVE_FOLDER_NAME,
			})

		folder.Upload()
		with open(FILE_ROOT,'w') as f:
			f.write(folder['id'])
		folder_id = folder['id']

	today = str(timezone.localtime(timezone.now()).date())
	folder1 = drive.CreateFile({'name':today,
				'mimeType':'application/vnd.google-apps.folder',
				'title':today,
				'parents':[{'id':folder_id}],
				})
	folder1.Upload()
	folder_id1 = folder1['id']

	file = drive.CreateFile()
	file.SetContentFile(DB_PATH)
	file['parents'] = [{'id':folder_id1}]
	file.Upload()
	os.remove(DB_PATH)
	file['title'] = drive_file_title(today)
	file.Upload()
	email = EmailMultiAlternatives(subject(today),
            msg(file['alternateLink']),SENDER,EMAIL_TO,cc=EMAIL_Cc)
	#email.attach_alternative(msg(file['alternateLink']), "text/html")
	email.send(fail_silently=True)

