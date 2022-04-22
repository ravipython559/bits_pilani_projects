from django.shortcuts import render, redirect
from registrations.models import *
from django.core import serializers
from django.http import Http404
from django.views.decorators.http import require_http_methods
from .forms import *
from .bits_decorator import *
from djqscsv import render_to_csv_response
from django.db.models.functions import Concat
from django.db.models import Max,Value,Count,F,Q,CharField, Case,  When, Sum,IntegerField,DateTimeField
from django.db.models.functions import Length, Upper, Value, Substr
from django.contrib.auth.decorators import login_required
import time
from time import strftime
from django.core.urlresolvers import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.contrib.auth.models import User
import os, tempfile, zipfile, shutil
from wsgiref.util import FileWrapper
from django.http import HttpResponse, StreamingHttpResponse, FileResponse
from django.core.serializers.json import DjangoJSONEncoder
import pytz
from .db_tools import Datediff
from datetime import datetime as dt
from .tables import *
from table.views import FeedDataView
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from bits_admin.dynamic_views import *
from bits_admin.tables_ajax import *
from bits_admin.csv_views import *
from registrations.utils.encoding_pdf import BasePDFTemplateView
from easy_thumbnails.files import get_thumbnailer
import json
import operator
import requests
import logging
from .models import *
import cPickle


logger = logging.getLogger("main")

def get_choice_display(value,choices):
	for k,v in choices:
		if k==value:return v
	return "Not Found"

def display_status(status):
	for x in settings.APP_STATUS:
		if x[0] == status:
			return x[1]

class PaymentAppDataView(FeedDataView):

	token = usr_payment_filter_paging().token
	def get_queryset(self):
		query = super(PaymentAppDataView, self).get_queryset()
		from_date = self.kwargs.get('fm_dt',None)
		to_date = self.kwargs.get('to_dt',None)
		bank = self.kwargs.get('bank',None)

		from_date = from_date if not from_date == '00-00-0000' else None
		to_date = to_date if not to_date == '00-00-0000' else None
		bank_name = bank if not bank =='n' else None
		query = query.annotate(
			app_id = Case(
					When(candidateselection_requests_created_5550__new_application_id=None, 
						then=Concat('student_application_id',Value(' '))),
					default=Concat('candidateselection_requests_created_5550__new_application_id',Value(' ')),
					output_field=CharField(),
					),
			full_prog = Concat('program__program_name',Value(' - '),
				'program__program_code',Value(' ('),
				'program__program_type',Value(')')),
			payment_date = F('applicationpayment_requests_created_3__payment_date'),
			payment_amount = F('applicationpayment_requests_created_3__payment_amount'),
			transaction_id = F('applicationpayment_requests_created_3__transaction_id'),
			payment_bank = F('applicationpayment_requests_created_3__payment_bank'),
			)

		if from_date and to_date :
			query=query.exclude( 
				payment_date__isnull = True 
				).filter( 
				payment_date__range = [dt.strptime(from_date,"%Y-%m-%d %H:%M:%S"),
				dt.strptime(to_date,"%Y-%m-%d %H:%M:%S")] 
				)
		elif from_date :
			query=query.exclude( 
				payment_date__isnull = True 
				).filter(
				payment_date__gte = dt.strptime(from_date,"%Y-%m-%d %H:%M:%S") 
				)
		elif to_date :
			query=query.exclude( 
				payment_date__isnull = True 
				).filter( 
				payment_date__lte = dt.strptime(to_date,"%Y-%m-%d %H:%M:%S") 
				)
		if bank_name:
			if 'TPSL' != bank_name:
				query = query.filter(payment_bank=bank_name)
			else:
				query = query.filter(payment_bank__regex=r'^[0-9]+$')
		return query

	def get_queryset_length(self, queryset):
		return len(queryset)

@staff_member_required
def paymentDataView(request):
	logger.info("{0} invoked funct.".format(request.user.email))

	query = StudentCandidateApplication.objects.annotate(
		app_id = Case(
				When(candidateselection_requests_created_5550__new_application_id=None, 
					then=Concat('student_application_id',Value(' '))),
				default=Concat('candidateselection_requests_created_5550__new_application_id',Value(' ')),
				output_field=CharField(),
				),
		full_prog = Concat('program__program_name',Value(' - '),
				'program__program_code',Value(' ('),
				'program__program_type',Value(')')),
		payment_date = F('applicationpayment_requests_created_3__payment_date'),
		payment_amount = F('applicationpayment_requests_created_3__payment_amount'),
		transaction_id = F('applicationpayment_requests_created_3__transaction_id'),
		payment_bank = F('applicationpayment_requests_created_3__payment_bank'),
		)

	SCATable = usr_payment_filter_paging()

	table = SCATable(query)

	return render(request, 'payment_data_view.html', {"queryResult": query ,
		"form1": ToAndFromDate(),'table': table},
		)


