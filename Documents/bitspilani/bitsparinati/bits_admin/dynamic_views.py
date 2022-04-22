from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from excel_response import ExcelResponse
from django.shortcuts import render, HttpResponseRedirect
from djqscsv import render_to_csv_response
from django.db.models.functions import *
from django.db.models import *
from django.conf import settings
from django.shortcuts import render
from registrations.models import *
from bits_admin.models import *
from bits_admin.tables import *
from bits_admin.forms import *
from bits_rest.models import ZestEmiTransaction, InBoundCall, OutBoundCall , EduvanzApplication,EzcredApplication, PropelldApplication
from bits_rest import zest_statuses as ZS
from bits_rest.zest_utils import update_approved_emi
from django_mysql.models import GroupConcat, ListCharField, SetCharField
from django.utils.decorators import method_decorator
from dateutil.parser import parse
from bits_admin.utils.datetime import *
from bits_admin.utils.querysets import *
import operator
import logging
import cPickle
import pandas as pd
india = settings.INDIAN_TIME_ZONE
logger = logging.getLogger("main")


class ApplicantDataView(TemplateView):
	def get_context_data(self, **kwargs):
		query = StudentCandidateApplication.objects.prefetch_related(
			Prefetch('applicationpayment_requests_created_3',
				queryset=ApplicationPayment.objects.filter(fee_type=1,
					application__application_status=settings.APP_STATUS[11][0]),
				to_attr='adm'),
			Prefetch('applicationpayment_requests_created_3',
				queryset=ApplicationPayment.objects.filter(fee_type=2,
					application__application_status=settings.APP_STATUS[13][0]),
				to_attr='app'),

			)

		query = query.annotate(
			
			c_l = F('current_location__location_name'),
			app_id = Case(
				When(candidateselection_requests_created_5550__new_application_id=None, 
					then=Concat('student_application_id',Value(' '))),
				default=Concat('candidateselection_requests_created_5550__new_application_id',Value(' ')),
				output_field=CharField(),
				),
			pg_name = F('program__program_name'),
			email =F('login_email__email'),
			student_id = F('candidateselection_requests_created_5550__student_id'),
			last_updated = Case(
				When(application_status__in=[settings.APP_STATUS[0][0],settings.APP_STATUS[4][0],
					settings.APP_STATUS[14][0]], 
					then=Max('applicationdocument_requests_created_1__last_uploaded_on')
					),
				When(application_status__in=[settings.APP_STATUS[5][0],settings.APP_STATUS[7][0]], 
					then=F('candidateselection_requests_created_5550__selected_rejected_on')
					),
				When(application_status__in=[settings.APP_STATUS[6][0],settings.APP_STATUS[8][0]], 
					then=F('candidateselection_requests_created_5550__offer_reject_mail_sent')
					),
				When(application_status__in=[settings.APP_STATUS[9][0],settings.APP_STATUS[10][0]], 
					then=F('candidateselection_requests_created_5550__accepted_rejected_by_candidate')
					),
				When(application_status=settings.APP_STATUS[15][0], 
					then=F('candidateselection_requests_created_5550__es_to_su_rev_dt')
					),
				When(application_status=settings.APP_STATUS[16][0], 
					then=F('candidateselection_requests_created_5550__app_rej_by_su_rev_dt')
					),
				When(application_status__in=[settings.APP_STATUS[1][0],settings.APP_STATUS[2][0],
					settings.APP_STATUS[3][0],settings.APP_STATUS[12][0],settings.APP_STATUS[17][0]],
					then=F('last_updated_on_datetime'),
					),
				When(Q(application_status=settings.APP_STATUS[13][0],
						applicationpayment_requests_created_3__fee_type='2',), #datetime for application fees paid.
					then=Min('applicationpayment_requests_created_3__payment_date')
					),
				When(Q(application_status=settings.APP_STATUS[11][0],
						applicationpayment_requests_created_3__fee_type='1',), # datetime for admission fees paid.
					then=Max('applicationpayment_requests_created_3__payment_date')
					),
				When(application_status__in=[settings.APP_STATUS[18][0],settings.APP_STATUS[19][0]],
					then=F('pre_selected_rejected_on_datetime'),
					),
				default=F('last_updated_on_datetime'),
				output_field=DateTimeField()
				),

		)

		context = super(ApplicantDataView, self).get_context_data(**kwargs)

		SCATable = filter_paging()
		context['table'] = SCATable(query)
		context['form1'] = ToAndFromDate()
		context['queryResult'] = query

		return context
		
	def get(self, request, *args, **kwargs):
		logger.info("{0} invoked funct.".format(request.user.email))
		return super(ApplicantDataView, self).get(request,*args, **kwargs)

class DateRefreshView(TemplateView):

	def get_context_data(self, to_date=None, from_date=None, pg_type=None, program=None, status=None, admit_batch=None, **kwargs):
		query = StudentCandidateApplication.objects.all()
		data = {}
		query = query.filter(program__program_type=pg_type) if pg_type else query
		data['pg_type'] = pg_type
		query = query.filter(program=program) if program else query
		data['programs'] = program
		query = query.filter(application_status=status) if status else query
		data['status'] = status
		query = query.filter(admit_batch=admit_batch) if admit_batch else query
		data['admit_batch'] = admit_batch

		if to_date :
			data['to_date'] = to_date
			t=to_date.split('-')
			to_date = dt( int(t[2]), int(t[1]), int(t[0]), 23, 59, 59 )

		if from_date :
			data['from_date'] = from_date
			t=from_date.split('-')
			from_date = dt( int(t[2]), int(t[1]), int(t[0]), 00, 00, 00 )

		if from_date and to_date :
			query=query.filter(created_on_datetime__range=[from_date,to_date])
		elif from_date :
			query = query.filter(created_on_datetime__gte=from_date)
		elif to_date:
			query = query.filter(created_on_datetime__lte=to_date)	

		query = query.annotate(
			
			c_l = F('current_location__location_name'),
			app_id = Case(
				When(candidateselection_requests_created_5550__new_application_id=None, 
					then=Concat('student_application_id',Value(' '))),
				default=Concat('candidateselection_requests_created_5550__new_application_id',Value(' ')),
				output_field=CharField(),
				),
			pg_name = F('program__program_name'),
			email =F('login_email__email'),
			)

		SCATable = filter_paging( programs = program, status = status,
		 from_date = from_date, to_date = to_date, pg_type = pg_type, admit_batch = admit_batch)
		context = super(DateRefreshView, self).get_context_data(**kwargs)
		context['table'] = SCATable(query)
		context['queryResult'] = query 
		context['form1'] = filter_form(data)
		context['program'] = program
		context['status'] = status
		context['pg_type'] = pg_type
		context['from_date'] = from_date
		context['to_date'] = to_date
		context['admit_batch'] = admit_batch
		return context

	def get(self, request, *args, **kwargs):
		logger.info("{0} invoked funct.".format(request.user.email))
		to_date = request.GET.get("to_date",None)
		from_date = request.GET.get("from_date",None)
		pg_type = request.GET.get('pg_type',None)
		program = request.GET.get('programs',None)
		status = request.GET.get('status',None)
		admit_batch = request.GET.get('admit_batch',None)
		return super(DateRefreshView, self).get(request, to_date=to_date,
			from_date=from_date, pg_type=pg_type, 
			program=program, status=status, admit_batch=admit_batch,
			*args, **kwargs)


class BaseApplicationAdminArchiveView(TemplateView):
	def generate_query(self, model, **params):
		try:
			query = model.objects.get(**params)
		except model.DoesNotExist:
			query = None
		return query

	def get_context_data(self, pk=None, run_id=None,**kwargs):
		context = super(BaseApplicationAdminArchiveView, self).get_context_data(**kwargs)
		app = StudentCandidateApplicationArchived.objects.get(pk=pk,run=run_id)
		#context['form_title'] = Program.objects.get(program_code=app.program).form_title
		context['form'] = app
		context['edu1'] = StudentCandidateWorkExperienceArchived.objects.filter(application=app,run=run_id)
		context['qual1'] = StudentCandidateQualificationArchived.objects.filter(application=app,run=run_id)
		context['uploadFiles'] = ApplicationDocumentArchived.objects.filter(
			application=app,
			run=run_id
		)
		context['app_payment'] = self.generate_query(
			ApplicationPaymentArchived,
			fee_type=FEE_TYPE_CHOICES[2][0],
			application=app,
			run=run_id
		)

		context['adm_payment'] = self.generate_query(
			ApplicationPaymentArchived,
			fee_type=FEE_TYPE_CHOICES[1][0],
			application=app,
			run=run_id
		)

		context['except_org_app'] = self.generate_query(
			ExceptionListOrgApplicantsArchived,
			employee_email=app.login_email, 
			run=run_id,
			program=app.program,
			exception_type=FEE_TYPE_CHOICE[1][0]
		)

		except_org_adm = self.generate_query(
			ExceptionListOrgApplicantsArchived,
			employee_email=app.login_email, 
			run=run_id,
			program=app.program,
			exception_type=FEE_TYPE_CHOICE[2][0]
		)

		context['emi_record'] = self.generate_query(
			ZestEmiTransactionArchived,
			application=app,
			run=run_id,
			program=app.program,
			status=ZS.Active
		)

		context['is_admission_complete'] = (
			app.application_status in [settings.APP_STATUS[11][0], settings.APP_STATUS[9][0]]
			if except_org_adm else 
			app.application_status == settings.APP_STATUS[11][0]
		)

		pgm = self.generate_query(Program, program_code=app.program)
		context['form_title'] = pgm.form_title if pgm else app.program

		cs_arch = self.generate_query(
			CandidateSelectionArchived,
			application=app,
			run=run_id
		)
		context['cs_arch'] = cs_arch
		
		context['bits_rejection_reason'] = ( 
			cPickle.loads(str(cs_arch.bits_rejection_reason)) if 
				cs_arch and
				not cs_arch.bits_rejection_reason == cPickle.dumps(None) and
				cs_arch.bits_rejection_reason	
			else None 
		)

		context['except_org_adm'] = except_org_adm

		return context


