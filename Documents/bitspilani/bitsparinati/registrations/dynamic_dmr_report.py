from django.shortcuts import render, redirect
from django.db import IntegrityError, transaction
from django.core.urlresolvers import reverse
from excel_response import ExcelResponse
from djqscsv import render_to_csv_response
from django_mysql.models import GroupConcat,ListCharField
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.db.models import *
from django.db.models.functions import Concat
from django.views.generic import TemplateView
from django.views.generic.base import *
from datetime import datetime as dt
from datetime import date, timedelta
from registrations.models import *
from .extra_forms import *
from .forms import *
from import_export.tmp_storages import MediaStorage as MS
from .bits_decorator import *
from django.views.decorators.cache import never_cache
from dateutil.parser import parse
from django.conf import settings
from django.http import JsonResponse,HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST, require_GET
from celery.result import AsyncResult
from django.core.serializers.json import DjangoJSONEncoder
from table.views import FeedDataView
from django.utils import timezone
from .tables import *
from import_export.tmp_storages import  *
from django.contrib.auth.decorators import login_required
from bits_admin.dynamic_views import  BaseApplicationExceptionView as BAdminEV
from django.db.models import Prefetch
from bits_rest import zest_statuses as ZS
import json
import datetime
import logging
import tablib
import operator
from itertools import chain
logger = logging.getLogger("main")

class BaseApplicationExceptionView(BAdminEV):pass

class BaseApplicationMilestoneReport(TemplateView):
	form_class = SCA_AdmitBatchProgramForm
	APP, ADM = '2','1'

	sca = StudentCandidateApplication.objects.prefetch_related(
			Prefetch('exceptionlistorgapplicants_app',
			 queryset=ExceptionListOrgApplicants.objects.filter(
			 	Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
			 	application__isnull = False,),
			 to_attr='eloa'),
			Prefetch('applicationpayment_requests_created_3',
			 queryset=ApplicationPayment.objects.all(), to_attr='ap'),
			).annotate(
			pk_adm = F('pk'),
			pk_app = F('pk'),
			full_prog = Concat('program__program_name',Value(' - '),
				'program__program_code',Value(' ('),
				'program__program_type',Value(')')),
			app_id = Case(
					When(candidateselection_requests_created_5550__new_application_id__isnull = True, 
						then=Concat('student_application_id',Value(' '))),
					default=Concat('candidateselection_requests_created_5550__new_application_id',Value(' ')),
					output_field=CharField(),
					),
			off_rej_date = F('candidateselection_requests_created_5550__offer_reject_mail_sent'),
			acc_rej_cand_date = F('candidateselection_requests_created_5550__accepted_rejected_by_candidate'),
			doc_sub_date = Max(
				Case(
					When(~(
							Q(application_status=settings.APP_STATUS[14][0])|
							Q(application_status=settings.APP_STATUS[3][0])
							),
						then=F('applicationdocument_requests_created_1__last_uploaded_on'),
						),
					),
				output_field=DateField(),
				),
			fee_waiver = F('pk'),

			profile_created_date = F('login_email__date_joined'),
			pre_selected_rejected_date=F('pre_selected_rejected_on_datetime'),
			adm_batch = F('admit_batch'),
			fee_paym_deadline_date =F('candidateselection_requests_created_5550__fee_payment_deadline_dt'),
			pgtype= F('program__program_type')
			)
	
	def pay_date(self, x, fee_type):
		for x in x.ap:
			if x.fee_type == fee_type:
				return timezone.localtime(x.payment_date).strftime("%d/%m/%Y") if x.payment_date else ' '
		else:
			return ''

	def waiver_type(self, x):
		return ' and '.join(
			map(lambda x:dict(FEE_TYPE_CHOICE)[x.exception_type].capitalize(),x.eloa)
			)

	def deadline_date(self,x):
		if not x.fee_paym_deadline_date:
			try:
				pld = ProgramLocationDetails.objects.get(program=x.program,
					location=x.current_location)
				text = timezone.localtime(pld.fee_payment_deadline_date).strftime("%d/%m/%Y ")
			except ProgramLocationDetails.DoesNotExist:
				text = '-'
		else:
			text = timezone.localtime(x.fee_paym_deadline_date).strftime("%d/%m/%Y ")

		return text


	csv_value = ['app_id','program','adm_batch',
		'application_status','profile_created_date','pre_selected_rejected_date','doc_sub_date',
		'off_rej_date','acc_rej_cand_date', 
		'pk_app',
		'pk_adm','fee_waiver',]

	csv_header = {
			'app_id':'Application ID',
			'program':'Program Applied For',
			'adm_batch':'Admit Batch',
			'application_status':'Current Status',
			'profile_created_date':'Profile Created Date',
			'pre_selected_rejected_date':'Pre-Selected / Rejected Date',
			'doc_sub_date':'Document Submitted Date(latest)',
			'off_rej_date':'Offer/Reject Release Date',
			'fee_paym_deadline_date':'Fee Payment Deadline Date',
			'acc_rej_cand_date':'Acceptance/Rejection by Candidate Date',
			'pk_app':'Application Fee Payment Date',
			'pk_adm':'Admission Fee Payment Date',
			'fee_waiver':'Fee Waiver'
		}

	xl_header = ['Application ID','Program Applied For','Admit Batch',
		'Current Status',
		'Profile Created Date',
		'Pre-Selected/ Rejected Date',
		'Document Submitted Date(latest)',
		'Offer/Reject Release Date',
		'Fee Payment Deadline Date',
		'Acceptance/Rejection by Candidate Date',
		'Application Fee Payment Date',
		'Admission Fee Payment Date',
		'Fee Waiver']

	def field_serializer_map(self): 
		return {
			'program': (lambda x: Program.objects.get(pk=x)),
			'profile_created_date': (lambda x: (x or '') and timezone.localtime(x).strftime("%d/%m/%Y")),
			'off_rej_date': (lambda x: (x or '') and timezone.localtime(x).strftime("%d/%m/%Y")),
			'acc_rej_cand_date': (lambda x: (x or '') and timezone.localtime(x).strftime("%d/%m/%Y")),
			'pk_app': (lambda x: self.pay_date(x, self.APP)),
			'pk_adm': (lambda x: self.pay_date(x, self.ADM)),
			'doc_sub_date': (lambda x: (x or '') and parse(x).strftime("%d/%m/%Y")),
			'fee_waiver':(lambda x: self.waiver_type(x)),
			'pre_selected_rejected_date': (lambda x: (x or '') and timezone.localtime(x).strftime("%d/%m/%Y")),
		}

	def get_context_data(self,search=None,**kwargs):
		context = super(BaseApplicationMilestoneReport, self).get_context_data(**kwargs)
		batch = self.request.GET.get('admit_batch', None)
		program =self.request.GET.get('program',None)
		ptype = self.request.GET.get('pg_type',None)
		data={'program':program, 'admit_batch': batch ,'pg_type':ptype}
		context['table'] = milestone_report_table(admit_batch=batch,program=program,pg_type=ptype)()
		context['title'] = 'Application Milestone Dates Report'
		context['form'] = SCA_AdmitBatchProgramForm(data)
		self.sca = self.sca.filter(program__program_type=ptype) if ptype else self.sca
		self.sca = self.sca.filter(adm_batch=batch) if batch else self.sca
		self.sca = self.sca.filter(program=program) if program else self.sca
		context['query'] = self.sca
		return context 

	def get(self, request, *args, **kwargs):
		search = request.GET.get('milestone_search',None)
		display_time = lambda x:timezone.localtime(x).strftime("%d/%m/%Y") if x else ' '

		def display_parse_time(instance):
			if isinstance(instance, dt):
				return instance.strftime("%d/%m/%Y ") if instance else '-'
			return parse(instance).strftime('%d/%m/%Y ') if instance else '-'

		context = self.get_context_data(search=search,**kwargs)
		self.sca = context['query'].filter(
			reduce(operator.and_, (
				Q(candidateselection_requests_created_5550__new_application_id__icontains = x )|
				Q(student_application_id__icontains = x )|
				Q(program__program_code__icontains = x )|
				Q(program__program_name__icontains = x )|
				Q(program__program_type__icontains = x )|
				Q(application_status__icontains = x )|
				Q(fee_waiver__icontains = x )|
				Q(full_prog__icontains = x )|
				Q(adm_batch__icontains = x )
				for x in search.split()
				)
			)) if search else self.sca
		sca_filter = self.sca 
		if 'CSV' in request.GET or 'EXCEL' in request.GET:
		
			data = [self.xl_header]
			data += [ [ x.app_id,
				str(Program.objects.get(pk=x.program.id)) if x.program else ' ',
				x.adm_batch,
				x.application_status,
				display_time(x.profile_created_date),
				display_time(x.pre_selected_rejected_date),
				display_parse_time(x.doc_sub_date),
				display_time(x.off_rej_date),
				self.deadline_date(x),
				display_time(x.acc_rej_cand_date),
				self.pay_date(x, self.APP),
				self.pay_date(x, self.ADM),
				self.waiver_type(x),
				] for x in self.sca]

			return ExcelResponse(data, 'Milestone_Report',force_csv=True if 'CSV' in request.GET else False)
		else:
			return super(BaseApplicationMilestoneReport, self).get(request,
				search=search, *args, **kwargs)