@staff_member_required
@require_http_methods(["POST"])
def date_refresh_payment(request):

	to_date = request.POST.get( "to_date", None )
	from_date = request.POST.get("from_date", None )
	bank_name = request.POST.get("bank_type", None )
	data = {}
	
	if to_date :
		data['to_date'] = to_date
		t = to_date.split('-')
		to_date = dt( int(t[2]), int(t[1]), int(t[0]), 23, 59, 59 )
	

	if from_date :
		data['from_date'] = from_date
		t = from_date.split('-')
		from_date = dt( int(t[2]), int(t[1]), int(t[0]), 00, 00, 00 )
	if bank_name:
		data['bank_type'] = bank_name

	query = StudentCandidateApplication.objects.annotate(
		app_id = Case(
				When(candidateselection_requests_created_5550__new_application_id=None, 
					then=Concat('student_application_id',Value(' '))),
				default=Concat('candidateselection_requests_created_5550__new_application_id',Value(' ')),
				output_field=CharField(),
				),
		full_prog = Concat('program__program_name',Value(' - '),
				'program__program_code',Value(' ('),
				'program__program_type',Value(')')),
		payment_date = F('applicationpayment_requests_created_3__payment_date'),
		payment_amount = F('applicationpayment_requests_created_3__payment_amount'),
		transaction_id = F('applicationpayment_requests_created_3__transaction_id'),
		payment_bank = F('applicationpayment_requests_created_3__payment_bank'),
		)
	


	if from_date and to_date :
		query=query.exclude( 
			payment_date__isnull = True 
			).filter( 
			payment_date__range=[from_date,to_date] 
			)
	elif from_date :
		query=query.exclude( 
			payment_date__isnull = True 
			).filter( 
			payment_date__gte=from_date 
			)
	elif to_date :
		query=query.exclude( 
			payment_date__isnull = True 
			).filter( payment_date__lte=to_date )

	if bank_name:
		if 'TPSL' != bank_name:
			query = query.filter(payment_bank=bank_name)
		else:
			query = query.filter(payment_bank__regex=r'^[0-9]+$')

	SCATable = usr_payment_filter_paging( from_date = from_date,
	 to_date = to_date,bank=bank_name)
	table = SCATable(query)
	
	return render(request, 'payment_data_view.html', {
		'queryResult' : query ,
		'form1' : ToAndFromDate(data),
		'table' : table,
		},)


@method_decorator([staff_member_required],name='dispatch')
class MyDataView(ApplicantAjaxDataView):
	token = filter_paging().token


@method_decorator([staff_member_required],name='dispatch')
class ViewData(ApplicantDataView):
	template_name = 'applicantView2.html'

@method_decorator([staff_member_required],name='dispatch')
class DateRefresh(DateRefreshView):
	template_name = 'applicantView2.html'

@method_decorator([staff_member_required],name='dispatch')
class CSVView(BaseCSVView):pass

