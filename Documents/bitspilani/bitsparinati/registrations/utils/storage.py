from django.conf import settings
import datetime
import base64
import uuid
import boto3
import os
import io

def document_extract_file(ad=None, student_id=None):
	s3 = boto3.resource(settings.AWS_S3_STORAGE, aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
		aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, region_name=settings.AWS_REGION_NAME
	)
	bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

	if student_id:
		student_id = student_id.upper()
		file = os.path.join(settings.S3_MEDIA_DIR, 'documents/manual-upload/student-photo/{0}.jpg'.format(student_id))
		try:
			temp_file = io.BytesIO()
			bucket.download_fileobj(file, temp_file)
			temp_file.seek(0)
			return temp_file
		except Exception as e:
			student_id = student_id.lower()
			file = os.path.join(settings.S3_MEDIA_DIR, 'documents/manual-upload/student-photo/{0}.jpg'.format(student_id))
	else:
		file = os.path.join(settings.S3_MEDIA_DIR, ad.file.name)
	temp_file = io.BytesIO()
	bucket.download_fileobj(file, temp_file)
	temp_file.seek(0)
	return temp_file

def document_offer_file(cs):
	file = os.path.join(settings.S3_MEDIA_DIR, cs.offer_letter.name)
	s3 = boto3.resource(settings.AWS_S3_STORAGE, aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
		aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, region_name=settings.AWS_REGION_NAME
	)

	bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
	temp_file = io.BytesIO()
	bucket.download_fileobj(file, temp_file)
	temp_file.seek(0)
	return temp_file

try:
	from bits.local_storage import *

except:
	print("No local storage found.")