class BaseWaiverReport(TemplateView):

	header = ['Name','Admit Batch','Email ID','Fee Waiver Type',
	'Organisation','Program','Created On Datetime',
	'Application ID','Student ID','Current Status']
	form_class = ELOA_AdmitBatchForm


	def get_context_data(self,**kwargs):
		context = super(BaseWaiverReport, self).get_context_data(**kwargs)
		batch = self.request.GET.get('admit_batch', None) 
		eloa = ExceptionListOrgApplicants.objects.filter(Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),)
		eloa_with_count_two = eloa.filter(exception_type__in=['1','2']).values(
				'employee_email','program'
				).annotate(
				emp_count = Count('pk'),
				pks = GroupConcat('pk'), 
				).distinct().filter(emp_count=2)
		exclude_list = map(lambda x:int(x['pks'].split(',')[0]),eloa_with_count_two)
		include_list = map(lambda x:int(x['pks'].split(',')[1]),eloa_with_count_two)
		eloa = eloa.exclude(
					pk__in = exclude_list
				).annotate(emp_type=Case(
			When(
				Q(pk__in = include_list),
				then=Value('Application and Admission Fees')
				),
			When(
				Q(exception_type='2'),
				then=Value('Admission Fees')
				),
			When(
				Q(exception_type='1'),
				then=Value('Application Fees')
				),
			output_field=CharField(),
			),
		cod = F('application__created_on_datetime'),
		app_id = Case(
					When(application__candidateselection_requests_created_5550__new_application_id__isnull = True, 
						then=Concat('application__student_application_id',Value(' '))),
					default=Concat('application__candidateselection_requests_created_5550__new_application_id',Value(' ')),
					output_field=CharField(),
					),
		student_id = F('application__candidateselection_requests_created_5550__student_id'),
		app_status = F('application__application_status'),
		adm_batch = F('application__admit_batch'),
		full_prog = Concat('program__program_name',Value(' - '),
				'program__program_code',Value(' ('),
				'program__program_type',Value(')')),
		).distinct()


		eloa_archive = ExceptionListOrgApplicantsArchived.objects.filter(Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),)
		eloa_with_count_two_archive = eloa_archive.filter(
			exception_type__in=['1','2']
		).values('employee_email','program', 'run').annotate(
			emp_count=Count('pk'),
			pks=GroupConcat('pk'), 
		).distinct().filter(emp_count=2)
		exclude_archive_list = map(lambda x:int(x['pks'].split(',')[0]), eloa_with_count_two_archive)
		include_archive_list = map(lambda x:int(x['pks'].split(',')[1]), eloa_with_count_two_archive)
		eloa_archive = eloa_archive.exclude(
				pk__in = exclude_archive_list
			).annotate(emp_type=Case(
			When(
				Q(pk__in = include_archive_list),
				then=Value('Application and Admission Fees')
				),
			When(
				Q(exception_type='2'),
				then=Value('Admission Fees')
				),
			When(
				Q(exception_type='1'),
				then=Value('Application Fees')
				),
			output_field=CharField(),
			),

			cod = F('application__created_on_datetime'),
			app_id = Case(
						When(application__candidateselectionarchived_1__new_application_id__isnull = True, 
							then=Concat('application__student_application_id',Value(' '))),
						default=Concat('application__candidateselectionarchived_1__new_application_id',Value(' ')),
						output_field=CharField(),
						),
			student_id = F('application__candidateselectionarchived_1__student_id'),
			app_status = F('application__application_status'),
			adm_batch = F('application__admit_batch'),
			full_prog = F('program'),

		).distinct()


		context['table'] = waiver_report_table(self.request.GET.get('admit_batch'))()
		context['title'] = 'Fee Waiver Report'
		context['query'] = eloa.filter(application__admit_batch=batch) if batch else eloa
		context['query_archive'] = eloa_archive.filter(application__admit_batch=batch) if batch else eloa_archive
		context['form'] = self.form_class(initial=self.request.GET)
		return context


	def get(self, request, *args, **kwargs):
		response=super(BaseWaiverReport, self).get(request, *args, **kwargs)

		if 'report_xls' in request.GET:
			search = request.GET.get('fee_waiver_search',None)
			query_context = response.context_data['query']
			query_context_archive = response.context_data['query_archive']

			eloa = query_context.filter(
				reduce(operator.and_, (
					Q(employee_name__icontains = x )|
					Q(employee_email__icontains = x)|
					Q(program__program_code__icontains = x )|
					Q(program__program_name__icontains = x )|
					Q(program__program_type__icontains = x )|
					Q(org__org_name__icontains = x )|
					Q(app_status__icontains = x )|
					Q(app_id__icontains = x )|
					Q(full_prog__icontains = x )|
					Q(student_id__icontains = x )|
					Q(adm_batch__icontains  = x)
					for x in search.split()
					)
				)) if search else query_context

			eloa_archive = query_context_archive.filter(
				reduce(operator.and_, (
					Q(employee_name__icontains = x )|
					Q(employee_email__icontains = x)|
					Q(program__icontains = x )|
					Q(org__icontains = x )|
					Q(app_status__icontains = x )|
					Q(app_id__icontains = x )|
					Q(full_prog__icontains = x )|
					Q(student_id__icontains = x )|
					Q(adm_batch__icontains  = x)
					for x in search.split()
					)
				)) if search else query_context_archive

			eloa_list=eloa.values('employee_name','adm_batch','employee_email',
				'emp_type','org_id','program_id','cod','app_id','student_id','app_status')

			eloa_list_archive=eloa_archive.values('employee_name','adm_batch','employee_email',
				'emp_type','org','program','cod','app_id','student_id','app_status')

			data = [ self.header ] 
			data += [ [x['employee_name'],x['adm_batch'],x['employee_email'],
				x['emp_type'],
				CollaboratingOrganization.objects.get(pk=x['org_id']).org_name,
				str(Program.objects.get(pk=x['program_id'])),
				timezone.localtime(x['cod']).strftime("%d-%m-%Y %I:%M %p") if x['cod'] else '',
				x['app_id'],x['student_id'],
				x['app_status']] for x in eloa_list.iterator()
				 ]
			data += [ [x['employee_name'],x['adm_batch'],x['employee_email'],
				x['emp_type'],x['org'],x['program'],
				timezone.localtime(x['cod']).strftime("%d-%m-%Y %I:%M %p") if x['cod'] else '',
				x['app_id'],x['student_id'],
				x['app_status']] for x in eloa_list_archive.iterator()
				 ]
			return ExcelResponse(data, 'Fee_Waiver_Report')

		else:
			return response

