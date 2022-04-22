import commands
import os
from datetime import datetime
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from bits.bits_conf import * 

def s3_bucket_backup(main_bucket, backup_bucket, region):
	bucket_location = lambda bucket_name: r"s3://{name}".format(name=bucket_name)
	s3_sync = r"{aws} s3 sync {bucket1} {bucket2}  --region {region}".format(
                aws='/home/ubuntu/.local/bin/aws',
		bucket1=bucket_location(main_bucket),
		bucket2=bucket_location(backup_bucket),
		region=region
		)
	output = commands.getstatusoutput(s3_sync)
	status = 'failed' if output[0] else 'success'

	subject = 'S3 bucket {bucket} backup {date}'.format(
		bucket=main_bucket,
		date=timezone.localtime(timezone.now()).strftime("%d-%m-%Y %I:%M %p"))
	MAIL_TO = ['shantanu@hyderabad.bits-pilani.ac.in',]
	MAIL_Cc = ['bits.wilp@parinati.in']
	msg = """
	Hi Shantanu,\nWe have taken s3 bucket {bucket}.\nbackup status : {status}
	""".format(bucket=main_bucket, status=status)

	email = EmailMultiAlternatives(subject, msg, SENDER,MAIL_TO, cc=MAIL_Cc)
	email.send(fail_silently=True)