class BaseFilterArchivalApplicant(TemplateView):

	def get_context_data(self, to_date=None, from_date=None, pg_type=None, 
			program=None, status=None, admit_batch=None, **kwargs):
		context = super(BaseFilterArchivalApplicant, self).get_context_data(**kwargs)
		query = StudentCandidateApplicationArchived.objects.all()
 
		data = {}
		data['programs'] = program
		data['pg_type'] = pg_type
		data['status'] = status
		data['admit_batch'] = admit_batch

		if to_date :
			data['to_date'] = to_date
			t=to_date.split('-')
			to_date = dt( int(t[2]), int(t[1]), int(t[0]), 23, 59, 59 )
		
		if from_date :
			data['from_date'] = from_date
			t=from_date.split('-')
			from_date = dt( int(t[2]), int(t[1]), int(t[0]), 00, 00, 00 )


		query = query.filter(program__program_type=pg_type ) if pg_type else query
		query = query.filter(program=program) if program else query
		query = query.filter(application_status=status) if status else query
		query = query.filter(admit_batch=admit_batch) if admit_batch else query
		
		if from_date and to_date :
			query=query.filter(created_on_datetime__range=[from_date,to_date])
		elif from_date :
			query = query.filter(created_on_datetime__gte=from_date)
		elif to_date:
			query = query.filter(created_on_datetime__lte=to_date)
		
		SCATable = arch_filter_paging(programs = program, status = status,
		 from_date = from_date, to_date = to_date, pg_type = pg_type, admit_batch=admit_batch,)

		context['queryResult'] =  query 
		context['form1'] = filter_form_arch(data)
		context['table'] = SCATable(query)
		context['to_date']=to_date
		context['from_date']=from_date
		context['pg_type']=pg_type
		context['program']=program
		context['status']=status
		context['admit_batch'] = admit_batch

		return context

	def get(self, request, *args, **kwargs):
		to_date = request.GET.get("to_date",None)
		from_date = request.GET.get("from_date",None)
		pg_type = request.GET.get('pg_type',None)
		program = request.GET.get('programs',None)
		status = request.GET.get('status',None)
		admit_batch = request.GET.get('admit_batch',None)

		return super(BaseFilterArchivalApplicant, self).get(request, to_date=to_date,
			from_date=from_date, pg_type=pg_type, 
			program=program, status=status, admit_batch=admit_batch,
			*args, **kwargs)


class BaseArchiveHomeDataView(TemplateView):
	def get_context_data(self, **kwargs):
		context = super(BaseArchiveHomeDataView, self).get_context_data(**kwargs)
		query = StudentCandidateApplicationArchived.objects.annotate(
				pg_app = Concat('program__program_code',Value(' - '),
					'program__program_name',Value(' ('),
					'program__program_type',Value(')')
					),
				app_id = Case(
					When(
						candidateselectionarchived_1__new_application_id__isnull=False, 
						then = F('candidateselectionarchived_1__new_application_id')
				 ),
				default=F('student_application_id'),
				output_field=CharField(),
			),
		)

		SCATable = arch_filter_paging()
		table = SCATable(query)

		context['queryResult'] = query 
		context['form1'] = ToAndFromDateArch()
		context['table'] = table
		return context

class BaseApplicationExceptionView(TemplateView):
	display_date = lambda self,x:timezone.localtime(x).strftime("%d/%m/%Y") if x else ' '

	def queryset(self):
		query = ApplicantExceptions.objects.filter(
				transfer_program__isnull = False
				).annotate(
				app_id = F('application__student_application_id'),
				pg_app = Concat('program__program_code',Value(' - '),
					'program__program_name',Value(' ('),
					'program__program_type',Value(')')
					),
				pg_adm = Concat('transfer_program__program_code',Value(' - '),
					'transfer_program__program_name',Value(' ('),
					'transfer_program__program_type',Value(')')
					),
				stud_id = F('application__candidateselection_requests_created_5550__student_id'),
				cur_status = F('application__application_status'),
				app_on = F('application__created_on_datetime'),
				)
		return query

	def get_context_data(self, **kwargs):
		context = super(BaseApplicationExceptionView, self).get_context_data(**kwargs)
		table = ApplcantExceptionTable(self.query)
		context['table'] = table
		context['query'] = self.query
		return context

	def get(self, request, *args, **kwargs):
		search = request.GET.get('pt_search_box',None)
		self.query = self.queryset()
		self.query = self.query.filter(
				reduce(operator.and_, (
					Q(app_id__icontains = x )|
					Q(pg_app__icontains = x)|
					Q(pg_adm__icontains = x )|
					Q(stud_id__icontains = x )|
					Q(cur_status__icontains = x )|
					Q(applicant_email__icontains = x )
					for x in search.split()
					)
				)) if search else self.query

		if 'report_xls' in request.GET:
			pg_xl = [['Application Email ID','Program Applied For ','Program Admitted To',
				'Student ID','Application ID',
				'Applied On','Current Status',],]
			pg_xl += [ [x.applicant_email,x.pg_app,
				x.pg_adm,x.stud_id,x.app_id,
				self.display_date(x.app_on),x.cur_status, ] for x in self.query.iterator()]
			return ExcelResponse(pg_xl,'Program-Transfer-Report')
		else:
			return super(BaseApplicationExceptionView, self).get(request, *args, **kwargs)


class BaseElectiveSelectionsAppData(TemplateView):
	cs_model = CandidateSelection
	success_url = reverse_lazy('bits_admin_payment:view-elective-selections')
	csv_header={
		'student_id':'Student ID',	
		'full_name':'Name',
		'pg_name':'Program Applied for',
		'c_slot':'Elective Course Slot ID',	
		'c_id':'Elective Course ID',
		'c_unit':'Course Units',
		'c_name':'Elective Course Name',
		}

	csv_value =['student_id',
		'full_name',
		'pg_name',
		'c_slot',
		'c_id',
		'c_unit',
		'c_name',
		]
	get_cs_queryset = lambda self: self.cs_model.objects.all()
	get_elective_pg_list = lambda self: Program.objects.filter(
					firstsemcourselist_requests_created_1__active_flag=True,
					firstsemcourselist_requests_created_1__is_elective=True
					).distinct(),
	get_success_url = lambda self: self.success_url
	render_to_csv_response = lambda self, query, csv_kwargs: render_to_csv_response(query, **csv_kwargs)

	def ses_search(self, query, search):
		return query.filter(Q(student_id__icontains = search)|
					Q(full_name__icontains = search)|
					Q(pg_name__icontains = search)|
					Q(c_slot__icontains = search)|
					Q(c_id__icontains = search)|
					Q(c_name__icontains = search)) if search else query

	def get_context_data(self, query=None, program=None, **kwargs):
		context = super(BaseElectiveSelectionsAppData, self).get_context_data(**kwargs)
		data={'programs':program,}
		SCATable = elective_selections_paging(programs=program,)
		context['table'] = SCATable(query)
		context['form'] = program_filter_form(data)
		context['program'] = program
		context['query'] = query
		return context 

	def get(self, request, *args, **kwargs):
		search = request.GET.get('user_search') or None
		program = request.GET.get('programs') or None
		query = self.get_cs_queryset()
		query=query.filter(application__program__in=Program.objects.filter(
					firstsemcourselist_requests_created_1__active_flag=True,
					firstsemcourselist_requests_created_1__is_elective=True
					).distinct(),)
		query = query.filter(application__program=program) if program else query

		query = query.annotate(
			stud_id = Case(
				When(Q(student_id__isnull=True), then=Value(''),),
				default=F('student_id'),
				output_field=CharField(),
			),
			full_name = F('application__full_name'),
			pg_name = Concat(F('application__program__program_code'),
						Value(' - '),F('application__program__program_name')),
			c_slot = Case(
				When(Q(studentelectiveselection_1__course_id_slot__isnull=True), then=Value(''),),
				default=F('studentelectiveselection_1__course_id_slot__course_id'),
				output_field=CharField(),
			),
			c_id = Case(
				When(Q(studentelectiveselection_1__course__pk__isnull=True), then=Value(''),),
				default=F('studentelectiveselection_1__course__course_id'),
				output_field=CharField(),
			),
			c_unit = Case(
				When(Q(studentelectiveselection_1__course_units__pk__isnull=True), then=Value(''),),
				default=F('studentelectiveselection_1__course_units__course_units'),
				output_field=CharField(),
			),
			c_name = Case(
				When(Q(studentelectiveselection_1__course__pk__isnull=True), then=Value(''),),
				default=F('studentelectiveselection_1__course__course_name'),
				output_field=CharField(),
			),
			)

		query = self.ses_search(query, search)
		ses=StudentElectiveSelection.objects.filter(
			id__in=query.values_list('studentelectiveselection_1__id'),
				)

		if 'elective_csv' in request.GET:
			query = query.values(*self.csv_value)
			csv_kwargs = {
				'append_datestamp': True,
				'field_header_map': self.csv_header,
				'field_order': self.csv_value,
				'filename':'elective_selection_data'
			}
			return self.render_to_csv_response(query, csv_kwargs)

		elif 'lock_selection' in request.GET:
			for x in ses.iterator():
				x.is_locked = True
				x.save()
			return HttpResponseRedirect(self.get_success_url())

		elif 'unlock_selection' in request.GET:
			for x in ses.iterator():
				x.is_locked = False
				x.save()
			return HttpResponseRedirect(self.get_success_url())

		return super(BaseElectiveSelectionsAppData, self).get(request, query=query,
			program=program, *args, **kwargs)