class BaseDMR(TemplateView):
	def get_context_data(self, program_type=None, title=None, **kwargs):
		context = super(BaseDMR, self).get_context_data(**kwargs)
		ap_fees_paid = map(lambda x :x[0],settings.APP_STATUS[:12]+settings.APP_STATUS[13:])
		ap_form_sub = map(lambda x :x[0],settings.APP_STATUS[:12]+settings.APP_STATUS[15:])
		ap_in_prog = [settings.APP_STATUS[14][0], settings.APP_STATUS[3][0], settings.APP_STATUS[16][0]]
		ap_off = [settings.APP_STATUS[6][0], settings.APP_STATUS[10][0],
					settings.APP_STATUS[9][0], settings.APP_STATUS[11][0]]
		ap_accp = [settings.APP_STATUS[9][0], settings.APP_STATUS[11][0]]
		ap_adm_fees_paid = [settings.APP_STATUS[11][0],]

		pg = Program.objects.filter(
			program_type__in = program_type,
			active_for_applicaton_flag=True,
			).values('pk','program_code','program_name').annotate(
			down = Count(F('studentcandidateapplication_requests_created_6__application_status')),
			ap_fee_paid = Count(
				Case(
					When(
						studentcandidateapplication_requests_created_6__application_status__in = ap_fees_paid,
						then=F('studentcandidateapplication_requests_created_6__application_status'),
						)
					)
				),
			ap_form_sub = Count(
				Case(
					When(
						studentcandidateapplication_requests_created_6__application_status__in = ap_form_sub,
						then=F('studentcandidateapplication_requests_created_6__application_status'),
						)
					)
				),
			prog = Count(
				Case(
					When(
						studentcandidateapplication_requests_created_6__application_status__in = ap_in_prog,
						then=F('studentcandidateapplication_requests_created_6__application_status'),
						)
					)
				),
			off = Count(
				Case(
					When(
						studentcandidateapplication_requests_created_6__application_status__in = ap_off,
						then=F('studentcandidateapplication_requests_created_6__application_status'),
						)
					)
				),
			accepted = Count(
				Case(
					When(
						studentcandidateapplication_requests_created_6__application_status__in = ap_accp,
						then=F('studentcandidateapplication_requests_created_6__application_status'),
						)
					)
				),
			fees_paid = Count(
				Case(
					When(
						studentcandidateapplication_requests_created_6__application_status__in = ap_adm_fees_paid,
						then=F('studentcandidateapplication_requests_created_6__application_status'),
						)
					)
				),
			).order_by('program_code')

		total_pg = pg.aggregate(
			total_down=Sum(F('down')),
			total_ap_fee_paid = Sum(F('ap_fee_paid')),
			total_ap_form_sub = Sum(F('ap_form_sub')),
			total_prog = Sum(F('prog')),
			total_off = Sum(F('off')),
			total_accepted = Sum(F('accepted')),
			total_fees_paid = Sum(F('fees_paid')),
			)
		context['total_pg'] = total_pg
		context['pg'] = pg
		context['title'] = title
		return context

	def get(self, request,program_type=None, title=None, *args, **kwargs):
		if 'report_xls' in request.GET:
			context = self.get_context_data(program_type=program_type, title=title, **kwargs)
			pg_xl = [['Code','Programme','Downloaded',
				'Application Fees Paid','Application Forms Submitted',
				'InProgress','Offered','Accepted',
				'Fee Paid'],]
			pg_xl += [ [x['program_code'],x['program_name'],
				x['down'],x['ap_fee_paid'],x['ap_form_sub'],
				x['prog'],x['off'],x['accepted'],x['fees_paid'] ] for x in context['pg']]
			return ExcelResponse(pg_xl,'DMR-Report')
		else:
			return super(BaseDMR, self).get(request,program_type=program_type, title=title, *args, **kwargs)

