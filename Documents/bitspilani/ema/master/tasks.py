from celery import shared_task
from django.conf import settings
from master.models import *
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth.models import User
from bulk_update.helper import bulk_update
import requests

@shared_task(time_limit=70000)
def sync_sdms_email_and_phone(students_data):
	admin_users = User.objects.filter(is_superuser=1)
	admin_users_emails = []
	for i in admin_users:
		if i.email != 'dummyuser@wilp.bits-pilani.ac.in':
			admin_users_emails.append(i.email)
	failed_students = []
	objs = []
	for student in students_data:
		headers = {
			'Content-type': 'application/json',
			settings.SDMS_API_AUTHHEADER : settings.SDMS_API_AUTHKEY ,
			'host': 'sdms.bits-pilani.ac.in',
		}
		params = {"student_id":"{}@wilp.bits-pilani.ac.in".format(student.student_id).lower()}
		response = requests.get(settings.SDMS_API_URL, params=params, headers=headers)
		if response.status_code !=200:
			failed_students.append(student.student_id)
		else:
			resp_json = response.json()
			student = Student.objects.filter(student_id=student.student_id)[0]
			student_params = {}
			if 'contact_no' in resp_json:
				if resp_json['contact_no'] != '':
					student.personal_phone = resp_json['contact_no']
					student.created_on = timezone.now()
			if 'email' in resp_json:
				if resp_json['email'] != '':
					student.personal_email = resp_json['email']
					student.created_on = timezone.now()
			objs.append(student)
	Student.objects.bulk_update(objs, ['personal_phone', 'personal_email', 'created_on'], batch_size=50000)
	if len(failed_students)==0:
		subject = 'Exam System Sync with SDMS Completed'
		message = 'Greetings, The sync with SDMS for {} student records is completed. Please check the data in Exam System when convenient'.format(len(students_data))
		email = send_mail(subject,message,'<'+settings.FROM_EMAIL+'>',
				admin_users_emails,fail_silently=False)
		return 'success'
	elif len(students_data)-len(failed_students)==0:
		subject = 'Exam System Sync with SDMS Failed'
		message = 'Greetings, The sync with SDMS for {} student records failed. Please check and retry the sync process'.format(len(failed_students))
		email = send_mail(subject,message,'<'+settings.FROM_EMAIL+'>',
				admin_users_emails,fail_silently=False)
		return 'failure'
	else:
		subject = 'Exam System Sync with SDMS Completed'
		message = 'Greetings, The sync with SDMS for {} student records is completed. Please check the data in Exam System when convenient'.format(len(students_data)-len(failed_students))
		email = send_mail(subject,message,'<'+settings.FROM_EMAIL+'>',
				admin_users_emails,fail_silently=False)

		subject = 'Exam System Sync with SDMS Failed'
		message = 'Greetings, The sync with SDMS for {} student records failed. Please check and retry the sync process'.format(len(failed_students))
		email = send_mail(subject,message,'<'+settings.FROM_EMAIL+'>',
				admin_users_emails,fail_silently=False)

		subject = 'Exam System Sync with SDMS Failed Student List'
		message = 'Failed Student List:{}'.format(failed_students)
		email = send_mail(subject,message,'<'+settings.FROM_EMAIL+'>',
				['ravisankar.reddy@accionlabs.com', 'mehndi.mahajan@accionlabs.com', 'vishakha.kudchadker@accionlabs.com'],fail_silently=False)
		return 'success, failure'

@shared_task(time_limit=70000)
def sync_ema_data_to_qpm(payload):
	url = settings.QPM_HOST_URL+'/administrator/sync-ema-examtype/'
	a = requests.post(url, data=payload)
	return 'success'

@shared_task(time_limit=70000)
def delete_sync_ema_data_to_qpm(payload):
	url = settings.QPM_HOST_URL+'/administrator/sync-ema-examtype/'
	a = requests.delete(url, data=payload)
	return 'success'

@shared_task(time_limit=70000)
def sync_ema_batch_data_to_qpm(payload):
	url = settings.QPM_HOST_URL+'/administrator/sync-ema-batch/'
	a = requests.post(url, data=payload)
	return 'success'

@shared_task(time_limit=70000)
def delete_sync_ema_batch_data_to_qpm(payload):
	url = settings.QPM_HOST_URL+'/administrator/sync-ema-batch/'
	a = requests.delete(url, data=payload)
	return 'success'

@shared_task(time_limit=70000)
def sync_ema_semester_data_to_qpm(payload):
	url = settings.QPM_HOST_URL+'/administrator/sync-ema-semester/'
	a = requests.post(url, data=payload)
	return 'success'

@shared_task(time_limit=70000)
def delete_sync_ema_semster_data_to_qpm(payload):
	url = settings.QPM_HOST_URL+'/administrator/sync-ema-semester/'
	a = requests.delete(url, data=payload)
	return 'success'

@shared_task(time_limit=70000)
def sync_ema_exam_slot_data_to_qpm(payload):
	url = settings.QPM_HOST_URL+'/administrator/sync-ema-examslot/'
	a = requests.post(url, data=payload)
	return 'success'

@shared_task(time_limit=70000)
def delete_sync_ema_exam_slot_data_to_qpm(payload):
	url = settings.QPM_HOST_URL+'/administrator/sync-ema-examslot/'
	a = requests.delete(url, data=payload)
	return 'success'