@rev_and_pay_rev_permission
def ApplicationAdminView(request,id,alert_status=None):
	logger.info("{0} invoked funct.".format(request.user.email))
	app=StudentCandidateApplication.objects.get(id=id)
	edu=StudentCandidateWorkExperience.objects.filter(application=app)
	qual=StudentCandidateQualification.objects.filter(application=app)
	uploadFiles=ApplicationDocument.objects.filter(application=app)
	try:
		cs = CandidateSelection.objects.get(application = app)
		bits_comment = cs.selection_rejection_comments
	except CandidateSelection.DoesNotExist:
		cs=None
		bits_comment = None


	# code to hide employment and mentor details
	sca_attributes = app.__dict__.keys()
	for x in sca_attributes:
		setattr(app, '%s_hide' %(x), False)

	rejected_attributes = FormFieldPopulationSpecific.objects.filter(
	program=app.program,
	show_on_form=False,
	).values_list('field_name', flat=True)

	for x in rejected_attributes:
		setattr(app, '%s_hide' %(x), True)

	teaching_mode_check = FormFieldPopulationSpecific.objects.filter(program = app.program,show_on_form=True,
				field_name__in=['teaching_mode','programming_flag','alternate_email_id',]
			).values_list('field_name', flat=True)

	is_specific = app.program.program_type == 'specific'

	url_sel_rej = reverse_lazy('bits_admin:pre_sel_rej_email')

	if request.method == "POST":
		form = DobForm(request.POST,instance=app)
		if form.is_valid():
			form.save()
	else:
		form = DobForm(initial={"date_of_birth":app.date_of_birth},instance=app)

	is_pre_sel_rej = app.application_status == settings.APP_STATUS[18][0] or app.application_status == settings.APP_STATUS[19][0]

	bits_rej_reason = ( 
			', '.join(cPickle.loads(str(cs.bits_rejection_reason))) if 
			cs and
			not cs.bits_rejection_reason == cPickle.dumps(None) and
			cs.bits_rejection_reason	
		else None 
	)

	return render(request,'application_form_view.html',{
		'form':app,
		'edu1':edu,
		'qual1':qual,
		'uploadFiles':uploadFiles,
		'alert_status':alert_status,
		'form1': form,
		'teaching_mode_check':teaching_mode_check,
		'is_specific':is_specific,
		'url_sel_rej':url_sel_rej,
		'is_pre_sel_rej':is_pre_sel_rej,
		'bits_rej_reason':bits_rej_reason,
		'bits_comment':bits_comment,
		})


class ApplicantAdmin (BasePDFTemplateView):
	template_name="applicantpdf.html"
	pdf_kwargs = {'encoding' : 'utf-8',}

	def get_context_data(self, **kwargs):
		email_id = None
		if self.request.user.is_authenticated():
			print self.request.user.id
			email_id = self.request.user
			context=super(ApplicantAdmin,self).get_context_data(
				pagesize="A4",
				title="Hi there!",
				**kwargs)
		q=StudentCandidateApplication.objects.annotate(finalName=F('full_name'))
		q=q.filter(login_email=email_id)#list
		context['q']=q
		context['qualification']=StudentCandidateQualification.objects.filter(application=q[0])	#list
		context['exp']=StudentCandidateWorkExperience.objects.filter(application=q[0])#list	

		return context