class BaseProgramChangeReport(TemplateView):
	form_class = SCA_AdmitBatchForm

	xl_header = ['Application ID(new ID - old ID)','Applied On',
		'Program Change Done On',
		'Admit Batch',
		'Student ID',
		'Old Student ID',
		'Program Applied for',
		'New Program',
		'Current Status',]

	def get_context_data(self, **kwargs):
		context = super(BaseProgramChangeReport, self).get_context_data(**kwargs)
		batch = self.request.GET.get('admit_batch', None)
		query = StudentCandidateApplication.objects.filter(
			candidateselection_requests_created_5550__new_sel_prog__isnull=False)
		data = {}

		query = query.annotate(
			app_id = Case(
				When(candidateselection_requests_created_5550__new_application_id=None, 
					then=Concat('student_application_id',Value(' '))),
				default=Concat('candidateselection_requests_created_5550__new_application_id',Value(' ')),
				output_field=CharField(),
				),
			new_prog = Concat('program__program_name',Value(' - '),
				'program__program_code',Value(' ('),
				'program__program_type',Value(')')),
			student_id = F('candidateselection_requests_created_5550__student_id'),
			old_student_id = F('candidateselection_requests_created_5550__old_student_id'),
			old_prog = Concat('candidateselection_requests_created_5550__new_sel_prog__program_name',Value(' - '),
				'candidateselection_requests_created_5550__new_sel_prog__program_code',Value(' ('),
				'candidateselection_requests_created_5550__new_sel_prog__program_type',Value(')')),
			prog_changed_on = F('candidateselection_requests_created_5550__app_rej_by_su_rev_dt'),
			adm_batch = F('admit_batch'),
			).distinct()

		query_archive = StudentCandidateApplicationArchived.objects.filter(
			candidateselectionarchived_1__new_sel_prog__isnull=False).annotate(
			app_id = Case(
				When(
					candidateselectionarchived_1__new_application_id=None, 
					then=Concat(
						'student_application_id',
						Value(' ')
					)
				),
				default=Concat('candidateselectionarchived_1__new_application_id',Value(' ')),
				output_field=CharField(),
			),
			new_prog = Concat(
				'program__program_code',Value(' - '),
				'program__program_name',Value(' ('),
				'program__program_type',Value(')')
			),
			student_id = F('candidateselectionarchived_1__student_id'),
			old_student_id = F('candidateselectionarchived_1__old_student_id'),
			old_prog = F('candidateselectionarchived_1__new_sel_prog'),
			prog_changed_on = F('candidateselectionarchived_1__app_rej_by_su_rev_dt'),
			adm_batch = F('admit_batch'),	
		).distinct()

	

		ProgChangeReportTable = prog_change_report_paging(batch)
		table = ProgChangeReportTable()
		context['table'] = table
		context['query'] = query.filter(adm_batch=batch) if batch else query
		context['query_archive'] = query_archive.filter(adm_batch=batch) if batch else query_archive
		context['form'] = self.form_class(initial=self.request.GET)
		return context

	def get(self, request, *args, **kwargs):
		if 'report_xls' in request.GET:
			search = request.GET.get('pc_search_box',None)
			context = self.get_context_data()
			display_date = lambda x:timezone.localtime(x).strftime("%d/%m/%Y") if x else ' '
			pc = (context['query']).filter(
				reduce(operator.and_, (
					Q(app_id__icontains = x )|
					Q(old_prog__icontains = x)|
					Q(student_id__icontains = x )|
					Q(old_student_id__icontains = x )|
					Q(new_prog__icontains = x )|
					Q(application_status__icontains = x )|
					Q(adm_batch__icontains=x)
					for x in search.split()
					)
				)) if search else context['query']

			pc_archive = (context['query_archive']).filter(
				reduce(operator.and_, (
					Q(app_id__icontains = x )|
					Q(old_prog__icontains = x)|
					Q(student_id__icontains = x )|
					Q(old_student_id__icontains = x )|
					Q(new_prog__icontains = x )|
					Q(application_status__icontains = x )|
					Q(adm_batch__icontains=x)
					for x in search.split()
					)
				)) if search else context['query_archive']

			queryset=chain(
					pc.values('app_id','created_on_datetime','old_prog','adm_batch',
						'student_id','old_student_id','new_prog','prog_changed_on','application_status').iterator(),
					pc_archive.values('app_id','created_on_datetime','old_prog','adm_batch',
						'student_id','old_student_id','new_prog','prog_changed_on','application_status').iterator(),
					)

			data = [ self.xl_header ] 

			data += [ [x['app_id'],display_date(x['created_on_datetime']),
				display_date(x['prog_changed_on']),x['adm_batch'],x['student_id'],x['old_student_id'],x['old_prog'],x['new_prog'],
				x['application_status']] for x in queryset
				]
			return ExcelResponse(data, 'Program_Change_Report')
		else:
			return super(BaseProgramChangeReport, self).get(request, *args, **kwargs)


class BaseProgramLocationReport(TemplateView):
	def get_context_data(self, program_type=None, content_title=None, **kwargs):
		context = super(BaseProgramLocationReport,self).get_context_data(**kwargs)
		query = StudentCandidateApplication.objects.select_related('program',
			'login_email','current_location').filter(program__active_for_applicaton_flag=True)
		program = Program.objects.annotate(
				full_pg = Concat('program_name',Value(' - '),
					'program_code',Value(' ('),
					'program_type',Value(')')),
				)
		bits_user = BitsUser.objects.select_related('user','source_program').annotate(
				full_pg = Concat('source_program__program_name',Value(' - '),
					'source_program__program_code',Value(' ('),
					'source_program__program_type',Value(')')),
				)
		eloa_adm_fees = ExceptionListOrgApplicants.objects.select_related(
			'application','program','org').filter(
				Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
				application__isnull=False,
				exception_type=2,
			).values_list('application',flat=True)

		eloa_app_fees = ExceptionListOrgApplicants.objects.select_related(
			'application','program','org').filter(
			Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
			application__isnull=False,
			exception_type=1,
			).values_list('application',flat=True)

		query = query.filter( program__program_type__in = program_type ) if program_type else query

		query = query.values('program','current_location')
		query = query.annotate(
			full_pg = Concat('program__program_name',Value(' - '),
				'program__program_code',Value(' ('),
				'program__program_type',Value(')')),
			loc_name = F('current_location__location_name'),
			sub=Count('pk',distinct = True,),#Total Application Form Downloads
			to_app_form_without_fee=Count(
				Case(
					When(~Q(application_status = settings.APP_STATUS[12][0]) & 
						~Q(exceptionlistorgapplicants_app__application__in=eloa_app_fees),
						then=F('login_email'),
						),
					),
				distinct = True,
				),#Total Application Form Payments (without Application Fee Waiver)

			to_app_form_with_fee=Count(
				Case(
					When(~Q(application_status = settings.APP_STATUS[12][0]) & 
						Q(pk__in=eloa_app_fees),
						then=F('login_email'),
						),
					),
				distinct = True,
				),#Total Application Form Payments (with Application Fee Waiver)
			doc_up_in_prog=Count(
				Case(
					When(application_status__in=[settings.APP_STATUS[16][0], 
						settings.APP_STATUS[14][0],
						 settings.APP_STATUS[3][0]],then=F('login_email')),
					),
				distinct = True,
				),#Documents Uploaded In Progress
			to_app_up_with_doc=Count(
				Case(
					When(application_status__in=[ 
						x[0] for x in settings.APP_STATUS[:12]+settings.APP_STATUS[15:]
						],
						then=F('login_email')),
					),
				distinct = True,
				),#Total Application uploaded with documents
			to_adm_off=Count(
				Case(
					When(application_status__in=[ settings.APP_STATUS[6][0],
						settings.APP_STATUS[9][0], settings.APP_STATUS[10][0],
						settings.APP_STATUS[11][0],
						],
						then=F('login_email')),
					),
				distinct = True,
				),#Total Admissions Offered 
			to_adm_accpted=Count(
				Case(
					When(application_status__in=[ 
						settings.APP_STATUS[9][0],
						settings.APP_STATUS[11][0],
						],
						then=F('login_email')),
					),
				distinct = True,
				),#Total Admissions Accepted
			to_adm_fees_paid_without_adm_fee_wav=Count(
				Case(
					When(Q(application_status=settings.APP_STATUS[11][0]) & 
						~Q(pk__in=eloa_adm_fees),
						then=F('login_email')),
					),
				distinct = True,
				),#Total Admissions Fees Paid (without admission fee waiver)
			to_adm_fees_paid_with_adm_fee_wav=Count(
				Case(
					When(Q(application_status__in=[settings.APP_STATUS[11][0],
						settings.APP_STATUS[9][0]]) & 
						Q(pk__in=eloa_adm_fees),
						then=F('login_email')),
					),
				distinct = True,
				),#Total Admission Fees Pad (with admission fee waiver)
			).order_by('current_location')

		context['query'] = query 
		status = [
			('Total Application Form Downloads','sub'),
			('Total Application Form Payments (without Application Fee Waiver)','to_app_form_without_fee'),
			('Total Application Form Payments (with Application Fee Waiver)','to_app_form_with_fee'),
			('Total Documents Uploaded In Progress','doc_up_in_prog'),
			('Total Application uploaded with documents','to_app_up_with_doc'),
			('Total Admissions Offered','to_adm_off'),
			('Total Admissions Accepted','to_adm_accpted'),
			('Total Admissions Fees Paid (without admission fee waiver)','to_adm_fees_paid_without_adm_fee_wav'),
			('Total Admission Fees Paid (with admission fee waiver)','to_adm_fees_paid_with_adm_fee_wav'),
		]

		pg_list = [x for x in program.filter(
			full_pg__in=query.values_list('full_pg',flat=True)
			).values_list('full_pg',flat=True).distinct().iterator() ]
		loc_list = [x for x in Location.objects.filter(
			location_name__in = query.values_list('loc_name',flat=True)
			).values_list('location_name',flat=True).distinct().iterator()]
		table = {}
		table['headers'] = tuple([' ',] + list(x.capitalize() for x in loc_list) + ['TOTAL',])
		table['blocks'] = []

		total_cols ={
			'col1' : Sum('sub'), 
			'col2' : Sum('to_app_form_without_fee'),
			'col3' : Sum('to_app_form_with_fee'), 
			'col4' : Sum('doc_up_in_prog'),
			'col5' : Sum('to_app_up_with_doc'), 
			'col6' : Sum('to_adm_off'), 
			'col7' : Sum('to_adm_accpted'),
			'col8' : Sum('to_adm_fees_paid_without_adm_fee_wav'),
			'col9' : Sum('to_adm_fees_paid_with_adm_fee_wav'),
		}

		status_data = [['Profile Total',] + [0 for x in loc_list] + [0,],]# grand total data initialization
		for (title,key) in status: 
			status_row = [title,]
			for loc in loc_list:
				status_row.append(0)
			status_row.append(0)
			status_data.append(status_row)
		
		for pg in pg_list:
			q = query.filter(full_pg = pg)
			
			pg_block = {}			
			pg_header = tuple(['{0}'.format(pg),] + list( '' for x in loc_list) + ['',])
			pg_block['header'] = pg_header

			data = []
			profile_count = bits_user.filter(full_pg = pg).count()
			data.append(tuple(['Profile Total',]+list( '' for x in loc_list)+[profile_count, ]))
			status_data[0][-1] += profile_count

			for st in range(len(status)):
				row = [status[st][0],]
				
				for loc in range(len(loc_list)):
					
					try:
						loc_total = q.get(loc_name=loc_list[loc])[status[st][1]]
						row.append(loc_total) 
						status_data[st+1][loc+1] += loc_total #status_data:zeroth index contain Profile Total so incremented by 1
					except StudentCandidateApplication.DoesNotExist:
						row.append('')
				row.append(sum(filter(None,row[1:]))) # sum of app status total 
				status_data[st+1][-1] = sum(status_data[st+1][1:-1]) #total zeroth column is status so index range 
				data.append(tuple(row))

			pg_block['data'] = tuple(data)
			table['blocks'].append(pg_block)

		table['status_total'] = {}
		table['status_total']['header'] = tuple(['GRAND TOTAL OF ALL PROGRAMS'] + list( '' for x in loc_list) + ['',])
		table['status_total']['data'] = status_data

		context['table'] = table
		context['title'] = content_title

		return context

	def get(self, request,program_type=None, content_title=None, *args, **kwargs):
		if 'report_xls' in request.GET:
			context = self.get_context_data(program_type=program_type, content_title=content_title, **kwargs)
			table=[]
			table.append(context['table']['headers'])
			for block in context['table']['blocks']:
				table.append(block['header'])
				for row in block['data']: table.append(row)

			table.append(context['table']['status_total']['header'])

			for x in context['table']['status_total']['data']:
				table.append(x)
		
			return ExcelResponse(table,'Program-Location-Report')
		else:
			return super(BaseProgramLocationReport, self).get(request,program_type=program_type, content_title=content_title, *args, **kwargs)


