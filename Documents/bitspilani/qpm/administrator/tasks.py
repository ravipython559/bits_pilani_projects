from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from master.utils.storage import admin_document_extract
import time
import itertools

@shared_task(time_limit=70000)
def qp_email_send_async(faculty_email_ids, qpsubmissions):
	faculty_email_ids = set(list(itertools.chain(*faculty_email_ids)))
	for email_id in faculty_email_ids:
		if email_id:
			subject = 'Question Paper Submission Reminder'
			message = '''Greetings Faculty,\n You have one or more question papers that are awaiting submissions from your side.You are requested to submit the same ASAP.\n Please do so at the link - https://qpm-wilp.bits-pilani.ac.in \n\n Regards \n WILP Instruction Team'''
			email = send_mail(subject,message,'<'+settings.FROM_EMAIL+'>',
					[email_id],fail_silently=False)
			qpsubmissions = qpsubmissions.filter(Q(faculty_email_id=email_id) | Q(email_access_id_1=email_id) | Q(email_access_id_2=email_id))
			for i in qpsubmissions:
				i.last_reminder_email_datetime = timezone.now()
				i.save()

		# time.sleep(2)
	subject = 'Question Paper Reminder Email Sent'
	message = 'Reminder emails have been sent to faculty for submission of Question papers'
	admin_users = User.objects.filter(is_superuser=1).values_list('email', flat=True).distinct()
	admin_users_emails = list(admin_users)

	email = send_mail(subject,message,'<'+settings.FROM_EMAIL+'>',
				admin_users_emails,fail_silently=False)
	return 'success'

@shared_task(time_limit=70000)
def send_email_fac(message, faculty):
	emails = set([faculty.faculty_email_id, faculty.email_access_id_1, faculty.email_access_id_2])
	for i in emails:
		if i:
			subject = 'Question Paper Submission Update'
			email = send_mail(subject,message,'<'+settings.FROM_EMAIL+'>',
							[i],fail_silently=False)
	return 'success'


@shared_task(time_limit=70000)
def admin_multiple_file_download(filelist=None,doc_uuid=None,email=None,check_box=None):
	admin_document_extract(filelist=filelist,doc_uuid=doc_uuid,email=email,check_box=check_box)
	return doc_uuid