@staff_member_required
@require_http_methods(["POST"])
def csv_payment_view(request) :
	logger.info("{0} invoked funct.".format(request.user.email))
	csv_fee_value = ['app_id',
				 'full_name','full_prog',
				 'created_on_datetime',
				 'payment_date',
				 'payment_amount',
				 'transaction_id',
				 'payment_bank',
				 'application_status',] #order

	csv_fee_header = {'app_id':'Application Number',
				 'full_name':'Name', 
				 'full_prog':'Program Applied For',
				 'created_on_datetime':'Applied on Date',
				 'payment_date':'Payment Date',
				 'payment_amount':'Payment Amount', 
				 'transaction_id':'Transaction ID',
				 'payment_bank':'Payment Bank',
				 'application_status':'Current Status'}

	field_serializer_map_fee={
	'created_on_datetime': (lambda x: (x or '') and timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p")),
	'payment_date':(lambda x: (x or '') and timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p")),
	'application_status':(lambda x: display_status(x)),
	}
	from_date=request.POST.get("fromDate",None)
	to_date=request.POST.get("toDate",None)
	search=request.POST.get("search",'')
	bank_name = request.POST.get("bank",None)

	if to_date:
		t = to_date.split('-')
		to_date = dt( int(t[2]), int(t[1]), int(t[0]), 23, 59, 59 )
	if from_date:
		t = from_date.split('-')
		from_date = dt( int(t[2]), int(t[1]), int(t[0]), 00, 00, 00 )
	
	query = StudentCandidateApplication.objects.annotate(
		app_id = Case(
					When(candidateselection_requests_created_5550__new_application_id=None, 
					then=Concat('student_application_id',Value(' '))),
				default=Concat('candidateselection_requests_created_5550__new_application_id',Value(' ')),
				output_field=CharField(),
				),

		full_prog = Concat('program__program_name',Value(' - '),
				'program__program_code',Value(' ('),
				'program__program_type',Value(')')),
		payment_date = F('applicationpayment_requests_created_3__payment_date'),
		payment_amount = F('applicationpayment_requests_created_3__payment_amount'),
		transaction_id = F('applicationpayment_requests_created_3__transaction_id'),
		payment_bank = Case(
			When(applicationpayment_requests_created_3__payment_bank__regex=r'^[0-9]+$', then=Value('Tech Process')),
			When(~Q(applicationpayment_requests_created_3__payment_bank__regex=r'^[0-9]+$'),
				 then=F('applicationpayment_requests_created_3__payment_bank')),
			output_field=CharField(),
		)
		)

	query = query.filter(
		reduce(operator.and_, (
			Q(full_name__icontains=item) |
			Q(app_id__icontains=item) |
			Q(full_prog__icontains=item)
			for item in search.split()))
	) if search else query

	if from_date and to_date :
		query=query.exclude( 
			payment_date__isnull = True 
			).filter( 
			payment_date__range=[from_date,to_date] 
			)

	elif from_date :
		query=query.exclude( 
			payment_date__isnull = True 
			).filter( 
			payment_date__gte=from_date 
			)
	elif to_date :
		query=query.exclude( 
			payment_date__isnull = True 
			).filter( payment_date__lte=to_date )

	if bank_name:
		if 'TPSL' != bank_name:
			query = query.filter(payment_bank=bank_name)
		else:
			query = query.filter(payment_bank='Tech Process')
	
	query=query.values(*csv_fee_value).distinct()	
	return render_to_csv_response(query,append_datestamp=True,
		field_header_map=csv_fee_header,
		field_serializer_map=field_serializer_map_fee ,field_order=csv_fee_value,)

#//////// 
@staff_member_required
@require_http_methods(["POST"])
def user_csv_view(request) :

	def display_waiver(x):
		email, pg_code = x.split('|')

		eloa=ExceptionListOrgApplicants.objects.filter(
			Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
			employee_email=email.strip(),program__program_code=pg_code.strip()
				).values_list('exception_type',flat=True)

		return ' and '.join(map(lambda x:dict(FEE_TYPE_CHOICE)[x].capitalize(),eloa))

	from_date=request.POST.get("fromDate",None)
	to_date=request.POST.get("toDate",None)
	search=request.POST.get("user",'')
	if to_date :
		t = to_date.split('-')
		to_date = dt( int(t[2]), int(t[1]), int(t[0]), 23, 59, 59 )
	if from_date :
		t = from_date.split('-')
		from_date= dt( int(t[2]), int(t[1]), int(t[0]), 00, 00, 00 )

	query = get_user_model().objects.annotate(
		pg_code = F('studentcandidateapplication_requests_created_5__program__program_code'),
		pg_name = Case(
				When(studentcandidateapplication_requests_created_5__program__isnull=False, 
					then=Concat('studentcandidateapplication_requests_created_5__program__program_name',
						Value(' - '),
						'studentcandidateapplication_requests_created_5__program__program_code',
						Value(' ('),
						'studentcandidateapplication_requests_created_5__program__program_type',
						Value(')')),),
				default=Value(''),
				output_field=CharField(),
				),
		user_waiver = Concat('email', Value('|'), 'studentcandidateapplication_requests_created_5__program__program_code'),
		last_mail_senton=F('bitsuser_user__last_followup_mail_sent_on'),
		mails_count=F('bitsuser_user__mails_sent_count'),
		app_fee_mail_senton=F('bitsuser_user__last_followup_app_fee_mail_sent'),
		app_fee_mail_count=F('bitsuser_user__app_fee_mail_sent_count'),
		program_registered_for=F('bitsuser_user__register_program_id__program_code'),
		utm_source_first=F('bitsuser_user__utm_source_first'),
		utm_medium_first=F('bitsuser_user__utm_medium_first'),
		utm_campaign_first=F('bitsuser_user__utm_campaign_first'),
		utm_source_last=F('bitsuser_user__utm_source_last'),
		utm_medium_last=F('bitsuser_user__utm_medium_last'),
		utm_campaign_last=F('bitsuser_user__utm_campaign_last'),
		)
	
	query = query.filter(
				reduce(operator.and_, (
					Q(email__icontains = item)|
					Q(pg_name__icontains = item)
					for item in search.split()))
				) if search else query

	if from_date and to_date:
		query=query.filter(date_joined__range=[from_date,to_date])
	elif from_date:
		query=query.filter(date_joined__gte=from_date)
	elif to_date:
		query=query.filter(date_joined__lte=to_date)

	query = query.values('email', 'last_login', 'pg_name', 'date_joined',
		'last_mail_senton','mails_count','app_fee_mail_senton','app_fee_mail_count','user_waiver', 'program_registered_for', 'utm_source_first', 'utm_medium_first', 'utm_campaign_first', 'utm_source_last', 'utm_medium_last', 'utm_campaign_last')

	return render_to_csv_response(query, append_datestamp=True,
		field_header_map={'email': 'User Id', 
		'date_joined': 'Created on',
		'pg_name': 'Program Applied For',
		'last_login': 'Last Logged on',
		'last_mail_senton': 'Last Follow Up Mail Sent On',
		'mails_count': 'Mails Sent Count',
		'app_fee_mail_senton':'Last Followup Application Fee Mail Sent On',
		'app_fee_mail_count':'Application Fee Mails Sent Count',
		'user_waiver':'Waiver',
		'program_registered_for':'Program Registered for',
		'utm_source_first': 'UTM Source First',
		'utm_medium_first': 'UTM Medium First',
		'utm_campaign_first': 'UTM Campaign First',
		'utm_source_last': 'UTM Source Last',
		'utm_medium_last': 'UTM Medium Last',
		'utm_campaign_last': 'UTM Campaign Last',
		},
		field_order=['email', 'date_joined','pg_name','user_waiver', 'last_login','last_mail_senton',
			'mails_count','app_fee_mail_senton','app_fee_mail_count','program_registered_for',
			'utm_source_first','utm_medium_first','utm_campaign_first','utm_source_last','utm_medium_last','utm_campaign_last'],
		field_serializer_map={'date_joined': (lambda x: (x or '') and timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p")),
		'last_login': (lambda x: (x or '') and timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p")),
		'last_mail_senton': (lambda x: (x or '') and timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p")),
		'app_fee_mail_senton': (lambda x: (x or '') and timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p")),
		'user_waiver': (lambda x: display_waiver(x)),
		})




@staff_member_required
def userdatacsv_view(request):
	logger.info("{0} invoked funct.".format(request.user.email))
	query = get_user_model().objects.all()
	query = query.values('email', 'last_login', 'date_joined')
	return render_to_csv_response(query,append_datestamp=True,
		field_header_map={'email':'User Id','date_joined':'Created on', 'last_login':'Last Logged on'},
		field_order=['email', 'date_joined', 'last_login'],
		field_serializer_map={'date_joined': (lambda x: (x or '') and timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p")),
							  'last_login': (lambda x: (x or '') and timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p")),
		},)


class UserDataView(FeedDataView):

	token = usr_filter_paging().token
	
	def get_queryset(self):
		query = super(UserDataView, self).get_queryset().annotate(
			last_mail_senton=F('bitsuser_user__last_followup_mail_sent_on'),
			mails_count=F('bitsuser_user__mails_sent_count'),
						app_fee_mail_sent=F('bitsuser_user__last_followup_app_fee_mail_sent'),
						app_fee_mail_count=F('bitsuser_user__app_fee_mail_sent_count'),
			pg_code = F('studentcandidateapplication_requests_created_5__program__program_code'),
			pg_name = Case(
				When(studentcandidateapplication_requests_created_5__program__isnull=False, 
					then=Concat('studentcandidateapplication_requests_created_5__program__program_name',
						Value(' - '),
						'studentcandidateapplication_requests_created_5__program__program_code',
						Value(' ('),
						'studentcandidateapplication_requests_created_5__program__program_type',
						Value(')')),),
				default=Value(''),
				output_field=CharField(),
				),
			program_registered_for=Case(
				When(bitsuser_user__register_program_id__program_code__isnull=False,
					 then='bitsuser_user__register_program_id__program_code'),
				default=Value(''),
			),
			utm_source_first=Case(
				When(bitsuser_user__utm_source_first__isnull=False,
					 then='bitsuser_user__utm_source_first'),
				default=Value(''),
			),
			utm_medium_first=Case(
				When(bitsuser_user__utm_medium_first__isnull=False,
					 then='bitsuser_user__utm_medium_first'),
				default=Value(''),
			),
			utm_campaign_first=	Case(
				When(bitsuser_user__utm_campaign_first__isnull=False,
					 then='bitsuser_user__utm_campaign_first'),
				default=Value(''),
			),
			utm_source_last=Case(
				When(bitsuser_user__utm_source_last__isnull=False,
					 then='bitsuser_user__utm_source_last'),
				default=Value(''),
			),
			utm_medium_last=Case(
				When(bitsuser_user__utm_medium_last__isnull=False,
					 then='bitsuser_user__utm_medium_last'),
				default=Value(''),
			),
			utm_campaign_last=Case(
				When(bitsuser_user__utm_campaign_last__isnull=False,
					 then='bitsuser_user__utm_campaign_last'),
				default=Value(''),
			)
			)
		from_date = self.kwargs.get('fm_dt',None)
		to_date = self.kwargs.get('to_dt',None)

		from_date = from_date if not from_date == '00-00-0000' else None
		to_date = to_date if not to_date == '00-00-0000' else None

		if from_date and to_date :
			query=query.filter(date_joined__range=[
				dt.strptime(from_date,"%Y-%m-%d %H:%M:%S"),
				dt.strptime(to_date,"%Y-%m-%d %H:%M:%S")
				])
		elif from_date :
			query=query.filter(
				date_joined__gte=dt.strptime(from_date,"%Y-%m-%d %H:%M:%S")
				)
		elif to_date :
			query=query.filter(
				date_joined__lte=dt.strptime(to_date,"%Y-%m-%d %H:%M:%S")
				)

		return query


@staff_member_required
def userdataView(request):
	logger.info("{0} invoked funct.".format(request.user.email))
	query = get_user_model().objects.all().annotate(
		
		last_mail_senton=F('bitsuser_user__last_followup_mail_sent_on'),
		mails_count=F('bitsuser_user__mails_sent_count'),
				app_fee_mail_sent=F('bitsuser_user__last_followup_app_fee_mail_sent'),		
		app_fee_mail_count=F('bitsuser_user__app_fee_mail_sent_count'),
		pg_code = F('studentcandidateapplication_requests_created_5__program__program_code'),
		pg_name = Case(
				When(studentcandidateapplication_requests_created_5__program__isnull=False, 
					then=Concat('studentcandidateapplication_requests_created_5__program__program_name',
						Value(' - '),
						'studentcandidateapplication_requests_created_5__program__program_code',
						Value(' ('),
						'studentcandidateapplication_requests_created_5__program__program_type',
						Value(')')),),
				default=Value(''),
				output_field=CharField(),
				),
		)
	UserTable = usr_filter_paging()
	table = UserTable(query)

	return render(request, 'user_data_view.html', {
		'queryResult': query ,
		'form1':ToAndFromDate(),
		'table':table,},
	   )	


@staff_member_required
@require_http_methods(["POST"])
def userDateRefresh(request):
	logger.info("{0} invoked funct.".format(request.user.email))
	query =get_user_model().objects.all().annotate(
		last_mail_senton=F('bitsuser_user__last_followup_mail_sent_on'),
		mails_count=F('bitsuser_user__mails_sent_count'),
		)

	to_date=request.POST.get("to_date",None)
	from_date=request.POST.get("from_date",None)
	data={}
	if to_date :
		data['to_date'] = to_date
		t = to_date.split('-')
		to_date = dt( int(t[2]), int(t[1]), int(t[0]), 23, 59, 59 )
	

	if from_date :
		data['from_date'] = from_date
		t = from_date.split('-')
		from_date = dt( int(t[2]), int(t[1]), int(t[0]), 00, 00, 00 )

	if from_date and to_date:
		query=query.filter(date_joined__range=[from_date,to_date])
	elif from_date:
		query=query.filter(date_joined__gte=from_date)
	elif to_date:
		query=query.filter(date_joined__lte=to_date)

	UserTable = usr_filter_paging(from_date=from_date, 
		to_date=to_date)
	table = UserTable(query)

	return render(request, 'user_data_view.html', {
		'queryResult': query ,
		'form1':ToAndFromDate(data),
		'table':table,}
		)
	
@staff_member_required
def zip_all_photo_file(request):
	logger.info("{0} invoked funct.".format(request.user.email))
	if request.method == 'POST':
		logger.info("{0} inside POST request".format(request.user.email))
		form = ZipProgram(request.POST)
		if form.is_valid():
			logger.info("{0} POST request is valid".format(request.user.email))
			pg= form.cleaned_data['program']
			temp_file = tempfile.NamedTemporaryFile()
			with zipfile.ZipFile(temp_file, 'w', zipfile.ZIP_DEFLATED, True) as archive :
				doc = DocumentType.objects.get(document_name = 'APPLICANT PHOTOGRAPH')
				# sc=StudentCandidateApplication.objects.annotate(
				# 	s_id =F('candidateselection_requests_created_5550__student_id')).filter(
				# 	application_status__in = [x[0] for x in settings.APP_STATUS[:12]] ,
				# 	program = pg,
				# 	)
				cs = CandidateSelection.objects.filter(student_id__isnull=False,application__program=pg)	
				for x in cs:
					try:
						ad = ApplicationDocument.objects.get(application = x.application,
							document = doc)
						try:
							photo = get_thumbnailer(ad.file).get_thumbnail(settings.THUMBNAIL_ALIASES['']['zip_thumb'])
						except:
							photo = ad.file

						with photo as f:
							f.seek(0, 0)
							cont = f.read()

						name = x.student_id
						archive.writestr(os.path.join(pg.program_code,
							'{0}.{1}'.format(name,photo.name.split('.')[-1])),
							cont,
							zipfile.ZIP_DEFLATED)
					except Exception as e :logger.info("zip-error:{0}".format(e))

			wrapper = FileWrapper(temp_file)
			response = FileResponse(wrapper, 
				content_type='application/force-download')
			attachment = 'attachment; filename={0}-passport-photos.zip'.format(pg.program_code)
			response['Content-Disposition'] = attachment
			response['Content-Length'] = temp_file.tell()
			temp_file.seek(0)
			return response
	else :
		logger.info("{0} inside GET request".format(request.user.email))
		form = ZipProgram()
	logger.info("{0} ready to render".format(request.user.email))
	return render(request, 'zipfile_form.html',{'form':form})

@staff_member_required
def application_status_report(request):
	logger.info("{0} invoked funct.".format(request.user.email))
	if request.method == 'POST':
		logger.info("{0} inside POST request".format(request.user.email))
		form = StatusReportForm(request.POST)
		if form.is_valid():
			logger.info("{0} POST request is valid".format(request.user.email))
			from_date = form.cleaned_data.get('from_date') or dt(2015,01,01) # else dummy data
			to_date = form.cleaned_data.get('to_date') or dt.now()
			sca = StudentCandidateApplication.objects.filter(
				application_status__in=[
				settings.APP_STATUS[0][0],
				settings.APP_STATUS[12][0],
				settings.APP_STATUS[14][0],
				settings.APP_STATUS[13][0],
				],
				created_on_datetime__range=[from_date,to_date],
				).values('program__program_name','program__program_code',
				'admit_year').annotate(
				s_c = Count(
					Case(When(application_status =settings.APP_STATUS[12][0],
						then=F('application_status'),
						)
					)
					),#submitted
				u_c = Count(
					Case(When(application_status =settings.APP_STATUS[0][0],
						then=F('application_status'),
						)
					)
					),#uploaded
				in_pg_c = Count(
					Case(When(application_status =settings.APP_STATUS[14][0],
						then=F('application_status'),
						)
					)
					),#in progress
				f_p_c= Count(
					Case(When(application_status =settings.APP_STATUS[13][0],
						then=F('application_status'),
						)
					)
					),#fees paid
				g_total = F('s_c') + F('u_c') + F('in_pg_c') + F('f_p_c') #grand total
				)
			return render(request, 'application_status_report.html',{
				'form':form,
				'sca':sca,})
	else:
		logger.info("{0} inside GET request".format(request.user.email))
		form = StatusReportForm()
	logger.info("{0} ready to render".format(request.user.email))
	return render(request, 'application_status_report.html',{'form':form})

#changes made by sai for Applicant Archive Data 

@method_decorator([staff_member_required],name='dispatch')
class ArchiveHomeDataView(BaseArchiveHomeDataView):
	template_name = 'bits_archived/archivedView.html'

@method_decorator([staff_member_required],name='dispatch')
class ArchiveDataView(BaseArchiveDataView):
	token = arch_filter_paging().token

@method_decorator([staff_member_required],name='dispatch')
class FilterArchivalApplicant(BaseFilterArchivalApplicant):
	template_name = 'bits_archived/archivedView.html'

@method_decorator([archive_view_permission],name='dispatch')
class ApplicationAdminArchiveView(BaseApplicationAdminArchiveView):
	template_name = 'bits_archived/applicant_archive.html'

#code for  archive csv 
@method_decorator([staff_member_required],name='dispatch')
class CSVArchiveView(BaseCSVArchiveView):pass