class BaseStudentCourseReport(TemplateView):
	header = ['Student ID','Name','Batch','Course 1','Course 2','Course 3','Course 4',]

	def get_context_data(self,**kwargs):
		context = super(BaseStudentCourseReport, self).get_context_data(**kwargs)
		course_list=FirstSemCourseList.objects.filter(is_elective=False)

		all_courses = Case(
			When(
				Q(
					Q(application__program__firstsemcourselist_requests_created_1__admit_year=F('application__admit_year')) &
					Q(application__program__firstsemcourselist_requests_created_1__active_flag=True) &
					Q(application__program__firstsemcourselist_requests_created_1__is_elective=False) 
				),
				then=F('application__program__firstsemcourselist_requests_created_1__course_id'),
			),
			When(
					Q(studentelectiveselection_1__course__course_id__isnull=False), 
					then=F('studentelectiveselection_1__course__course_id')
				),
			output_field=CharField(),
		)
		all_cources_concat = GroupConcat(all_courses, distinct=True, 
			output_field=ListCharField(base_field=CharField()))

		all_cources_concat_str= GroupConcat(all_courses, distinct=True, 
			output_field=CharField(),)
		
		cs=CandidateSelection.objects.exclude(Q(student_id__isnull=True) | Q(student_id='')).annotate(
			batch=F('application__admit_batch'),
			name=F('application__full_name'),
			courses=all_cources_concat,
			courses_str=all_cources_concat_str,
			)

		context['table'] = StudentCourseReportTable(cs)
		context['title'] = 'Student Course Registration Report'
		context['query'] = cs 
		return context

	def get_course(self,courses,index):
		course = '-'
		try:
			course = courses[index]
		except: pass
		return course

	def get(self, request, *args, **kwargs):
		if 'report_csv' in request.GET:
			search = request.GET.get('fee_waiver_search',None)
			context = self.get_context_data(**kwargs)
			cs = context['query'].filter(
				reduce(operator.and_, (
					Q(student_id__icontains = x )|
					Q(name__icontains = x)|
					Q(batch__icontains = x)|
					Q(courses_str__icontains = x)
					for x in search.split()
					)
				)) if search else context['query']

			cs_list=cs.values('student_id','name','batch','courses')
			data = [ self.header ] 
			data += [
				[
					x['student_id'],
					x['name'],
					x['batch'],
					self.get_course(x['courses'],0),
					self.get_course(x['courses'],1),
					self.get_course(x['courses'],2),
					self.get_course(x['courses'],3),
				] for x in cs_list.iterator()
				]
			return ExcelResponse(data, 'Student_Course_Registration_Report',force_csv=True)

		return super(BaseStudentCourseReport, self).get(request, *args, **kwargs)


