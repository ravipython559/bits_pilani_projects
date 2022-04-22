from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.utils import timezone
import time


@shared_task(time_limit=70000)
def send_email_from_fac_to_instr(message):
	subject = 'Question Paper Submission Update'
	admin_users = User.objects.filter(is_superuser=1).values_list('email', flat=True).distinct()
	admin_users_emails = list(admin_users)
	email = send_mail(subject,message,'<'+settings.FROM_EMAIL+'>',
					admin_users_emails,fail_silently=False)
	return 'success'
