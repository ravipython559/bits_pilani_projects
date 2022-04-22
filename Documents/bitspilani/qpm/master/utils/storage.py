from django.conf import settings
import datetime
import base64
import uuid
import boto3
import os
import io
from django.utils import timezone
import shutil

def document_extract_file(QP_doc):
	s3 = boto3.resource(settings.AWS_S3_STORAGE, aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
		aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, region_name=settings.AWS_REGION_NAME
	)
	bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
	file = os.path.join(settings.S3_MEDIA_DIR, QP_doc)
	temp_file = io.BytesIO()
	bucket.download_fileobj(file, temp_file)
	temp_file.seek(0)
	return temp_file



def admin_document_extract(filelist=None,doc_uuid=None,email=None,check_box=None):
	if not os.path.exists('/tmp/{}/documents/'.format(doc_uuid)):
		os.makedirs('/tmp/{}/documents/'.format(doc_uuid))
	if check_box=='only_instr':
		for filename in filelist:
			if filename.alternate_qp_path.name:
				s3 = boto3.resource(settings.AWS_S3_STORAGE, aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
				    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, region_name=settings.AWS_REGION_NAME
				)
				bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
				file = os.path.join(settings.S3_MEDIA_DIR, filename.alternate_qp_path.name)
				bucket.download_file(file, '/tmp/{}/{}'.format(doc_uuid,filename.alternate_qp_path.name))
				filename.save()

	elif check_box == 'both_qp_and_alternate_qp':
		for filename in filelist:
			if filename.qp_path.name:
				s3 = boto3.resource(settings.AWS_S3_STORAGE, aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
				    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, region_name=settings.AWS_REGION_NAME
				)
				bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
				file = os.path.join(settings.S3_MEDIA_DIR, filename.qp_path.name)
				bucket.download_file(file, '/tmp/{}/{}'.format(doc_uuid,filename.qp_path.name))
				filename.last_download_datetime = timezone.now()
				filename.downloaded_by = email
				filename.save()

		for filename in filelist:
			if filename.alternate_qp_path.name:
				s3 = boto3.resource(settings.AWS_S3_STORAGE, aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
				    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, region_name=settings.AWS_REGION_NAME
				)
				bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
				file = os.path.join(settings.S3_MEDIA_DIR, filename.alternate_qp_path.name)
				bucket.download_file(file, '/tmp/{}/{}'.format(doc_uuid,filename.alternate_qp_path.name))
				filename.save()

	else:
		for filename in filelist:
			if filename.qp_path.name:
				s3 = boto3.resource(settings.AWS_S3_STORAGE, aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
				    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, region_name=settings.AWS_REGION_NAME
				)
				bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
				file = os.path.join(settings.S3_MEDIA_DIR, filename.qp_path.name)
				bucket.download_file(file, '/tmp/{}/{}'.format(doc_uuid,filename.qp_path.name))
				filename.last_download_datetime = timezone.now()
				filename.downloaded_by = email
				filename.save()

	shutil.make_archive('/tmp/{}/documents/'.format(doc_uuid), 'zip', '/tmp/{}/documents/'.format(doc_uuid))
	return doc_uuid

try:
	from qpm.local_storage import *
except:
	print("No local storage found.")