class BaseDMRNonSpecific(TemplateView):
	program_type=PROGRAM_TYPE_CHOICES[2][0] #'non-specific'

	def conditions_list(self,Datedata):
		conditions = []

		conditions.append({ # Application Form Downloads
			'title' : 'Application Form Downloads',
			'total':{
				'cond':Q(created_on_datetime__lte = Datedata['start_date_time']),
				'then':F('student_application_id')
				},
			'earlier' : {
				'cond':Q(
					created_on_datetime__lt = Datedata['earlier_date_time']
					),
				'then': F('student_application_id'),
				},
			'weeks':{
				'cond':(lambda x : Q(created_on_datetime__range = [dt( x.year, x.month, x.day, 0, 0, 0 ),
					dt( x.year, x.month, x.day, 23, 59, 59 )])),
				'then': F('student_application_id'),
				},
			'filter':{
				'application_status__in':[ x[0] for x in settings.APP_STATUS ],
				},
			'exclude':{},
			
			})

		conditions.append({ #Total Application Form Payments(without fee waiver)
			'title' : 'Total Application Form Payments(without fee waiver)',
			'total':{
				'cond':Q(applicationpayment_requests_created_3__fee_type = Value('2')) & 
					Q(applicationpayment_requests_created_3__payment_date__lte = Datedata['start_date_time']),
				'then':F('student_application_id')
				},
			'earlier' : {
				'cond':Q(applicationpayment_requests_created_3__fee_type = Value('2')) & Q(
					applicationpayment_requests_created_3__payment_date__lt = Datedata['earlier_date_time']
					),
				'then': F('student_application_id'),
				},
			'weeks':{
				'cond':(lambda x : Q(applicationpayment_requests_created_3__fee_type = Value('2')) & 
					Q(applicationpayment_requests_created_3__payment_date__range = [dt( x.year, x.month, x.day, 0, 0, 0 ),
						dt( x.year, x.month, x.day, 23, 59, 59 )])),
				'then': F('student_application_id'),
				},
			'filter':{
				'application_status__in':[ x[0] for x in settings.APP_STATUS[13:] + settings.APP_STATUS[:12] ],
				},
			'exclude':{
				'login_email__email__in':ExceptionListOrgApplicants.objects.filter(
					Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
					application__isnull = False,
					exception_type='1',
					).values_list('employee_email',flat=True),
				},
			})

		conditions.append({#Total Application Form Submissions with Application Fee Waiver
			'title' : 'Total Application Form Submissions with Application Fee Waiver',
			'total':{
				'cond':Q(
					created_on_datetime__lte = Datedata['start_date_time']
					),
				'then':F('student_application_id')
				},
			'earlier' : {
				'cond':Q(
					created_on_datetime__lt = Datedata['earlier_date_time']
					),
				'then': F('student_application_id'),
				},

			'weeks':{
				'cond':(lambda x : Q(created_on_datetime__range = [dt( x.year, x.month, x.day, 0, 0, 0 ),
					dt( x.year, x.month, x.day, 23, 59, 59 )])),
				'then': F('student_application_id'),
				},

			'filter':{
				'application_status__in':[ x[0] for x in settings.APP_STATUS[13:] + settings.APP_STATUS[:12] ],
				'login_email__email__in':ExceptionListOrgApplicants.objects.filter(
					Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
					application__isnull = False,
					exception_type='1',
					).values_list('employee_email',flat=True),
				},

			'exclude':{},

			})

		conditions.append({ #Total Application Forms uploaded (Completed)
			'annotate' : {'max':Max('applicationdocument_requests_created_1__last_uploaded_on')},
			'title' : 'Total Application Forms uploaded (Completed)',
			'total' : Q(max__lte = Datedata['start_date_time']),
			'earlier' :Q(max__lt = Datedata['earlier_date_time']),
			'weeks':(lambda x : Q(max__range = [dt( x.year, x.month, x.day, 0, 0, 0 ),
					dt( x.year, x.month, x.day, 23, 59, 59 )])),

			'filter':{
				'application_status__in':[ x[0] for x in settings.APP_STATUS[:12] + settings.APP_STATUS[15:]],
				},
			'exclude':{},
			})

		conditions.append({ #Total Admissions Offered
			'title' : 'Total Admissions Offered',
			'total':{
				'cond':Q(
					candidateselection_requests_created_5550__offer_reject_mail_sent__lte = Datedata['start_date_time']
					),
				'then':F('student_application_id')
				},
			'earlier' : {
				'cond':Q(
					candidateselection_requests_created_5550__offer_reject_mail_sent__lt = Datedata['earlier_date_time']
					),
				'then': F('student_application_id'),
				},
			'weeks':{
				'cond':(lambda x : Q(candidateselection_requests_created_5550__offer_reject_mail_sent__range = [dt( x.year, x.month, x.day, 0, 0, 0 ),
					dt( x.year, x.month, x.day, 23, 59, 59 )])),
				'then': F('student_application_id'),

				},
			'filter':{
				'application_status__in':[settings.APP_STATUS[9][0],settings.APP_STATUS[11][0],settings.APP_STATUS[6][0],settings.APP_STATUS[10][0]],
				},
			'exclude':{},
			})

		conditions.append({ #Total Admissions Accepted
			'title' : 'Total Admissions Accepted',
			'total':{
				'cond':Q(
					candidateselection_requests_created_5550__accepted_rejected_by_candidate__lte = Datedata['start_date_time']
					),
				'then':F('student_application_id')
				},
			'earlier' : {
				'cond':Q(
					candidateselection_requests_created_5550__accepted_rejected_by_candidate__lt = Datedata['earlier_date_time']
					),
				'then': F('student_application_id'),
				},
			'weeks':{
				'cond':(lambda x : Q(candidateselection_requests_created_5550__accepted_rejected_by_candidate__range = [dt( x.year, x.month, x.day, 0, 0, 0 ),
					dt( x.year, x.month, x.day, 23, 59, 59 )])),
				'then': F('student_application_id'),

				},
			'filter':{
				'application_status__in':[settings.APP_STATUS[9][0],settings.APP_STATUS[11][0]],
				},
			'exclude':{},
			})

		conditions.append({#Total Admission Acceptances with Admission Fee waiver
			'title' : 'Total Admission Acceptances with Admission Fee waiver',
			'total':{
				'cond':Q(
					candidateselection_requests_created_5550__accepted_rejected_by_candidate__lte = Datedata['start_date_time']
					),
				'then':F('student_application_id')
				},
			'earlier' : {
				'cond':Q(
					candidateselection_requests_created_5550__accepted_rejected_by_candidate__lt = Datedata['earlier_date_time']
					),
				'then': F('student_application_id'),
				},
			'weeks':{
				'cond':(lambda x : Q(candidateselection_requests_created_5550__accepted_rejected_by_candidate__range = [dt( x.year, x.month, x.day, 0, 0, 0 ),
					dt( x.year, x.month, x.day, 23, 59, 59 )])),
				'then': F('student_application_id'),

				},

			'filter':{
				'application_status__in':[settings.APP_STATUS[9][0],settings.APP_STATUS[11][0]],
				'login_email__email__in':ExceptionListOrgApplicants.objects.filter(
					Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
					application__isnull = False,
					exception_type='2',
					).values_list('employee_email',flat=True),
				},
			'exclude':{},

			})

		conditions.append({ #Total Admissions Fees Paid(without fee waiver)
			'title' : 'Total Admissions Fees Paid(without fee waiver)',
			'total':{
				'cond':Q(applicationpayment_requests_created_3__fee_type = Value('1')) &
				Q(applicationpayment_requests_created_3__payment_date__lte = Datedata['start_date_time']),
				'then':F('student_application_id')
				},
			'earlier' : {
				'cond':Q(applicationpayment_requests_created_3__payment_date__lt=Datedata['earlier_date_time']) & 
					Q(applicationpayment_requests_created_3__fee_type = Value('1')),
				'then': F('student_application_id'),
				},
			'weeks':{
				'cond':(lambda x : Q(applicationpayment_requests_created_3__payment_date__range = [dt( x.year, x.month, x.day, 0, 0, 0 ),
					dt( x.year, x.month, x.day, 23, 59, 59 )]) & 
					Q(applicationpayment_requests_created_3__fee_type = Value('1'))),
				'then': F('student_application_id'),

				},
			'filter':{
				'application_status__in':[settings.APP_STATUS[11][0],],
				},
			'exclude':{
				'login_email__email__in':ExceptionListOrgApplicants.objects.filter(
					Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
					application__isnull = False,
					exception_type='2',
					).values_list('employee_email',flat=True),
				},
			})

		conditions.append({ #Total Admission Fees Paid (with Admission Loan)
			'title' : 'Total Admission Fees Paid with Admission Loan - Zest',
			'total':{
				'cond':Q(zestemitransaction_1__status=ZS.Active),
				'then':F('student_application_id')
				},
			'earlier' : {
				'cond':Q(zestemitransaction_1__approved_or_rejected_on__lt=Datedata['earlier_date_time']) & 
					Q(zestemitransaction_1__status=ZS.Active),
				'then': F('student_application_id'),
				},
			'weeks':{
				'cond':(lambda x : Q(zestemitransaction_1__approved_or_rejected_on__range=[dt( x.year, x.month, x.day, 0, 0, 0 ),
					dt( x.year, x.month, x.day, 23, 59, 59 )]) & 
					Q(zestemitransaction_1__status=ZS.Active)),
				'then': F('student_application_id'),

				},
			'filter':{
				'application_status__in':[settings.APP_STATUS[11][0],],
				},
			'exclude':{},
		})


		conditions.append({ #Total Admission Fees Paid (with Admission Loan)
			'title' : 'Total Admission Fees Paid with Admission Loan - Eduvanz',
			'total':{
				'cond':Q(applicationpayment_requests_created_3__payment_bank='eduvanz')&
					   Q(applicationpayment_requests_created_3__fee_type=Value('1')),
				'then':F('student_application_id')
				},
			'earlier' : {
				'cond':Q(applicationpayment_requests_created_3__payment_date__lt=Datedata['earlier_date_time']) & 
				  	   Q(applicationpayment_requests_created_3__fee_type='1') & 
					   Q(applicationpayment_requests_created_3__payment_bank='eduvanz'),
				'then': F('student_application_id'),
				},
			'weeks':{
				'cond':(lambda x : Q(applicationpayment_requests_created_3__payment_date__range=[dt( x.year, x.month, x.day, 0, 0, 0 ),
					    dt( x.year, x.month, x.day, 23, 59, 59 )]) & 
					    Q(applicationpayment_requests_created_3__fee_type='1') & 
					    Q(applicationpayment_requests_created_3__payment_bank='eduvanz')),
				'then': F('student_application_id'),

				},
			'filter':{
				'application_status__in':[settings.APP_STATUS[11][0],],
				},
			'exclude':{},
		})



		conditions.append({ #Total Admission Fees Paid (with Admission Loan)
			'title' : 'Total Admission Fees Paid with Admission Loan - Ezcred (ABFL)',
			'total':{
				'cond':Q(applicationpayment_requests_created_3__payment_bank='ezcred')&
					   Q(applicationpayment_requests_created_3__fee_type=Value('1')),
				'then':F('student_application_id')
				},
			'earlier' : {
				'cond':Q(applicationpayment_requests_created_3__payment_date__lt=Datedata['earlier_date_time']) & 
				  	   Q(applicationpayment_requests_created_3__fee_type='1') & 
					   Q(applicationpayment_requests_created_3__payment_bank='ezcred'),
				'then': F('student_application_id'),
				},
			'weeks':{
				'cond':(lambda x : Q(applicationpayment_requests_created_3__payment_date__range=[dt( x.year, x.month, x.day, 0, 0, 0 ),
					    dt( x.year, x.month, x.day, 23, 59, 59 )]) & 
					    Q(applicationpayment_requests_created_3__fee_type='1') & 
					    Q(applicationpayment_requests_created_3__payment_bank='ezcred')),
				'then': F('student_application_id'),

				},
			'filter':{
				'application_status__in':[settings.APP_STATUS[11][0],],
				},
			'exclude':{},
		})



		conditions.append({ #Total Admission Fees Paid (with Admission Loan)
			'title' : 'Total Admission Fees Paid with Admission Loan - Propelld',
			'total':{
				'cond':Q(applicationpayment_requests_created_3__payment_bank='propelld')&
					   Q(applicationpayment_requests_created_3__fee_type=Value('1')),
				'then':F('student_application_id')
				},
			'earlier' : {
				'cond':Q(applicationpayment_requests_created_3__payment_date__lt=Datedata['earlier_date_time']) & 
				  	   Q(applicationpayment_requests_created_3__fee_type='1') & 
					   Q(applicationpayment_requests_created_3__payment_bank='propelld'),
				'then': F('student_application_id'),
				},
			'weeks':{
				'cond':(lambda x : Q(applicationpayment_requests_created_3__payment_date__range=[dt( x.year, x.month, x.day, 0, 0, 0 ),
					    dt( x.year, x.month, x.day, 23, 59, 59 )]) & 
					    Q(applicationpayment_requests_created_3__fee_type='1') & 
					    Q(applicationpayment_requests_created_3__payment_bank='propelld')),
				'then': F('student_application_id'),

				},
			'filter':{
				'application_status__in':[settings.APP_STATUS[11][0],],
				},
			'exclude':{},
		})


		conditions.append({ #Total Admission Fees Paid (with Admission Loan)
			'title' : 'Total Admission Fees Paid - Paytm',
			'total':{
				'cond':Q(applicationpayment_requests_created_3__payment_bank='paytm')&
					   Q(applicationpayment_requests_created_3__fee_type=Value('1')),
				'then':F('student_application_id')
				},
			'earlier' : {
				'cond':Q(applicationpayment_requests_created_3__payment_date__lt=Datedata['earlier_date_time']) & 
				  	   Q(applicationpayment_requests_created_3__fee_type='1') & 
					   Q(applicationpayment_requests_created_3__payment_bank='paytm'),
				'then': F('student_application_id'),
				},
			'weeks':{
				'cond':(lambda x : Q(applicationpayment_requests_created_3__payment_date__range=[dt( x.year, x.month, x.day, 0, 0, 0 ),
					    dt( x.year, x.month, x.day, 23, 59, 59 )]) & 
					    Q(applicationpayment_requests_created_3__fee_type='1') & 
					    Q(applicationpayment_requests_created_3__payment_bank='paytm')),
				'then': F('student_application_id'),

				},
			'filter':{
				'application_status__in':[settings.APP_STATUS[11][0],],
				},
			'exclude':{},
		})


		return conditions

	def get_queryset(self, program_id):

		queryset = StudentCandidateApplication.objects.filter(Q(program__program_type=self.program_type,
			program__active_for_applicaton_flag=True,) | Q(program__program_type=self.program_type,
			program__active_for_admission_flag=True,)
			
			)
		return queryset.filter(program__pk=program_id) if program_id else queryset

	def get_context_data(self, **kwargs):
		context = super(BaseDMRNonSpecific, self).get_context_data(**kwargs)

		week = map(lambda x :timezone.now().date()-timezone.timedelta(days=x),range(7))
		data = tablib.Dataset()

		data.headers = tuple(['Title','Total','Earlier'] + [ x.isoformat() for x in week[::-1]])

		sca_query = self.get_queryset(self.request.GET.get('program') or None)

		sca = sca_query.values( 'student_application_id' )

		earlier_date = timezone.now().date()-timezone.timedelta(days=7)
		earlier_date_time = dt( earlier_date.year, earlier_date.month, earlier_date.day, 23, 59, 59 )
		start_date = timezone.now().date()
		start_date_time = dt( start_date.year, start_date.month, start_date.day, 23, 59, 59 )

		Datedata={
			'earlier_date':earlier_date,
			'earlier_date_time':earlier_date_time,
			'start_date':start_date,
			'start_date_time':start_date_time,
		}
		for cond in self.conditions_list(Datedata):
			query = sca.filter( **cond['filter'] ).exclude( **cond['exclude'] )

			if 'annotate' in cond:
				query = query.annotate( **cond['annotate'] ).filter(cond['total'])
				rows={
					data.headers[1] : query.count(),
					data.headers[2] : query.filter(cond['earlier']).count(),
				}
				rows.update({ x.isoformat() : query.filter(cond['weeks'](x)).count() for x in week })

			else:

				cols = {}
				cols.update({
					data.headers[1] : Count(
						Case(
							When( cond['total']['cond'], 
								then = cond['total']['then'] )
							)
						)
					})
				cols.update({
					data.headers[2] : Count(
						Case(
							When( cond['earlier']['cond'], 
								then = cond['earlier']['then'] )
							)
						)
					})
				cols.update({
					x.isoformat():Count(
						Case(
							When( cond['weeks']['cond'](x),
								then = cond['weeks']['then'] )
							)
						) for x in week }
					)
				rows = query.aggregate( **cols )

			rows[data.headers[0]] = cond['title']
			data.append(tuple(rows[x] for x in data.headers))

		context['data'] = data

		return context 

	def get(self, request, *args, **kwargs):
		response = super(BaseDMRNonSpecific, self).get(request, *args, **kwargs)

		if 'report_xls' in request.GET:
			return ExcelResponse(response.context_data['data'].dict, 'DMR-Daily_Movement')
		else:
			return response


