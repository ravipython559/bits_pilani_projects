import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bits.settings")
import django
django.setup()
import operator
import pytz
from registrations.models import *
from bits_admin.db_tools import Datediff
from django.db.models import *
from django.contrib.auth import get_user_model
from datetime import datetime as dt
from django.utils import timezone
from datetime import date, timedelta
from django.core.mail import send_mass_mail
from django.core import mail
from django.core.mail import get_connection, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from dateutil import rrule, parser
from validate_email import validate_email
kolkatta = pytz.timezone('Asia/Kolkata')

def send_mails(): #Automated Emailers Registered Users who are yet to Apply
	fuml = FollowUpMailLog.objects.aggregate(Max(F('run')))
	sca = StudentCandidateApplication.objects.values_list('login_email',flat = True)
	rev = Reviewer.objects.values_list('user',flat=True)
	bmc = BatchMailConfig.objects.get( mail_type = '1' )

	user_domains = ProgramDomainMapping.objects.exclude(
			Q(email_domain__isnull = True)|
			Q(email_domain ='')
		).values_list(
			'email_domain',flat=True
		).distinct()

	cutoff_date = bmc.cutoff_date
	cutoff_datetime=timezone.datetime.strptime(str(cutoff_date),'%Y-%m-%d')
	kolkatta_cutoff_datetime = cutoff_datetime.replace(tzinfo = kolkatta)
	actual_cutoff_date = kolkatta_cutoff_datetime.astimezone(pytz.UTC)
	
	users = get_user_model().objects.exclude(
			Q(date_joined__lt = actual_cutoff_date)|
			Q(pk__in  = sca) |
			Q(is_staff = True) |
			Q(pk__in = rev) |
			Q(email__in = ProgramDomainMapping.objects.values_list('email',flat = True)) |
			reduce(operator.or_,( Q( email__iendswith = x ) for x in user_domains ) )
		)

	x1 = timezone.localtime(timezone.now()).date()-timezone.timedelta(days=bmc.initial_day)
	x2 = bmc.cutoff_date
	ds_arg = {'dtstart' : x2,'until':x1} if x1>x2 else {'dtstart' : x1,'until':x2}
	date_range = map(lambda x:str(x.date()),list(rrule.rrule(rrule.DAILY,**ds_arg)))
	start_end_datetime = map(
		lambda x :timezone.datetime.strptime(str(x),'%Y-%m-%d'),
		[date_range[0],date_range[-1]]
		)
	range_datetime = [start_end_datetime[0],
		timezone.datetime(hour=23,minute=59,second=59,
			**{x:getattr(start_end_datetime[-1],x) for x in ['day','month','year'] })]

	kolkatta_range_datetime =map(lambda x: x.replace(tzinfo = kolkatta), range_datetime)
	actual_range_datetime = map(lambda x :x.astimezone(pytz.UTC),kolkatta_range_datetime)

	users = users.filter(
		date_joined__range = actual_range_datetime
		)

	sub ='Complete your Application for BITS Pilani degree programmes for working professionals'
	body = render_to_string('auto_mail/auto_email.html',)
	
	from_email = '<{0}>'.format(settings.FROM_EMAIL)

	emails_list = list(EmailMultiAlternatives(sub,body,from_email,[x.email,]) for x in users)
	for x in emails_list: x.attach_alternative(body,"text/html")

	connection = mail.get_connection(fail_silently = True )
	connection.open()
	email_send_list = connection.send_messages_bits(emails_list)
	connection.close()
	print '{0} : {1}'.format('follow_up_mails', users.values('email','date_joined'))

	BitsUser.objects.filter(user__email__in = email_send_list ).update(
		mails_sent_count = F('mails_sent_count') + 1,
		last_followup_mail_sent_on = timezone.now(),
		)

	FollowUpMailLog.objects.create(
		run = ( fuml['run__max'] if fuml['run__max'] else  0 ) + 1,
		mail_type = '1',
		no_of_mails_sent = len(email_send_list),
		)


def send_app_fee_mails(): #Automated Emailers to Applications who are yet to pay Application Fees
	fuml = FollowUpMailLog.objects.aggregate(Max(F('run')))
	bmc = BatchMailConfig.objects.get( mail_type = '2' )

	user_domains = ProgramDomainMapping.objects.exclude(
			Q(email_domain__isnull = True)|
			Q(email_domain ='')
		).values_list(
			'email_domain',flat=True
		).distinct()

	cutoff_date = bmc.cutoff_date
	cutoff_datetime=timezone.datetime.strptime(str(cutoff_date),'%Y-%m-%d')
	kolkatta_cutoff_datetime = cutoff_datetime.replace(tzinfo = kolkatta)
	actual_cutoff_date = kolkatta_cutoff_datetime.astimezone(pytz.UTC)

	sca = StudentCandidateApplication.objects.exclude(
			Q(created_on_datetime__lt = actual_cutoff_date )|
			Q(login_email__email__in = ProgramDomainMapping.objects.values_list('email',flat = True)) |
			reduce(operator.or_,( Q( login_email__email__iendswith = x ) for x in user_domains ) )|
			reduce(operator.or_,( 
				Q( login_email__email = x.employee_email,
					program = x.program  ) for x in ExceptionListOrgApplicants.objects.filter(
					Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
					exception_type='1',
					) 
				) 
			)
		
		)

	x1 = timezone.localtime(timezone.now()).date()-timezone.timedelta(days=bmc.initial_day)
	x2 = bmc.cutoff_date
	ds_arg = {'dtstart' : x2,'until':x1} if x1>x2 else {'dtstart' : x1,'until':x2}
	date_range = map(lambda x:str(x.date()),list(rrule.rrule(rrule.DAILY,**ds_arg)))
	start_end_datetime = map(
		lambda x :timezone.datetime.strptime(str(x),'%Y-%m-%d'),
		[date_range[0],date_range[-1]]
		)
	range_datetime = [start_end_datetime[0],
		timezone.datetime(hour=23,minute=59,second=59,
			**{x:getattr(start_end_datetime[-1],x) for x in ['day','month','year'] })]

	kolkatta_range_datetime =map(lambda x: x.replace(tzinfo = kolkatta), range_datetime)
	actual_range_datetime = map(lambda x :x.astimezone(pytz.UTC),kolkatta_range_datetime)

	sca = sca.filter( created_on_datetime__range = actual_range_datetime,
		application_status = settings.APP_STATUS[12][0]  )

	sub ='Your Application Fee of INR 1500 is due for BITS Pilani degree programmes for working professionals'
	body = render_to_string('auto_mail/auto_email_app_fee.html',)
	
	from_email = '<{0}>'.format(settings.FROM_EMAIL)

	emails_list = list(EmailMultiAlternatives(sub,body,from_email,[x.login_email.email,]) for x in sca)
	for x in emails_list: x.attach_alternative(body,"text/html")

	connection = mail.get_connection( fail_silently = True )
	connection.open()
	email_send_list = connection.send_messages_bits(emails_list)
	connection.close()
	print '{0} : {1}'.format('followup_app_fee_mail',
		sca.values('login_email__email',
		'created_on_datetime',
		'application_status'
		)
	)

	BitsUser.objects.filter(user__email__in = email_send_list ).update(
		app_fee_mail_sent_count = F('app_fee_mail_sent_count') + 1,
		last_followup_app_fee_mail_sent = timezone.now(),
		)

	FollowUpMailLog.objects.create(
		run = ( fuml['run__max'] if fuml['run__max'] else  0 ) + 1,
		mail_type = '2',
		no_of_mails_sent = len(email_send_list),
		)