class BaseEMIReportAppData(TemplateView):
	return_table_func = lambda self, *args, **kwargs: emi_report_paging(*args, **kwargs)
	zet_model = ZestEmiTransaction
	zet_archive_model = ZestEmiTransactionArchived

	get_zet_queryset = lambda self: self.zet_model.objects.all()
	get_zet_archive_queryset = lambda self: self.zet_archive_model.objects.all()

	render_to_csv_response = lambda self, query, csv_kwargs: render_to_csv_response(query, **csv_kwargs)

	csv_header = [
		'Application ID',
		'Admit Batch',
		'Student ID',
		'Name',
		'Program Applied for',
		'Program Type',
		'Loan Applied On',
		'Loan Approval / Rejection Date',
		'Zest Order ID',
		'Current Loan Status',
		'Application Status',
	]
		
	csv_value =['application__student_application_id',
		'application__admit_batch',
		'application__candidateselection_requests_created_5550__student_id',
		'application__full_name',
		'application__program__program_name',
		'application__program__program_type',
		'requested_on',
		'approved_or_rejected_on',
		'order_id',
		'status',
		'application__application_status',
		]

	csv_archive_value=csv_value[:]
	csv_archive_value[2] ='application__candidateselectionarchived_1__student_id'

	def field_serializer_map(self):
		return {
				'requested_on': (lambda x: timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p")),
				'approved_or_rejected_on': (lambda x: timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p")),
				'status': (lambda x:dict(ZS.ZEST_DISPLAY_STATUS_CHOICES).get(x, '-')),
				}

	def zet_search(self, query, search):
		return query.filter(
			reduce(operator.and_, 
				(
					Q(application__student_application_id__icontains = item)|
					Q(application__admit_batch__icontains = item)|
					Q(application__candidateselection_requests_created_5550__student_id__icontains = item)|
					Q(application__full_name__icontains = item)|
					Q(application__program__program_name__icontains = item)|
					Q(order_id__icontains = item)|
					Q(application__program__program_type__icontains = item)|
					Q(status__icontains = item)
					for item in search.split()
				)
			) 
		) if search else query


	def zet_archive_search(self, query_archive, search):
		return query_archive.filter(
			reduce(operator.and_, 
				(
					Q(application__student_application_id__icontains = item)|
					Q(application__admit_batch__icontains = item)|
					Q(application__candidateselectionarchived_1__student_id__icontains = item)|
					Q(application__full_name__icontains = item)|
					Q(application__program__program_name__icontains = item)|
					Q(order_id__icontains = item)|
					Q(application__program__program_type__icontains = item)|
					Q(status__icontains = item)
					for item in search.split()
				)
			) 
		) if search else query_archive



	def get_context_data(self, program=None, admit_batch = None, pg_type=None,status=None,  **kwargs):
		query = self.get_zet_queryset()
		pg_code = Program.objects.get(pk=program).program_code if program else None
		admit_batch = self.request.GET.get('admit_batch',None)
		ptype = self.request.GET.get('pg_type',None)
		query = query.filter(application__program__program_type=ptype) if ptype else query
		query = query.filter(application__program__program_code=pg_code ) if pg_code else query
		#query = query.filter(application__program=program) if program else query
		query = query.filter(application__admit_batch=admit_batch) if admit_batch else query
		query = query.filter(status=status) if status else query

		query_archive = self.get_zet_archive_queryset()
		query_archive = query_archive.filter(application__program__program_code=pg_code ) if pg_code else query_archive
		query_archive = query_archive.filter(application__program=program) if program else query_archive
		query_archive = query_archive.filter(application__admit_batch=admit_batch) if admit_batch else query_archive
		query_archive = query_archive.filter(application__program__program_type=ptype) if ptype else query_archive
		query_archive = query_archive.filter(status=status) if status else query_archive

		app_id_case = lambda : Case(
				When(Q(application__candidateselection_requests_created_5550__new_application_id__isnull=False,
					application__candidateselection_requests_created_5550__application__pk=F('pk')
					), 
					then=F('application__candidateselection_requests_created_5550__new_application_id')),
				default=F('application__student_application_id'),
				output_field=CharField(),
				)

		app_id_str = GroupConcat(app_id_case(), 
			distinct=True, 
			output_field=CharField()
		)

		query = query.annotate(
			sca_id=F('application__pk'),
			app_id = app_id_str,
			student_id=F('application__candidateselection_requests_created_5550__student_id'),
			full_name=F('application__full_name'),
			pg_name=Concat('application__program__program_name',Value(' - '),
				'application__program__program_type',Value(')')),
			app_status=F('application__application_status'),
			admit_batch=F('application__admit_batch'),
		).distinct()

		app_id_case_archive = lambda : Case(
				When(Q(application__candidateselectionarchived_1__new_application_id__isnull=False,
					application__candidateselectionarchived_1__application__pk=F('pk')
					), 
					then=F('application__candidateselectionarchived_1__new_application_id')),
				default=F('application__student_application_id'),
				output_field=CharField(),
				)

		app_id_str_archive = GroupConcat(app_id_case_archive(), 
			distinct=True, 
			output_field=CharField()
		)

		query_archive = query_archive.annotate(
			sca_id=F('application__pk'),
			app_id = app_id_str_archive,
			student_id=F('application__candidateselectionarchived_1__student_id'),
			full_name=F('application__full_name'),
			pg_name=Concat('application__program__program_name',Value(' - '),
				'application__program__program_type',Value(')')),
			app_status=F('application__application_status'),
			admit_batch=F('application__admit_batch'),

		).distinct()

		context = super(BaseEMIReportAppData, self).get_context_data(**kwargs)
		data={'programs':program, 'admit_batch': admit_batch ,'status':status,'pg_type':ptype}
		SCATable = self.return_table_func(programs=program, admit_batch=admit_batch, status=status,pg_type=ptype,
			ajax_url=self.ajax_url, action_url=self.action_url)
		context['table'] = SCATable()
		
		context['form'] = emi_filter_form(data)
		context['scaTotal'] = query.count()+query_archive.count()
		context['query'] = query
		context['query_archive'] = query_archive
		context['program'] = program
		context['admit_batch'] = admit_batch
		context['ptype'] = ptype
		context['status'] = status
		return context 

	def get(self, request, *args, **kwargs):
		program = request.GET.get('programs') or None
		admit_batch = request.GET.get('admit_batch') or None
		status = request.GET.get('status') or None
		ptype = request.GET.get('pg_type',None)
		search = request.GET.get('search') or None

		query = self.get_zet_queryset().distinct()
		pg_code = Program.objects.get(pk=program).program_code if program else None
		admit_batch = self.request.GET.get('admit_batch')
		ptype = self.request.GET.get('pg_type',None)
		query = query.filter(application__program__program_type=ptype) if ptype else query
		query = query.filter(application__program__program_code=pg_code ) if pg_code else query
		query = query.filter(application__admit_batch=admit_batch) if admit_batch else query
		# query = query.filter(application__program=program) if program else query
		query = query.filter(status=status) if status else query
		query = self.zet_search(query, search)

		query_archive = self.get_zet_archive_queryset().distinct()
		# query_archive = query_archive.filter(application__program=program) if program else query_archive
		query_archive = query_archive.filter(application__program__program_code=pg_code ) if pg_code else query_archive
		query_archive = query_archive.filter(application__admit_batch=admit_batch) if admit_batch else query_archive
		query_archive = query_archive.filter(status=status) if status else query_archive
		query_archive = query_archive.filter(application__program__program_type=ptype) if ptype else query_archive
		query_archive = self.zet_archive_search(query_archive, search)

		if 'emi_app_csv' in request.GET:
			query = query.values(*self.csv_value)
			query_archive = query_archive.values(*self.csv_archive_value)

			
			data = [self.csv_header, ] 
			data += [ [x['application__student_application_id'],x['application__admit_batch'],
					x['application__candidateselection_requests_created_5550__student_id'],
					x['application__full_name'],
					x['application__program__program_name'],
					x['application__program__program_type'],
					timezone.localtime(x['requested_on']).strftime("%d-%m-%Y %I:%M %p") if x['requested_on'] else '',
					timezone.localtime(x['approved_or_rejected_on']).strftime("%d-%m-%Y %I:%M %p") if x['approved_or_rejected_on'] else '',
					x['order_id'],x['status'],
					x['application__application_status']] for x in query.iterator()
				 ]
			data += [ [x['application__student_application_id'],x['application__admit_batch'],
					x['application__candidateselectionarchived_1__student_id'],
					x['application__full_name'],
					x['application__program__program_name'],
					x['application__program__program_type'],
					timezone.localtime(x['requested_on']).strftime("%d-%m-%Y %I:%M %p") if x['requested_on'] else '',
					timezone.localtime(x['approved_or_rejected_on']).strftime("%d-%m-%Y %I:%M %p") if x['approved_or_rejected_on'] else '',
					x['order_id'],x['status'],
					x['application__application_status']] for x in query_archive.iterator()
				 ]
			return ExcelResponse(data, 'Student_Loan_Application_data')

		return super(BaseEMIReportAppData, self).get(request, 
			program=program, admit_batch = admit_batch, status=status, pg_type=ptype,  *args, **kwargs)


class BaseDefDocsAppData(TemplateView):
	return_table_func = lambda self, *args, **kwargs: def_doc_paging(*args, **kwargs)

	csv_query=StudentCandidateApplication.objects.none()
	csv_header = [
		'Application ID',
		'Student ID',
		'Admit Batch',
		'Name',
		'Last Action/Update On',
		'Location',
		'Program Applied for',
		'Missing Document Name',
		'Application Status',
	]
		
	csv_value =['student_application_id',
		'candidateselection_requests_created_5550__student_id',
		'admit_batch',
		'full_name',
		'last_updated',
		'current_location__location_name',
		'program__program_name',
		'missing',
		'application_status',
		]

	csvs_value =['student_application_id',
		'candidateselection_requests_created_5550__student_id',
		'admit_batch',
		'full_name',
		'last_updated',
		'current_location__location_name',
		'program__program_name',
		'missing',
		'application_status',
		]
	
	
	missing_case = lambda self: Case(
			When(
				Q(
					Q(
						Q(applicationdocument_requests_created_1__file__isnull=True)|
						Q(applicationdocument_requests_created_1__file=Value(''))
					) |
					Q(
						Q(applicationdocument_requests_created_1__file__isnull=False) &
						Q(applicationdocument_requests_created_1__rejected_by_bits_flag=True)
					)
				) &
				Q(
					Q(applicationdocument_requests_created_1__program_document_map__deffered_submission_flag=True)|
					Q(applicationdocument_requests_created_1__program_document_map__mandatory_flag=True)
				) &
				Q(applicationdocument_requests_created_1__application=F('pk')),
				then=F('applicationdocument_requests_created_1__document__document_name'),
			),
			output_field=CharField(),
	)


	def get_def_data_queryset(self,pg1,status,admit_batch,search):
		
		pdm_program_list = ProgramDocumentMap.objects.filter(deffered_submission_flag=True).values_list('program__pk', flat=True)
		query = StudentCandidateApplication.objects.filter(program__in=pdm_program_list,
			application_status__in = [x[0] for x in list(settings.APP_STATUS[0:7]) + [settings.APP_STATUS[9],settings.APP_STATUS[11]] + list(settings.APP_STATUS[15:])],
														   # login_email__email='saksham.jain1998@gmail.com'
														   )

		missing_concat = GroupConcat(self.missing_case(), 
			distinct=True, 
			output_field=SetCharField(base_field=CharField())
		)
		missing_concat_str = GroupConcat(self.missing_case(), 
			distinct=True, 
			output_field=CharField()
		)

		app_id_case = lambda : Case(
				When(Q(candidateselection_requests_created_5550__new_application_id__isnull=False,
					candidateselection_requests_created_5550__application__pk=F('pk')
					), 
					then=F('candidateselection_requests_created_5550__new_application_id')),
				default=F('student_application_id'),
				output_field=CharField(),
				)

		app_id_str = GroupConcat(app_id_case(), 
			distinct=True, 
			output_field=CharField()
		)
		
		df = pd.DataFrame(list(query.values('program', 'student_application_id')))
		df2 = pd.DataFrame(
			list(ProgramDocumentMap.objects.filter(deffered_submission_flag=True).values('document_type', 'program','document_type__document_name')))
		s1 = pd.merge(df, df2, how='left', on=['program'])
		df3 = pd.DataFrame(list(
			ApplicationDocument.objects.values('application__student_application_id', 'document__id', 'reload_flag',
											   'rejected_by_bits_flag', 'program_document_map__program', 'file')))
		df3 = df3.rename(columns={'application__student_application_id': 'student_application_id',
								  'program_document_map__program': 'program',
								  'document__id': 'document_type'})
		s2 = pd.merge(s1, df3, how='left', on=["student_application_id", "document_type"])
		#To get def docs not submitted
		s3 = s2[s2['program_y'].isnull()]
		#To get def docs not submitted, some times stores doc as file with empty value
		s4 = s2[s2['file']=='']
		#To get def docs submitted but got rejected or deferred for later submission
		s5 = s2[s2.rejected_by_bits_flag.isin(['nan', True]) | s2.reload_flag.isin(['nan', True])]
		s6 = pd.concat([s3, s4, s5])
		s7 = s6.groupby('student_application_id').agg({'document_type__document_name': ', '.join}).reset_index()
		results = s6.student_application_id.unique()
		query = query.filter(Q(student_application_id__in=results))
		query=query.annotate(missing=Value('', output_field=CharField()))

		query = query.filter(program=pg1 ) if pg1 and pg1 > 0 else query
		query = query.filter(admit_batch=admit_batch ) if admit_batch and not admit_batch == 'n' else query
		query = query.filter(application_status=status ) if status and not status == 'n' else query
		query = deffered_doc_search(query, search)
		query = query.annotate(
			app_id = app_id_str,
			location = F('current_location__location_name'),
			pg_name = F('program__program_name'),
			student_id = F('candidateselection_requests_created_5550__student_id'),
			last_updated = Case(
				When(application_status__in=[settings.APP_STATUS[0][0],
					settings.APP_STATUS[4][0]], 
					then=Max(F('applicationdocument_requests_created_1__last_uploaded_on'))
					),
				When(application_status__in=[settings.APP_STATUS[5][0],settings.APP_STATUS[7][0]], 
					then=F('candidateselection_requests_created_5550__selected_rejected_on')
					),
				When(application_status__in=[settings.APP_STATUS[6][0],settings.APP_STATUS[8][0]], 
					then=F('candidateselection_requests_created_5550__offer_reject_mail_sent')
					),
				When(application_status__in=[settings.APP_STATUS[9][0],settings.APP_STATUS[10][0]], 
					then=F('candidateselection_requests_created_5550__accepted_rejected_by_candidate')
					),
				When(application_status=settings.APP_STATUS[15][0], 
					then=F('candidateselection_requests_created_5550__es_to_su_rev_dt')
					),
				When(application_status=settings.APP_STATUS[16][0], 
					then=F('candidateselection_requests_created_5550__app_rej_by_su_rev_dt')
					),
				When(application_status__in=[settings.APP_STATUS[1][0],settings.APP_STATUS[2][0],
					settings.APP_STATUS[3][0], settings.APP_STATUS[17][0]],
					then=F('last_updated_on_datetime'),
					),
				When(Q(application_status=settings.APP_STATUS[11][0],
						applicationpayment_requests_created_3__fee_type='1',), # datetime for admission fees paid.
					then=Max('applicationpayment_requests_created_3__payment_date')
					),
				When(application_status__in=[settings.APP_STATUS[18][0],settings.APP_STATUS[19][0]],
					then=F('pre_selected_rejected_on_datetime'),
					),
				default=F('last_updated_on_datetime'),
				output_field=DateTimeField(),
				),
			)
		return query,s7


	def get_context_data(self, program=None, status=None, admit_batch=None, **kwargs):
		pdm_program_list = ProgramDocumentMap.objects.values_list('program__pk', flat=True)
		query = StudentCandidateApplication.objects.filter(program__in=pdm_program_list,
			application_status__in=[x[0] for x in list(settings.APP_STATUS[0:7]) + [settings.APP_STATUS[9], settings.APP_STATUS[11]] + list(settings.APP_STATUS[15:])])

		missing_concat = GroupConcat(self.missing_case(), 
			distinct=True, 
			output_field=SetCharField(base_field=CharField())
		)
		missing_concat_str = GroupConcat(self.missing_case(), 
			distinct=True, 
			output_field=CharField()
		)

		app_id_case = lambda : Case(
				When(Q(candidateselection_requests_created_5550__new_application_id__isnull=False,
					candidateselection_requests_created_5550__application__pk=F('pk')
					), 
					then=F('candidateselection_requests_created_5550__new_application_id')),
				default=F('student_application_id'),
				output_field=CharField(),
				)

		app_id_str = GroupConcat(app_id_case(), 
			distinct=True, 
			output_field=CharField()
		)


		# query = query.annotate(missingSet=missing_concat, missing=missing_concat_str)
		# query = query.filter(missingSet__isnull=False)
		query = query.filter(program=program) if program else query
		query = query.filter(application_status=status) if status else query
		query = query.filter(admit_batch=admit_batch) if admit_batch else query

		query = query.annotate(
			
			app_id = app_id_str, #This is done as a temporary workaround for search functionality 
			location = F('current_location__location_name'),
			pg_name = F('program__program_name'),
			student_id = F('candidateselection_requests_created_5550__student_id'),
			last_updated = Case(
				When(application_status__in=[settings.APP_STATUS[0][0],
					settings.APP_STATUS[4][0]], 
					then=Max(F('applicationdocument_requests_created_1__last_uploaded_on'))
					),
				When(application_status__in=[settings.APP_STATUS[5][0],settings.APP_STATUS[7][0]], 
					then=F('candidateselection_requests_created_5550__selected_rejected_on')
					),
				When(application_status__in=[settings.APP_STATUS[6][0],settings.APP_STATUS[8][0]], 
					then=F('candidateselection_requests_created_5550__offer_reject_mail_sent')
					),
				When(application_status__in=[settings.APP_STATUS[9][0],settings.APP_STATUS[10][0]], 
					then=F('candidateselection_requests_created_5550__accepted_rejected_by_candidate')
					),
				When(application_status=settings.APP_STATUS[15][0], 
					then=F('candidateselection_requests_created_5550__es_to_su_rev_dt')
					),
				When(application_status=settings.APP_STATUS[16][0], 
					then=F('candidateselection_requests_created_5550__app_rej_by_su_rev_dt')
					),
				When(application_status__in=[settings.APP_STATUS[1][0],settings.APP_STATUS[2][0],
					settings.APP_STATUS[3][0], settings.APP_STATUS[17][0]],
					then=F('last_updated_on_datetime'),
					),
				When(Q(application_status=settings.APP_STATUS[11][0],
						applicationpayment_requests_created_3__fee_type='1',), # datetime for admission fees paid.
					then=Max('applicationpayment_requests_created_3__payment_date')
					),
				When(application_status__in=[settings.APP_STATUS[18][0],settings.APP_STATUS[19][0]],
					then=F('pre_selected_rejected_on_datetime'),
					),
				default=F('last_updated_on_datetime'),
				output_field=DateTimeField(),
				),
			)
		context = super(BaseDefDocsAppData, self).get_context_data(**kwargs)
		data={'programs':program, 'status':status, 'admit_batch':admit_batch }
		SCATable = self.return_table_func(programs=program, status=status, 
			admit_batch=admit_batch, ajax_url=self.ajax_url, action_url=self.action_url)
		context['table'] = SCATable(query)
		context['form2'] = def_filter_form(data)
		context['scaTotal'] = query.distinct().count()
		context['query'] = query
		context['program'] = program
		context['status'] = status
		context['admit_batch'] = admit_batch
		return context 

	
	def get_sub_data_queryset(self,pg1,status,admit_batch,search):
		return_table_func = lambda self, *args, **kwargs: doc_sub_paging(*args, **kwargs)
	
		document_name = lambda self, verified: When(
			~Q(applicationdocument_requests_created_1__file=Value('')) &
			Q(applicationdocument_requests_created_1__program_document_map__deffered_submission_flag=True) &
			Q(applicationdocument_requests_created_1__rejected_by_bits_flag=False) &
			Q(applicationdocument_requests_created_1__reload_flag=False) &
			Q(applicationdocument_requests_created_1__accepted_verified_by_bits_flag=verified),
			then=Concat(
				'applicationdocument_requests_created_1__document__document_name', 
				Value((': VERIFIED' if verified else ': NOT VERIFIED'))
			),
		)

		missing_case = lambda self: Case(
			self.document_name(True),
			self.document_name(False),
			output_field=CharField(),
		)

		pdm_program_list = ProgramDocumentMap.objects.values_list('program__pk', flat=True)
		query = StudentCandidateApplication.objects.filter(program__in=pdm_program_list,
														   application_status__in=[x[0] for x in
																				   list(settings.APP_STATUS[0:7]) + [
																					   settings.APP_STATUS[9],
																					   settings.APP_STATUS[11]] + list(
																					   settings.APP_STATUS[15:])])

		missing_concat = GroupConcat(self.missing_case(),
									 distinct=True,
									 output_field=SetCharField(base_field=CharField())
									 )
		missing_concat_str = GroupConcat(self.missing_case(),
										 distinct=True,
										 output_field=CharField()
										 )

		app_id_case = lambda: Case(
			When(Q(candidateselection_requests_created_5550__new_application_id__isnull=False,
				   candidateselection_requests_created_5550__application__pk=F('pk')
				   ),
				 then=F('candidateselection_requests_created_5550__new_application_id')),
			default=F('student_application_id'),
			output_field=CharField(),
		)

		app_id_str = GroupConcat(app_id_case(),
								 distinct=True,
								 output_field=CharField()
								 )

		query = query.annotate(missingSet=missing_concat, missing=missing_concat_str)

		query = query.filter(missingSet__isnull=False)

		query = query.filter(program=pg1) if pg1 and pg1 > 0 else query
		query = query.filter(admit_batch=admit_batch) if admit_batch and not admit_batch == 'n' else query
		query = query.filter(application_status=status) if status and not status == 'n' else query
		query = deffered_doc_search(query, search)
		query = query.annotate(
			app_id=app_id_str,
			location=F('current_location__location_name'),
			pg_name=F('program__program_name'),
			student_id=F('candidateselection_requests_created_5550__student_id'),
			last_updated=Case(
				When(application_status__in=[settings.APP_STATUS[0][0],
											 settings.APP_STATUS[4][0]],
					 then=Max(F('applicationdocument_requests_created_1__last_uploaded_on'))
					 ),
				When(application_status__in=[settings.APP_STATUS[5][0], settings.APP_STATUS[7][0]],
					 then=F('candidateselection_requests_created_5550__selected_rejected_on')
					 ),
				When(application_status__in=[settings.APP_STATUS[6][0], settings.APP_STATUS[8][0]],
					 then=F('candidateselection_requests_created_5550__offer_reject_mail_sent')
					 ),
				When(application_status__in=[settings.APP_STATUS[9][0], settings.APP_STATUS[10][0]],
					 then=F('candidateselection_requests_created_5550__accepted_rejected_by_candidate')
					 ),
				When(application_status=settings.APP_STATUS[15][0],
					 then=F('candidateselection_requests_created_5550__es_to_su_rev_dt')
					 ),
				When(application_status=settings.APP_STATUS[16][0],
					 then=F('candidateselection_requests_created_5550__app_rej_by_su_rev_dt')
					 ),
				When(application_status__in=[settings.APP_STATUS[1][0], settings.APP_STATUS[2][0],
											 settings.APP_STATUS[3][0], settings.APP_STATUS[17][0]],
					 then=F('last_updated_on_datetime'),
					 ),
				When(Q(application_status=settings.APP_STATUS[11][0],
					   applicationpayment_requests_created_3__fee_type='1', ),  # datetime for admission fees paid.
					 then=Max('applicationpayment_requests_created_3__payment_date')
					 ),
				When(application_status__in=[settings.APP_STATUS[18][0], settings.APP_STATUS[19][0]],
					 then=F('pre_selected_rejected_on_datetime'),
					 ),
				default=F('last_updated_on_datetime'),
				output_field=DateTimeField(),
			),
		)
		return query


	def get(self, request, *args, **kwargs):
		
		program = request.GET.get('programs',None)
		status = request.GET.get('status',None)
		admit_batch = request.GET.get('admit_batch',None)
		search = request.GET.get('search',None)

		if 'csv' in request.GET:
			csv_query,s7=self.get_def_data_queryset(program,status,admit_batch,search)
			query = csv_query.values(*self.csv_value)		
			data = [self.csv_header, ]
			data += [ [x['student_application_id'],x['candidateselection_requests_created_5550__student_id'],x['admit_batch'],
					 x['full_name'],
					timezone.localtime(x['last_updated']).strftime("%d-%m-%Y %I:%M %p") if x['last_updated'] else '',
					x['current_location__location_name'],
					x['program__program_name'],
					s7.loc[s7['student_application_id'] ==x['student_application_id'], 'document_type__document_name'].iloc[0],
					x['application_status']
					] for x in query.iterator()
				 ]		 
			return ExcelResponse(data, 'Missing Deffered Document')

		if 'csvs' in request.GET:
			csv_query=self.get_sub_data_queryset(program,status,admit_batch,search)
			query = csv_query.values(*self.csvs_value)		
			data = [self.csv_header, ]
			data += [ [x['student_application_id'],x['candidateselection_requests_created_5550__student_id'],x['admit_batch'],
					 x['full_name'],
					timezone.localtime(x['last_updated']).strftime("%d-%m-%Y %I:%M %p") if x['last_updated'] else '',
					x['current_location__location_name'],
					x['program__program_name'],
					x['missing'],
					x['application_status']
					] for x in query.iterator()
				 ]	 
			return ExcelResponse(data, 'Submitted Deffered Document')
		return super(BaseDefDocsAppData, self).get(request, 
			program=program, status=status, admit_batch=admit_batch, *args, **kwargs)

class BaseDefDocsSubData(BaseDefDocsAppData):
	return_table_func = lambda self, *args, **kwargs: doc_sub_paging(*args, **kwargs)
	
	document_name = lambda self, verified: When(
		~Q(applicationdocument_requests_created_1__file=Value('')) &
		Q(applicationdocument_requests_created_1__program_document_map__deffered_submission_flag=True) &
		Q(applicationdocument_requests_created_1__rejected_by_bits_flag=False) &
		Q(applicationdocument_requests_created_1__reload_flag=False) &
		Q(applicationdocument_requests_created_1__accepted_verified_by_bits_flag=verified),
		then=Concat(
			'applicationdocument_requests_created_1__document__document_name', 
			Value((': VERIFIED' if verified else ': NOT VERIFIED'))
		),
	)

	missing_case = lambda self: Case(
		self.document_name(True),
		self.document_name(False),
		output_field=CharField(),
	)


class BasePreSelAppData(TemplateView):
	return_table_func = lambda self, *args, **kwargs: pre_sel_paging(*args, **kwargs)

	def get_context_data(self, program=None, location=None, **kwargs):
		query = StudentCandidateApplication.objects.filter(program__enable_pre_selection_flag = True,
				application_status__in =[
					settings.APP_STATUS[12][0],
					settings.APP_STATUS[18][0],
					settings.APP_STATUS[19][0],
					])

		app_id_case = lambda : Case(
				When(Q(candidateselection_requests_created_5550__new_application_id__isnull=False,
					candidateselection_requests_created_5550__application__pk=F('pk')
					), 
					then=F('candidateselection_requests_created_5550__new_application_id')),
				default=F('student_application_id'),
				output_field=CharField(),
				)

		app_id_str = GroupConcat(app_id_case(), 
			distinct=True, 
			output_field=CharField()
		)

		query = query.filter(program = program) if program else query
		query = query.filter(current_location = location) if location else query
		query = query.annotate(
			
			app_id = app_id_str, #This is done as a temporary workaround for search functionality 
			pg_name = F('program__program_name'),
			email =F('login_email__email'),
			c_l = F('current_location__location_name'),
			last_updated = Case(
				When(application_status__in=[settings.APP_STATUS[0][0],
					settings.APP_STATUS[4][0]], 
					then=Max(F('applicationdocument_requests_created_1__last_uploaded_on'))
					),
				When(application_status__in=[settings.APP_STATUS[5][0],settings.APP_STATUS[7][0]], 
					then=F('candidateselection_requests_created_5550__selected_rejected_on')
					),
				When(application_status__in=[settings.APP_STATUS[6][0],settings.APP_STATUS[8][0]], 
					then=F('candidateselection_requests_created_5550__offer_reject_mail_sent')
					),
				When(application_status__in=[settings.APP_STATUS[9][0],settings.APP_STATUS[10][0]], 
					then=F('candidateselection_requests_created_5550__accepted_rejected_by_candidate')
					),
				When(application_status=settings.APP_STATUS[15][0], 
					then=F('candidateselection_requests_created_5550__es_to_su_rev_dt')
					),
				When(application_status=settings.APP_STATUS[16][0], 
					then=F('candidateselection_requests_created_5550__app_rej_by_su_rev_dt')
					),
				When(application_status__in=[settings.APP_STATUS[1][0],settings.APP_STATUS[2][0],
					settings.APP_STATUS[3][0], settings.APP_STATUS[17][0]],
					then=F('last_updated_on_datetime'),
					),
				When(Q(application_status=settings.APP_STATUS[11][0],
						applicationpayment_requests_created_3__fee_type='1',), # datetime for admission fees paid.
					then=Max('applicationpayment_requests_created_3__payment_date')
					),
				When(application_status__in=[settings.APP_STATUS[18][0],settings.APP_STATUS[19][0]],
					then=F('pre_selected_rejected_on_datetime'),
					),
				default=F('last_updated_on_datetime'),
				output_field=DateTimeField(),
				),
			)
		context = super(BasePreSelAppData, self).get_context_data(**kwargs)
		data={'programs':program, 'location':location}
		SCATable = self.return_table_func(programs=program, location=location, 
			 ajax_url=self.ajax_url, action_url=self.action_url)
		context['table'] = SCATable(query)
		context['form2'] = pre_sel_rej_filter_form(data)
		context['query'] = query
		context['program'] = program
		context['location'] = location
		return context 

	def get(self, request, *args, **kwargs):
		program = request.GET.get('programs',None)
		location = request.GET.get('location',None)
		return super(BasePreSelAppData, self).get(request, 
			program=program, location=location,*args, **kwargs)



class BaseCompleteAppTemplateView(TemplateView):

	def get_context_data(self, **kwargs):
		context = super(BaseCompleteAppTemplateView, self).get_context_data(**kwargs)
		context['table'] = ApplicationCombineTable()
		return context 


#Base CallBound Class
class BaseBoundView(TemplateView):
	template_name = ''
	model=''

	def filter_arguments(self):
		return {'to_date':self.to_date,'from_date':self.from_date}

	def get_context_data(self, **kwargs):
		context = super(BaseBoundView, self).get_context_data(**kwargs)
		query = self.model.objects.all()
		if query.exists():
			query = query.annotate(
				called_on_date=Trunc(
					'called_on',
					'day',
					output_field=DateField(),
					tzinfo=india
				)
			)

			from_date = parse(self.from_date) if self.from_date else timezone.datetime.min.date()
			to_date = parse(self.to_date) if self.to_date else timezone.datetime.max.date()
			query = query.filter(
				called_on_date__gte = from_date,
				called_on_date__lte = to_date,
			)

		context['form'] = call_log_form(self.filter_arguments())
		context['query'] = query

		return context

	def get(self, request, *args, **kwargs):
		self.to_date = request.GET.get('to_date',None)
		self.from_date = request.GET.get('from_date',None)
		return super(BaseBoundView, self).get(request, *args, **kwargs)

class BaseInboundView(BaseBoundView):
	template_name = 'bits_admin/inbound.html'
	model=InBoundCall

	def get_context_data(self, **kwargs):
		context = super(BaseInboundView, self).get_context_data(**kwargs)
		context['table'] = inbound_call_log_paging(**self.filter_arguments())(context['query'])
		return context


class BaseOutboundView(BaseBoundView):
	template_name = 'bits_admin/outbound.html'
	model=OutBoundCall

	def get_context_data(self, **kwargs):
		context = super(BaseOutboundView, self).get_context_data(**kwargs)
		context['table'] = outbound_call_log_paging(**self.filter_arguments())(context['query'])
		return context


class BaseEMIReportEduvAppData(TemplateView):

	return_table_func = lambda self, *args, **kwargs: eduv_report_paging(*args, **kwargs)

	render_to_csv_response = lambda self, query, csv_kwargs: render_to_csv_response(query, **csv_kwargs)

	eduv_model = EduvanzApplication
	eduv_archive_model = EduvanzApplicationArchived

	get_eduv_status = lambda self,x:dict(self.eduv_model.EDUVANZ_CHOICES).get(x, '-')

	csv_header = [
		'Application ID',
		'Admit Batch',
		'Student ID',
		'Eduvanz Lead ID',
		'Name',
		'Program Applied for',
		'Loan Applied On',
		'Loan Approval / Rejection Date',
		'Last Status Update Date',
		'Eduvanz Order ID',
		'Current Loan Status',
		'Application Status',
	]
		
	csv_value =['application__student_application_id',
		'application__admit_batch',
		'application__candidateselection_requests_created_5550__student_id',
		'lead_id',
		'application__full_name',
		'pg_name',
		'created_on',
		'approved_or_rejected_on',
		'updated_on',
		'order_id',
		'status_code',
		'application__application_status',
		]

	csv_archive_value=csv_value[:]
	csv_archive_value[2] ='application__candidateselectionarchived_1__student_id'


	def get_context_data(self, program=None, status=None, **kwargs):
		query = get_eduv_queryset(self.eduv_model)
		pg_code = Program.objects.get(pk=program).program_code if program else None
		admit_batch = self.request.GET.get('admit_batch',None)
		ptype = self.request.GET.get('pg_type',None)
		query = query.filter(application__program__program_code=pg_code ) if pg_code else query
		query = query.filter(status_code=status) if status else query

		query_archive = get_eduv_queryset(self.eduv_archive_model)
		pg_code = Program.objects.get(pk=program).program_code if program else None
		admit_batch = self.request.GET.get('admit_batch',None)
		ptype = self.request.GET.get('pg_type',None)
		query_archive = query_archive.filter(application__program__program_code=pg_code ) if pg_code else query_archive
		query_archive = query_archive.filter(status_code=status) if status else query_archive

		context = super(BaseEMIReportEduvAppData, self).get_context_data(**kwargs)
		data={'programs':program, 'status':status,'admit_batch': admit_batch ,'pg_type':ptype}
		SCATable = self.return_table_func(programs=program, admit_batch=admit_batch, status=status,pg_type=ptype,
			ajax_url=self.ajax_url,action_url=self.action_url)
		context['table'] = SCATable()	
		context['form'] = eduv_emi_filter_form(data)
		context['scaTotal'] = query.count()+query_archive.count()
		context['query'] = query
		context['query_archive'] = query_archive
		context['program'] = program
		context['status'] = status
		context['admit_batch'] = admit_batch
		context['ptype'] = ptype
		return context 

	def get(self, request, *args, **kwargs):
		program = request.GET.get('programs') or None
		admit_batch = request.GET.get('admit_batch') or None
		ptype = request.GET.get('pg_type',None)
		status = request.GET.get('status') or None
		search = request.GET.get('search') or None

		query = get_eduv_queryset(self.eduv_model)
		pg_code = Program.objects.get(pk=program).program_code if program else None
		admit_batch = self.request.GET.get('admit_batch') if admit_batch else None
		ptype = self.request.GET.get('pg_type',None) if ptype else None

		query = query.filter(application__program__program_code=pg_code ) if pg_code else query
		query = query.filter(application__program__program_type=ptype) if ptype else query
		query = query.filter(application__admit_batch=admit_batch) if admit_batch else query
		query = query.filter(status_code=status) if status else query
		query = eduv_search(query, search)

		query_archive = get_eduv_queryset(self.eduv_archive_model)
		query_archive = query_archive.filter(application__program__program_code=pg_code ) if pg_code else query_archive
		query_archive = query_archive.filter(application__program__program_type=ptype) if ptype else query_archive
		query_archive = query_archive.filter(application__admit_batch=admit_batch) if admit_batch else query_archive
		query_archive = query_archive.filter(status_code=status) if status else query_archive
		query_archive = eduv_search(query_archive, search)		

		if 'emi_app_csv' in request.GET:
			query = query.values(*self.csv_value)
			query_archive = query_archive.values(*self.csv_archive_value)		
			data = [self.csv_header, ]
			data += [ [x['application__student_application_id'],x['application__admit_batch'],
					x['application__candidateselection_requests_created_5550__student_id'],x['lead_id'],
					x['application__full_name'],
					x['pg_name'],
					timezone.localtime(x['created_on']).strftime("%d-%m-%Y %I:%M %p") if x['created_on'] else '',
					timezone.localtime(x['approved_or_rejected_on']).strftime("%d-%m-%Y %I:%M %p") if x['approved_or_rejected_on'] else '',
					timezone.localtime(x['updated_on']).strftime("%d-%m-%Y %I:%M %p") if x['updated_on'] else '',
					x['order_id'],self.get_eduv_status(x['status_code']),
					x['application__application_status']] for x in query.iterator()
				 ]
			data += [ [x['application__student_application_id'],x['application__admit_batch'],
					x['application__candidateselectionarchived_1__student_id'],x['lead_id'],
					x['application__full_name'],
					x['pg_name'],
					timezone.localtime(x['created_on']).strftime("%d-%m-%Y %I:%M %p") if x['created_on'] else '',
					timezone.localtime(x['approved_or_rejected_on']).strftime("%d-%m-%Y %I:%M %p") if x['approved_or_rejected_on'] else '',
					timezone.localtime(x['updated_on']).strftime("%d-%m-%Y %I:%M %p") if x['updated_on'] else '',
					x['order_id'],self.get_eduv_status(x['status_code']),
					x['application__application_status']] for x in query_archive.iterator()
				 ]
			return ExcelResponse(data, 'Student_Loan_Application_data (Eduvanz)')

		return super(BaseEMIReportEduvAppData, self).get(request, 
			program=program,admit_batch=admit_batch,pg_type=ptype, status=status, *args, **kwargs)

class BaseEMIReportEzcredAppData(TemplateView):
	return_table_func = lambda self, *args, **kwargs: ezcred_report_paging(*args, **kwargs)
	ezcred_model = EzcredApplication
	get_ezcred_queryset = lambda self: self.ezcred_model.objects.all()

	csv_header = [
		'Application ID',
		'Admit Batch',
		'Student ID',
		'Name',
		'Program Applied for',
		'Loan Applied On',
		'Ezcred Order ID',
		'Current Loan Status',
		'Application Status',
	]
		
	csv_value =['application__student_application_id',
		'application__admit_batch',
		'application__candidateselection_requests_created_5550__student_id',
		'application__full_name',
		'pg_full',
		'created_on',
		'order_id',
		'status',
		'application__application_status',
		]

	def ezcred_search(self, query, search):
		return query.filter(
			reduce(operator.and_, 
				(
					Q(application__student_application_id__icontains = item)|
					Q(application__admit_batch__icontains = item)|
					Q(application__candidateselection_requests_created_5550__student_id__icontains = item)|
					Q(application__full_name__icontains = item)|
					Q(application__program__program_name__icontains = item)|
					Q(order_id__icontains = item)|
					Q(application__program__program_type__icontains = item)|
					Q(status__icontains = item)
					for item in search.split()
				)
			) 
		) if search else query

	def get_context_data(self, program=None, admit_batch = None, pg_type=None,status=None, **kwargs):
		query = self.get_ezcred_queryset()
		pg_code = Program.objects.get(pk=program).program_code if program else None
		admit_batch = self.request.GET.get('admit_batch',None)
		ptype = self.request.GET.get('pg_type',None)
		query = query.filter(application__program__program_type=ptype) if ptype else query
		query = query.filter(application__program__program_code=pg_code ) if pg_code else query
		query = query.filter(application__admit_batch=admit_batch) if admit_batch else query
		query = query.filter(status=status) if status else query
		query=query.annotate(app_id=Case(
					When(Q(application__candidateselection_requests_created_5550__new_application_id__isnull=False,
							application__candidateselection_requests_created_5550__application__pk=F('pk')
							), 
							then=F('application__candidateselection_requests_created_5550__new_application_id')),
							default=F('application__student_application_id'),
							output_field=CharField(),
							),
							app_status=F('application__application_status'),
							full_name=F('application__full_name'),
							pg_full=Concat(F('application__program__program_name'),Value(' - '),
								F('application__program__program_code'),Value(' ('),
								F('application__program__program_type'),Value(')')),
							stud_id=F('application__candidateselection_requests_created_5550__student_id'),
							adm_batch=F('application__admit_batch'),
							sca_id=F('application__pk'),

			)

		context = super(BaseEMIReportEzcredAppData, self).get_context_data(**kwargs)
		data={'programs':program, 'admit_batch': admit_batch ,'status':status,'pg_type':ptype}
		SCATable = self.return_table_func(programs=program, admit_batch=admit_batch, status=status,pg_type=ptype,
			ajax_url=self.ajax_url,action_url=self.action_url)
		context['form'] = ezcred_filter_form(data)
		context['table'] = SCATable(query)
		context['program'] = program
		context['admit_batch'] = admit_batch
		context['ptype'] = ptype
		context['status'] = status
		return context

	def get(self, request, *args, **kwargs):
		
		program = request.GET.get('programs') or None
		admit_batch = request.GET.get('admit_batch') or None
		status = request.GET.get('status') or None
		ptype = request.GET.get('pg_type',None)
		search = request.GET.get('search') or None

		query = self.get_ezcred_queryset().distinct()
		pg_code = Program.objects.get(pk=program).program_code if program else None
		admit_batch = self.request.GET.get('admit_batch')
		ptype = self.request.GET.get('pg_type',None)
		query = query.filter(application__program__program_type=ptype) if ptype else query
		query = query.filter(application__program__program_code=pg_code ) if pg_code else query
		query = query.filter(application__admit_batch=admit_batch) if admit_batch else query
		query = query.filter(status=status) if status else query
		query = self.ezcred_search(query, search)
		query=query.annotate(app_id=Case(
					When(Q(application__candidateselection_requests_created_5550__new_application_id__isnull=False,
							application__candidateselection_requests_created_5550__application__pk=F('pk')
							), 
							then=F('application__candidateselection_requests_created_5550__new_application_id')),
							default=F('application__student_application_id'),
							output_field=CharField(),
							),
							app_status=F('application__application_status'),
							full_name=F('application__full_name'),
							pg_full=Concat(F('application__program__program_name'),Value(' - '),
								F('application__program__program_code'),Value(' ('),
								F('application__program__program_type'),Value(')')),
							stud_id=F('application__candidateselection_requests_created_5550__student_id'),
							adm_batch=F('application__admit_batch'),
							sca_id=F('application__pk'),

			)

		if 'emi_app_csv' in request.GET:
			query = query.values(*self.csv_value)

			
			data = [self.csv_header, ] 
			data += [ [x['application__student_application_id'],x['application__admit_batch'],
					x['application__candidateselection_requests_created_5550__student_id'],
					x['application__full_name'],
					x['pg_full'],
					timezone.localtime(x['created_on']).strftime("%d-%m-%Y %I:%M %p") if x['created_on'] else '',
					x['order_id'],x['status'],
					x['application__application_status']] for x in query.iterator()
				 ]
			return ExcelResponse(data, 'Student_Loan_Application_data')
		return super(BaseEMIReportEzcredAppData, self).get(request, 
			program=program, admit_batch = admit_batch, status=status, pg_type=ptype,  *args, **kwargs)


class BaseEMIReportPropelldAppData(TemplateView):
	return_table_func = lambda self, *args, **kwargs: propelld_report_paging(*args, **kwargs)
	propelld_model = PropelldApplication
	get_propelld_queryset = lambda self: self.propelld_model.objects.all()

	csv_header = [
		'Application ID',
		'Admit Batch',
		'Student ID',
		'Name',
		'Program Applied for',
		'Loan Applied On',
		'Last Status Update Date',
		'Loan Disbursement Date',
		'Propelld Quote ID',
		'Current Loan Status',
		'Application Status',
		'UTR Number',
	]
		
	csv_value =['application__student_application_id',
		'application__admit_batch',
		'application__candidateselection_requests_created_5550__student_id',
		'application__full_name',
		'pg_full',
		'created_on',
		'updated_on',
		'disbursement_date',
		'quote_id',
		'status',
		'application__application_status',
		'utr_number',
		]

	def propelld_search(self, query, search):
		return query.filter(
			reduce(operator.and_, 
				(
					Q(application__student_application_id__icontains = item)|
					Q(application__admit_batch__icontains = item)|
					Q(application__candidateselection_requests_created_5550__student_id__icontains = item)|
					Q(application__full_name__icontains = item)|
					Q(application__program__program_name__icontains = item)|
					Q(order_id__icontains = item)|
					Q(application__program__program_type__icontains = item)|
					Q(status__icontains = item)
					for item in search.split()
				)
			) 
		) if search else query

	def get_context_data(self, program=None, admit_batch = None, pg_type=None,status=None, **kwargs):
		query = self.get_propelld_queryset()
		pg_code = Program.objects.get(pk=program).program_code if program else None
		admit_batch = self.request.GET.get('admit_batch',None)
		ptype = self.request.GET.get('pg_type',None)
		query = query.filter(application__program__program_type=ptype) if ptype else query
		query = query.filter(application__program__program_code=pg_code ) if pg_code else query
		query = query.filter(application__admit_batch=admit_batch) if admit_batch else query
		query = query.filter(status=status) if status else query
		query=query.annotate(app_id=Case(
					When(Q(application__candidateselection_requests_created_5550__new_application_id__isnull=False,
							application__candidateselection_requests_created_5550__application__pk=F('pk')
							), 
							then=F('application__candidateselection_requests_created_5550__new_application_id')),
							default=F('application__student_application_id'),
							output_field=CharField(),
							),
							app_status=F('application__application_status'),
							fullname=F('application__full_name'),
							pg_full=Concat(F('application__program__program_name'),Value(' - '),
								F('application__program__program_code'),Value(' ('),
								F('application__program__program_type'),Value(')')),
							stud_id=F('application__candidateselection_requests_created_5550__student_id'),
							adm_batch=F('application__admit_batch'),
							sca_id=F('application__pk'),

			)

		context = super(BaseEMIReportPropelldAppData, self).get_context_data(**kwargs)
		data={'programs':program, 'admit_batch': admit_batch ,'status':status,'pg_type':ptype}
		SCATable = self.return_table_func(programs=program, admit_batch=admit_batch, status=status,pg_type=ptype,
			ajax_url=self.ajax_url,action_url=self.action_url)
		context['form'] = propelld_filter_form(data)
		context['table'] = SCATable(query)
		context['program'] = program
		context['admit_batch'] = admit_batch
		context['ptype'] = ptype
		context['status'] = status
		return context

	def get(self, request, *args, **kwargs):
		
		program = request.GET.get('programs') or None
		admit_batch = request.GET.get('admit_batch') or None
		status = request.GET.get('status') or None
		ptype = request.GET.get('pg_type',None)
		search = request.GET.get('search') or None

		query = self.get_propelld_queryset().distinct()
		pg_code = Program.objects.get(pk=program).program_code if program else None
		admit_batch = self.request.GET.get('admit_batch')
		ptype = self.request.GET.get('pg_type',None)
		query = query.filter(application__program__program_type=ptype) if ptype else query
		query = query.filter(application__program__program_code=pg_code ) if pg_code else query
		query = query.filter(application__admit_batch=admit_batch) if admit_batch else query
		query = query.filter(status=status) if status else query
		query = self.propelld_search(query, search)
		query=query.annotate(app_id=Case(
					When(Q(application__candidateselection_requests_created_5550__new_application_id__isnull=False,
							application__candidateselection_requests_created_5550__application__pk=F('pk')
							), 
							then=F('application__candidateselection_requests_created_5550__new_application_id')),
							default=F('application__student_application_id'),
							output_field=CharField(),
							),
							app_status=F('application__application_status'),
							fullname=F('application__full_name'),
							pg_full=Concat(F('application__program__program_name'),Value(' - '),
								F('application__program__program_code'),Value(' ('),
								F('application__program__program_type'),Value(')')),
							stud_id=F('application__candidateselection_requests_created_5550__student_id'),
							adm_batch=F('application__admit_batch'),
							sca_id=F('application__pk'),

			)

		if 'emi_app_csv' in request.GET:
			query = query.values(*self.csv_value)

			
			data = [self.csv_header, ] 
			data += [ [x['application__student_application_id'],x['application__admit_batch'],
					x['application__candidateselection_requests_created_5550__student_id'],
					x['application__full_name'],
					x['pg_full'],
					timezone.localtime(x['created_on']).strftime("%d-%m-%Y %I:%M %p") if x['created_on'] else '',
					timezone.localtime(x['updated_on']).strftime("%d-%m-%Y %I:%M %p") if x['updated_on'] else '',
					timezone.localtime(x['disbursement_date']).strftime("%d-%m-%Y %I:%M %p") if x['disbursement_date'] else '',
					x['quote_id'],x['status'],
					x['application__application_status'],
					x['utr_number']] for x in query.iterator()

				 ]
			return ExcelResponse(data, 'Student_Loan_Application_data')
		return super(BaseEMIReportPropelldAppData, self).get(request, 
			program=program, admit_batch = admit_batch, status=status, pg_type=ptype,  *args, **kwargs)		



	