class BaseDMRCertification(BaseDMRNonSpecific):
	program_type = PROGRAM_TYPE_CHOICES[5][0] #'certification'
	form_class = DMRCertificationForm

	def get_context_data(self, **kwargs):
		context = super(BaseDMRCertification, self).get_context_data(**kwargs)
		context['form'] = self.form_class(initial=self.request.GET)
		return context

	def conditions_list(self,Datedata):
		conditions=super(BaseDMRCertification, self).conditions_list(Datedata)

		conditions.insert(1,{ # Pre-Selections
			'title' : 'Pre-Selections',
			'total':{
				'cond':Q(pre_selected_rejected_on_datetime__lte = Datedata['start_date_time']),		
				'then':F('student_application_id'),
				},
			'earlier' : {
				'cond':Q(pre_selected_rejected_on_datetime__lt = Datedata['earlier_date_time']),
				'then': F('student_application_id'),
				},
			'weeks':{
				'cond':(lambda x : Q(pre_selected_rejected_on_datetime__range = [dt( x.year, x.month, x.day, 0, 0, 0 ),
					dt( x.year, x.month, x.day, 23, 59, 59 )])),
				'then': F('student_application_id'),
				},
			'filter':{
				'pre_selected_flag':StudentCandidateApplication.PRE_SELECTION_FLAG_CHOICES[1][0],
				'pre_selected_rejected_on_datetime__isnull':False,
				},
			'exclude':{},
			})

		conditions.insert(2,{ # Pre-Rejections
			'title' : 'Pre-Rejections',
			'total':{
				'cond':Q(pre_selected_rejected_on_datetime__lte = Datedata['start_date_time']),
				'then':F('student_application_id')
				},
			'earlier' : {
				'cond':Q(pre_selected_rejected_on_datetime__lt = Datedata['earlier_date_time']),
				'then': F('student_application_id'),
				},
			'weeks':{
				'cond':(lambda x : Q(pre_selected_rejected_on_datetime__range = [dt( x.year, x.month, x.day, 0, 0, 0 ),
					dt( x.year, x.month, x.day, 23, 59, 59 )])),
				'then': F('student_application_id'),
				},
			'filter':{
				'pre_selected_flag':StudentCandidateApplication.PRE_SELECTION_FLAG_CHOICES[2][0],
				'pre_selected_rejected_on_datetime__isnull':False,
				},
			'exclude':{},
			})

		return conditions

