from django.conf import settings
import datetime
import base64
import uuid
import boto3
import os
import io

def document_extract_file(student):
	
	s3 = boto3.resource(settings.AWS_S3_STORAGE, aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
		aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, region_name=settings.AWS_REGION_NAME
	)

	bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
	temp_file = io.BytesIO()
	file = os.path.join(settings.S3_MEDIA_DIR, student.photo.name)
	bucket.download_fileobj(file, temp_file)
	temp_file.seek(0)
	return temp_file