class BaseDMRCluster(BaseDMRNonSpecific):
	program_type = PROGRAM_TYPE_CHOICES[3][0] #'cluster'
	form_class = DMRClusterForm

	def get_context_data(self, **kwargs):
		context = super(BaseDMRCluster, self).get_context_data(**kwargs)
		context['form'] = self.form_class(initial=self.request.GET)
		return context

class BaseDMRSpecific(BaseDMRNonSpecific):
	program_type = PROGRAM_TYPE_CHOICES[1][0] #'specific'
	form_class = DMRSpecificForm

	def get_context_data(self, **kwargs):
		context = super(BaseDMRSpecific, self).get_context_data(**kwargs)
		context['form'] = self.form_class(initial=self.request.GET)
		return context

class BaseProgramAdmissionReport(TemplateView):
	return_table_func = lambda self, *args, **kwargs:pgm_adm_report_paging(*args, **kwargs)
	cs_model = CandidateSelection
	get_cs_queryset = lambda self:self.cs_model.objects.exclude(
			Q(student_id__isnull=True) | Q(student_id='')).values('application__program','application__admit_batch',).annotate(
			adm_count=Count('pk'),
			pgm = Concat('application__program__program_name',Value(' - '),
				'application__program__program_code',Value(' ('),
				'application__program__program_type',Value(')')),
			btc = F('application__admit_batch'),
			)
	def get_context_data(self, program_type=None, program=None, admit_batch=None,
		**kwargs):
		context = super(BaseProgramAdmissionReport, self).get_context_data(**kwargs)
		pg_code = Program.objects.get(pk=program).program_code if program else None
		query = self.get_cs_queryset()
		query = query.filter(application__program__program_type=program_type) if program_type else query
		query = query.filter(application__program__program_code=pg_code) if pg_code else query
		query = query.filter(application__admit_batch=admit_batch) if admit_batch else query	

		data={'pg_type':program_type, 'programs':program, 'admit_batch':admit_batch,}
		PARTable = self.return_table_func(program_type=program_type, program=program,
			admit_batch=admit_batch, ajax_url=self.ajax_url,)
		context['table'] = PARTable()
		context['title'] = 'Program Admissions Report'
		context['query'] = query.distinct() 
		context['form_data'] = pgm_adm_filter_form(data)
		return context

	def get(self, request, *args, **kwargs):
		program_type = request.GET.get('pg_type') or None
		program = request.GET.get('programs') or None
		admit_batch = request.GET.get('admit_batch') or None
		
		return super(BaseProgramAdmissionReport, self).get(request, 
			program_type=program_type, program=program, admit_batch=admit_batch,
			*args, **kwargs)