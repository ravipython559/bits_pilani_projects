from django.shortcuts import render, redirect
from django.db import IntegrityError, transaction
from django.core.urlresolvers import reverse
from django_mysql.models import GroupConcat
from djqscsv import render_to_csv_response
from excel_response import ExcelResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.db.models import Max, Value,Count,F,Q,CharField,Case,When,Sum,DateTimeField
from django.db.models.functions import Concat,Upper
from datetime import datetime as dt
from datetime import date, timedelta
from .models import *
from registrations.models import *
from .forms import *
from .task import *
from .bits_decorator import *
from django.views.decorators.cache import never_cache
from django.conf import settings
from import_export.tmp_storages import  MediaStorage as MS
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect, FileResponse
from django.views.decorators.http import  require_GET
from celery.result import AsyncResult
from django.core.serializers.json import DjangoJSONEncoder
from table.views import FeedDataView
from .tables import *
from .tables import (ncl_paging as NCL_Adm)
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from bits_admin.dynamic_views import (BaseDefDocsAppData, BaseElectiveSelectionsAppData, 
	BaseEMIReportAppData, BaseDefDocsSubData, BasePreSelAppData, BaseCompleteAppTemplateView,
	BaseOutboundView,BaseInboundView,BaseEMIReportEduvAppData,BaseEMIReportEzcredAppData, BaseEMIReportPropelldAppData)
from bits_admin.tables import (def_doc_paging, doc_sub_paging, pre_sel_paging, 
	inbound_call_log_paging, outbound_call_log_paging)
from .tables_ajax import (DefDocView, BaseElectiveSelectionsAppAjaxData, 
	BaseEMIReportAppAjaxData, DefDocSubView, PreSelAppView, BaseEMIReportEduvAppAjaxData,BaseEMIReportEzcredAppAjaxData,BaseEMIReportPropelldAppAjaxData)

from registrations.dynamic_dmr_report import *
from registrations.dynamic_views import BaseSendPreConfirmSelRejEmail
from registrations.tables_ajax import *
from registrations.tables import ( waiver_report_table, milestone_report_table, prog_change_report_paging as PCRPTable,
	StudentCourseReportTable as SCRTable, pgm_adm_report_paging )
from registrations.bits_api import name_verify_api
from bits_rest.bits_extra import student_id_generator
from wsgiref.util import FileWrapper
from adhoc.views import BaseAdhocReportAppData,BaseAjaxAdhocReport,BaseAdhocReportEduvAppData,BaseAjaxAdhocReportEduv,BaseAdhocReportPropelldAppData, BaseAjaxAdhocReportPropelld
from adhoc.tables import *
from registrations.utils import offer_letter as ol
from django_mysql.locks import Lock
import json
import tempfile
import datetime
import logging
import tablib
import operator
from django.utils import timezone
logger = logging.getLogger("main")
import itertools


@staff_member_required
@adm_man_id_wav_chk
@never_cache
def adm_manID_gen(request,app_id):
	logger.info("{0} invoked funct.".format(request.user.email))
	app = StudentCandidateApplication.objects.get(id=int(app_id))
	pfa = PROGRAM_FEES_ADMISSION.objects.get(program=app.program,
		fee_type = '1',latest_fee_amount_flag=True)
	max_id = CandidateSelection.objects.filter(
		application__admit_year=pfa.admit_year,
		application__program = pfa.program,
		student_id__contains = pfa.program.program_code
		).aggregate(Max('student_id'))
	cs = CandidateSelection.objects.get(application = app,)

	with Lock('bits_student_id_lock'):
		student_id = student_id_generator(login_email=app.login_email.email)
		if cs.student_id:student_id=cs.student_id
		cs.student_id  = student_id
		cs.save()

	return redirect(reverse('bits_admin:applicantData'))

@staff_member_required
def app_archive_data(request):
	logger.info("{0} invoked funct.".format(request.user.email))
	archive = 'no'
	if request.method == 'POST':
		logger.info("{0} inside POST request".format(request.user.email))
		form = ArchiveForm( request.POST )
		
		if form.is_valid():
			logger.info("{0} POST request is valid".format(request.user.email))
			from_date = form.cleaned_data.get('from_date',None)
			to_date = form.cleaned_data.get('to_date',None)
			programs = form.cleaned_data['programs']
			admit_batch = form.cleaned_data.get('admit_batch',None)

			job = archive_task.apply_async(user=request.user, from_date=from_date,
				to_date=to_date,programs=programs, admit_batch=admit_batch)
			archive = 'yes'
			# return redirect(reverse('bits_admin:archive_progress') + '?job=' + job.id)
			
	else:
		logger.info("{0} inside GET request".format(request.user.email))
		form = ArchiveForm()
	max_id = ArchiveAuditTable.objects.aggregate(Max('run'))
	aat = ArchiveAuditTable.objects.filter( run = max_id['run__max'] )
	logger.info("{0} ready to render".format(request.user.email))
	return render(request,'bits_admin/app_archive_data.html',{
		'form':form,
		'aat':aat,
		'archive': archive,
		})

@staff_member_required
@require_GET
def archive_progress(request):
	if request.is_ajax():

		if 'job' in request.GET:
			job_id = request.GET['job']
		else:
			return JsonResponse({'message':None,'status':'FAILURE'})
		job = AsyncResult(job_id)

		try :
			message = job.result['message']
		except : 
			message ='processing...'

		print 'Message............',message
		if job.status == 'SUCCESS':
			job.revoke()
		return JsonResponse({'message':message,'status':job.status})

	else:
		return render(request,'bits_admin/archive_progress.html',{
			'job_id':request.GET['job'] if 'job' in request.GET else 0,
			})


@staff_member_required
@require_GET
def sdms_progress(request):
	if request.is_ajax():

		if 'job' in request.GET:
			job_id = request.GET['job']
		else:
			return JsonResponse({'message':None,'status':'FAILURE'})
		job = AsyncResult(job_id)
		try :
			message = job.result['message']
		except : 
			message ='processing...'

		print 'Message............',message
		if job.status == 'SUCCESS':
			request.session['synced_ids_job_result'] = job.result
			request.session['synced_ids'] = job.result['synced_list']
			job.revoke()
		return JsonResponse({'message':message,'status':job.status})

	else:
		return render(request,'bits_admin/sdms_progress.html',{
			'job_id':request.GET['job'] if 'job' in request.GET else 0,
			})




#Name verification code...
@method_decorator(staff_member_required,name='dispatch')
class NclDataView(FeedDataView):

	token = NCL_Adm().token

	def get_queryset(self):
		query = super(NclDataView, self).get_queryset()

		pg1 = int(self.kwargs.get('pg',None))

		batch = self.kwargs.get('ab')

		pg_type = self.kwargs.get('p_type',None)

		query = query.filter( application__program=pg1 ) if pg1 and pg1 > 0 else query

		query = query if batch=='0' or not batch else query.filter(application__admit_batch=batch)

		query = query.filter(application__program__program_type=pg_type ) if pg_type and not pg_type == '0' else query

		query = query.exclude(
			Q(student_id__isnull=True)|Q(student_id='')).annotate(
			app_id = Case(
				When(new_application_id=None,
					then=Concat('application__student_application_id',Value(' '))),
				default=Concat('new_application_id',Value(' ')),
				output_field=CharField(),
				),
			finalName = F('application__full_name'),
			applied_on = F('application__created_on_datetime'),
			pg_name = Concat('application__program__program_name',Value(' - '),
				'application__program__program_code',Value(' ('),
				'application__program__program_type',Value(')')),
			sca_id = F('application__id'),
			admit_batch = F('application__admit_batch')
			)

		return query


@staff_member_required
def name_change_list(request):
	logger.info("{0} invoked funct.".format(request.user.email))

	query = CandidateSelection.objects.exclude(
		Q(student_id__isnull=True)|Q(student_id='')).annotate(
		app_id = Case(
			When(new_application_id=None,
				then=Concat('application__student_application_id',Value(' '))),
			default=Concat('new_application_id',Value(' ')),
			output_field=CharField(),
			),
		finalName = F('application__full_name'),
		applied_on = F('application__created_on_datetime'),
		pg_name = Concat('application__program__program_name',Value(' - '),
				'application__program__program_code',Value(' ('),
				'application__program__program_type',Value(')')),
		sca_id = F('application__id'),
		admit_batch = F('application__admit_batch'),
		)
	pg1 = request.POST.get('programs',None)
	ptype = request.POST.get('pg_type', None)
	batch = request.POST.get('admit_batch',None)
	query = query.filter(application__program__program_type=ptype) if ptype else query
	query = query.filter(application__program=pg1) if pg1 else query
	query = query.filter(application__admit_batch=batch) if batch else query

	data={'programs':pg1,'admit_batch':batch,'pg_type':ptype}
	if request.session.has_key('synced_ids_job_result'):
		data = request.session['synced_ids_job_result']['form_data']
		pg1 = data['programs']
		batch = data['admit_batch']
		ptype = data['pg_type']

	SCATable = NCL_Adm(programs=pg1,admit_batch=batch,pg_type=ptype)
	table = SCATable(query)
	if 'sync' in request.POST:
		user_name = request.user
		job= sdms_sync_task.delay(programs=pg1,program_type=ptype,admit_batch=batch,user_name=user_name)
		return redirect(reverse('bits_admin:sdms_progress') + '?job=' + job.id)
	if 'unsynceddetails' in request.POST:
		user_name = request.user
		job= sdms_sync_task.delay(programs=pg1,program_type=ptype,admit_batch=batch,user_name=user_name,unsynced_data=True)
		return redirect(reverse('bits_admin:sdms_progress') + '?job=' + job.id)
	if request.session.has_key('synced_ids_job_result'):
		sync_success = request.session['synced_ids_job_result']['sync_success']
		sync_error = request.session['synced_ids_job_result']['sync_error']
		del request.session['synced_ids_job_result']
	else:
		sync_success = False
		sync_error = False
	return render(request, 'bits_admin/nc_list_admin.html',
		{'queryResult':query,
		'prog_form':Ncl_Form(data),
		'batch_form':Ncl_Form(data),
		'ptype_form':Ncl_Form(data),
		'table' : table,
		'sync_success': sync_success,
		'sync_error': sync_error,
		})

def sdms_error_download(request):
	list_meta_api_errors = [json.loads(x.api_response) for x in MetaApi.objects.filter(id__in=request.session['synced_ids'])]
	meta_api_errors_list = list(itertools.chain(*list_meta_api_errors))
	meta_api_errors = [x for x in meta_api_errors_list if x['sdms_status_code'] == 400]
	display = []
	for x in meta_api_errors:
		display.extend([ '{0}  |  {1}\n\n'.format(x['id_no'], y.strip())for y in x['sdms_error'].split(',')])
		display.append('-'*150)
		display.append('\n')

	temp_file = tempfile.NamedTemporaryFile(delete=False)
	temp_file.file.writelines(display)
	content_length = temp_file.tell()
	wrapper = FileWrapper(temp_file)
	response = FileResponse(wrapper, content_type='application/force-download')
	attachment = 'attachment; filename=sdms_api_error_log_{0}.txt'.format(timezone.localtime(
		timezone.now()).strftime("%d_%m_%Y_%I_%M_%p"))
	response['Content-Disposition'] = attachment
	response['Content-Length'] = content_length
	temp_file.seek(0)
	return response

def sync_student_list(request):
	list_meta_api_errors = [json.loads(x.api_response) for x in MetaApi.objects.filter(id__in=request.session['synced_ids'])]
	meta_api_errors = list(itertools.chain(*list_meta_api_errors))
	synced_list = []
	error_list = []
	synced_display_list = ['Successfully synced Student ID:\n\n']
	error_display_list = ['Error Student ID:\n\n']
	for x in meta_api_errors:
		if x['sdms_status_code']==200:
			synced_list.append(str(x['id_no']))
		else:
			error_list.append(str(x['id_no']))

	synced_display_list.append(', '.join(synced_list))
	synced_display_list.append('\n\nTotal success count: {0}\n{1}\n\n'.format(len(synced_list),'-'*150))

	error_display_list.append(', '.join(error_list))
	error_display_list.append('\n\nTotal error count: {0}\n{1}\n'.format(len(error_list),'-'*150))

	temp_file = tempfile.NamedTemporaryFile(delete=False)
	temp_file.file.writelines(synced_display_list + error_display_list)
	content_length = temp_file.tell()
	wrapper = FileWrapper(temp_file)
	response = FileResponse(wrapper, content_type='application/force-download')
	attachment = 'attachment; filename=sync_student_list_{0}.txt'.format(timezone.localtime(
		timezone.now()).strftime("%d_%m_%Y_%I_%M_%p"))
	response['Content-Disposition'] = attachment
	response['Content-Length'] = content_length
	temp_file.seek(0)
	return response

@staff_member_required
def name_change_form(request,application_id):

	def ac_sync(request,application_id):
		try:
			sync_data, sync_meta_list = name_verify_api( CandidateSelection.objects.filter(
				application__id=application_id), request.user)
		except Exception as e:
			sync_data = [{'id_no': query.student_id,
			 'sdms_status_code': 400,
			 'sdms_error':str(e)},]
		else:
			
			for x in sync_data:
				if x['sdms_status_code'] == 200:
					cs = CandidateSelection.objects.get(student_id = x['id_no'])
					cs.dps_flag = True
					cs.dps_datetime = timezone.localtime(timezone.now())
					cs.save()
		return sync_data


	query = CandidateSelection.objects.get(
		application__id=application_id)
	doc = ApplicationDocument.objects.filter(
		application__id=application_id,document__n_v_flag=True)
	form = NameChangeForm(instance = query)
	sync_data = None

	if 'save' in request.POST:
		form = NameChangeForm(request.POST,instance = query)
		if form.is_valid():
			with transaction.atomic():
				query.name_verified_on = timezone.localtime(timezone.now())
				query.name_verified_by = request.user.email
				query.save()
				form.save()
				sync_data = ac_sync(request,application_id)
			#return redirect(reverse('bits_admin:nc-list'))

	elif 'sync'in request.POST:
		sync_data = ac_sync(request,application_id)

	return render(request, 'bits_admin/nc_form_admin.html',
		{'query':query,
		'doc':doc,
		'prog_form':form,
		'api_op': sync_data,
		})
#Name verification code ends...

@method_decorator([staff_member_required,],name='dispatch')
class DMR(BaseDMR):
	template_name = 'bits_admin/dmr_report.html'

@method_decorator([staff_member_required,],name='dispatch')
class DMRNonSpecific(BaseDMRNonSpecific):
	template_name = 'bits_admin/dmr_non_specific.html'
	form_class = DMRNonSpecificForm

	def get_context_data(self, **kwargs):
		context = super(DMRNonSpecific, self).get_context_data(**kwargs)
		context['form'] = self.form_class(initial=self.request.GET)
		return context


@method_decorator([staff_member_required,],name='dispatch')
class WaiverReportDataView(BaseWaiverReportDataView):
	token = waiver_report_table().token

@method_decorator([staff_member_required,],name='dispatch')
class WaiverReport(BaseWaiverReport):
	template_name = 'bits_admin/fee_waiver_report.html'

	def render_RA_table(self):
		class SCATable(waiver_report_table()):
			class Meta(waiver_report_table().Meta):
				ajax_source = reverse_lazy(
				'bits_admin:waiver-report-ajax',
				kwargs={'b_id':self.request.GET.get('admit_batch')  or 0}
			)
		return SCATable

	def get_context_data(self, **kwargs):
		context = super(WaiverReport, self).get_context_data(**kwargs)
		SCATable = self.render_RA_table()
		context['table'] = SCATable(context['query'])
		return context

@method_decorator(staff_member_required,name='dispatch')
class MilestoneView(BaseMilestoneView):
	token = milestone_report_table().token

@method_decorator([staff_member_required,],name='dispatch')
class ApplicationMilestoneReport(BaseApplicationMilestoneReport):
	template_name = 'bits_admin/milestone_report.html'

	def render_RA_table(self):
		class SCATable(milestone_report_table()):
			class Meta(milestone_report_table().Meta):
				ajax_source = reverse_lazy('bits_admin:milestone-report-ajax',
					kwargs={'b_id':self.request.GET.get('admit_batch')  or 0,
							'p_id':self.request.GET.get('program') or 0,
							'p_type':self.request.GET.get('pg_type') or 0})
		return SCATable

	def get_context_data(self, **kwargs):
		context = super(ApplicationMilestoneReport, self).get_context_data(**kwargs)
		SCATable = self.render_RA_table()
		context['table'] = SCATable(context['query'])
		return context

@method_decorator([staff_member_required,],name='dispatch')
class ProgChangeReportAjax(BaseProgChangeReport):
	token = PCRPTable().token

@method_decorator([staff_member_required,],name='dispatch')
class ProgramChangeReport(BaseProgramChangeReport):
	template_name = 'bits_admin/prog_change_report.html'

	def render_RA_table(self):
		PTable = PCRPTable()
		class SCATable(PTable):
			class Meta(PTable.Meta):
				ajax_source = reverse_lazy(
					'bits_admin:prog-change-report-ajax',
					kwargs={'b_id':self.request.GET.get('admit_batch')  or 0},)
		return SCATable

	def get_context_data(self, **kwargs):
		context = super(ProgramChangeReport, self).get_context_data(**kwargs)
		SCATable = self.render_RA_table()
		context['table'] = SCATable(context['query'])
		return context

@method_decorator([staff_member_required,],name='dispatch')
class ProgramLocationReport(BaseProgramLocationReport):
	template_name = 'bits_admin/prog_loc_report.html'

@method_decorator(staff_member_required,name='dispatch')
class FMLView(FeedDataView):

	token = mail_logs().token

	def get_queryset(self):
		query = super(FMLView, self).get_queryset()

		from_date = self.kwargs.get('fm_dt',None)
		to_date = self.kwargs.get('to_dt',None)

		from_date = from_date if not from_date == '00-00-0000' else None
		to_date = to_date if not to_date == '00-00-0000' else None

		if from_date and to_date :
			query=query.filter(mail_sent_time__range = [
				dt.strptime(from_date,"%Y-%m-%d %H:%M:%S"),
				dt.strptime(to_date,"%Y-%m-%d %H:%M:%S")
				] )
		elif from_date :
			query=query.filter(mail_sent_time__gte = dt.strptime(from_date,"%Y-%m-%d %H:%M:%S") )
		elif to_date :
			query=query.filter(mail_sent_time__lte = dt.strptime(to_date,"%Y-%m-%d %H:%M:%S") )

		return query

@staff_member_required
def followup_mail_logs(request):

	query = FollowUpMailLog.objects.all()

	to_date = request.GET.get("to_date",None)
	from_date = request.GET.get("from_date",None)

	data = {}

	if to_date :
		data['to_date'] = to_date
		t=to_date.split('-')
		to_date = dt( int(t[2]), int(t[1]), int(t[0]), 23, 59, 59 )
	

	if from_date :
		data['from_date'] = from_date
		t=from_date.split('-')
		from_date = dt( int(t[2]), int(t[1]), int(t[0]), 00, 00, 00 )
	

	if from_date and to_date :
		query=query.filter(mail_sent_time__range=[from_date,to_date])
	elif from_date :
		query = query.filter(mail_sent_time__gte=from_date)
	elif to_date:
		query = query.filter(mail_sent_time__lte=to_date)

	FollowupMailTable = mail_logs(from_date = from_date,to_date = to_date )

	table = FollowupMailTable(query)

	return render(request,'bits_admin/followup_mail_logs.html',
		{'table':table,
		'form':FollowupMailForm(data),
		})

def get_program_data(ap_id,cs,prog):
	amount = None
	pld = ProgramLocationDetails.objects.get(
				program=prog,
				location=cs.application.current_location
			)

	pfa = PROGRAM_FEES_ADMISSION.objects.get(
		program=prog,
		fee_type='1',
		latest_fee_amount_flag=True
	)
	try:
		amount = ExceptionListOrgApplicants.objects.get(
			Q(fee_amount__gte = 0.01)|Q(fee_amount__isnull=False),
			application__pk=int(ap_id),
			exception_type='2',
			program=prog,
			).fee_amount
	except ExceptionListOrgApplicants.DoesNotExist:
		amount = pfa.fee_amount
	return amount,pld

@staff_member_required
def adm_regen_offer(request,ap_id=None):
	cs = CandidateSelection.objects.get(application__pk=int(ap_id))
	amount=None
	template_name = cs.application.program.offer_letter_template
	try:
		amount,pld=get_program_data(ap_id,cs,cs.application.program)
		ap_exp = ApplicantExceptions.objects.get(applicant_email=cs.application.login_email.email,
			program = cs.application.program)
		template_name = ap_exp.offer_letter or template_name

		if ap_exp.transfer_program:
			amount,pld=get_program_data(ap_id,cs,ap_exp.transfer_program)
			template_name = (
					ap_exp.offer_letter or 
					ap_exp.transfer_program.offer_letter_template or 
					cs.application.program.offer_letter_template
			)		
					
	except (
		ApplicantExceptions.DoesNotExist, 
		ProgramLocationDetails.DoesNotExist,
		PROGRAM_FEES_ADMISSION.DoesNotExist,
		) as e:
		amount,pld=get_program_data(ap_id,cs,cs.application.program)

	cs.fee_payment_deadline_dt = pld.fee_payment_deadline_date
	cs.orientation_dt = pld.orientation_date
	cs.lecture_start_dt = pld.lecture_start_date
	cs.orientation_venue = pld.orientation_venue
	cs.lecture_venue = pld.lecture_venue
	cs.admin_contact_person = pld.admin_contact_person
	cs.acad_contact_person = pld.acad_contact_person
	cs.admin_contact_phone = pld.admin_contact_phone
	cs.acad_contact_phone = pld.acad_contact_phone
	cs.adm_fees = amount
	cs.offer_letter_generated_flag = True
	cs.offer_letter_regenerated_dt = timezone.now()
	cs.offer_letter_template = template_name
	cs.offer_letter = ol.render_offer_letter_content(cs)
	cs.save()

	return redirect(reverse('bits_admin:admin-offer-redirect',
		kwargs={'id':cs.application.id,
			'alert_status':True}))

@login_required
def get_program1(request):
	if request.is_ajax():
		pg = Program.objects.annotate(full_pg = Concat('program_code',Value(' - '),
			'program_name',Value(' ('),Upper('program_type'),Value(')'))).order_by('program_code')
		if request.GET.get('pg_type',None):
			pg = pg.filter(program_type = request.GET.get('pg_type',None))
		else:
			pg = pg.none()

		return JsonResponse({'pg': json.dumps(list(pg.values('pk','full_pg')), cls=DjangoJSONEncoder),})


@method_decorator([login_required, staff_member_required,],name='dispatch')
class StudentCourseReport(BaseStudentCourseReport):
	template_name = 'bits_admin/student_course_report.html'

	def render_RA_table(self):
		class SCATable(SCRTable):
			class Meta(SCRTable.Meta):
				ajax_source = reverse_lazy('bits_admin:student-course-report-ajax')
		return SCATable

	def get_context_data(self, **kwargs):
		context = super(StudentCourseReport, self).get_context_data(**kwargs)
		SCATable = self.render_RA_table()
		context['table'] = SCATable(context['query'])
		return context

@method_decorator([login_required,staff_member_required,],name='dispatch')
class StudentCourseReportDataView(BaseStudentCourseReportDataView):
	token = SCRTable.token

@method_decorator([login_required, staff_member_required],name='dispatch')
class ElectiveSelectionsAppData(BaseElectiveSelectionsAppData):
	template_name = 'bits_admin/elective_selections_app_view.html'

@method_decorator([login_required, staff_member_required],name='dispatch')
class ElectiveSelectionsAppAjaxData(BaseElectiveSelectionsAppAjaxData):
	token = elective_selections_paging().token


@method_decorator([login_required, staff_member_required],name='dispatch')
class EMIReportAppData(BaseEMIReportAppData):	
	template_name = 'bits_admin/emi_report.html'
	ajax_url = 'bits_admin_payment:emi-report-ajax'
	action_url = 'bits_admin:admin-application-views'


@method_decorator([login_required, staff_member_required],name='dispatch')
class EMIReportAppAjaxData(BaseEMIReportAppAjaxData):
	token = emi_report_paging(ajax_url='bits_admin_payment:emi-report-ajax', action_url = 'bits_admin:admin-application-views').token

@method_decorator([login_required, staff_member_required],name='dispatch')
class DefDocsAppAjaxData(DefDocView):
	token = def_doc_paging(ajax_url='bits_admin_payment:def-doc-ajax', action_url='bits_admin:admin-application-views').token

@method_decorator([login_required, staff_member_required],name='dispatch')
class DefDocsSubAjaxData(DefDocSubView):
	token = doc_sub_paging(ajax_url='bits_admin_payment:def-doc-sub-ajax', action_url = 'bits_admin:admin-application-views').token

@method_decorator([login_required, staff_member_required],name='dispatch')
class DefDocsAppData(BaseDefDocsAppData):
	template_name = 'bits_admin/def_doc_app_view.html'
	ajax_url = 'bits_admin_payment:def-doc-ajax'
	action_url = 'bits_admin:admin-application-views'

@method_decorator([login_required, staff_member_required],name='dispatch')
class DefDocsSubData(BaseDefDocsSubData):
	ajax_url = 'bits_admin_payment:def-doc-sub-ajax'
	action_url = 'bits_admin:admin-application-views'
	template_name = 'bits_admin/def_doc_fields_view.html'

@method_decorator([login_required, staff_member_required],name='dispatch')
class AdhocReportAppData(BaseAdhocReportAppData):
	ajax_url = 'bits_admin_payment:adhoc-report-ajax'

@method_decorator([login_required, staff_member_required],name='dispatch')
class AjaxAdhocReport(BaseAjaxAdhocReport):
	token = adhoc_zest_paging(ajax_url='bits_admin_payment:adhoc-report-ajax').token

@method_decorator([login_required, staff_member_required],name='dispatch')
class PreSelAppData(BasePreSelAppData):
	template_name = 'bits_admin/pre_sel_rej_view.html'
	ajax_url = 'bits_admin_payment:pre-sel-rej-app-ajax'
	action_url = 'bits_admin:admin-application-views'

@method_decorator([login_required, staff_member_required],name='dispatch')
class PreSelAppAjaxData(PreSelAppView):
	token = pre_sel_paging(ajax_url='bits_admin_payment:pre-sel-rej-app-ajax', action_url='bits_admin:admin-application-views').token

@method_decorator([login_required,staff_member_required,],name='dispatch')
class SendPreConfirmSelRejEmail(BaseSendPreConfirmSelRejEmail):
	success_url = reverse_lazy('bits_admin:adminapplicationViews')

@method_decorator([staff_member_required,],name='dispatch')
class AdminDMRCertification(BaseDMRCertification):
	template_name = 'bits_admin/dmr_certification.html'

@method_decorator([staff_member_required,],name='dispatch')
class AdminDMRCluster(BaseDMRCluster):
	template_name = 'bits_admin/dmr_cluster.html'

@method_decorator([staff_member_required,],name='dispatch')
class AdminDMRSpecific(BaseDMRSpecific):
	template_name = 'bits_admin/dmr_specific.html'

@login_required
def get_program_arch(request):
	if request.is_ajax():
		pg = ProgramArchived.objects.annotate(full_pg = Concat('program_code',Value(' - '),
			'program_name',Value(' ('),Upper('program_type'),Value(')'))).order_by('program_code')
		if request.GET.get('pg_type',None):
			pg = pg.filter(program_type = request.GET.get('pg_type',None))
		else:
			pg = pg.none()
		return JsonResponse({'pg': json.dumps(list(pg.values('pk','full_pg')), cls=DjangoJSONEncoder),})	


@method_decorator([staff_member_required,],name='dispatch')	
class ProgramAdmissionsReport(BaseProgramAdmissionReport):
	template_name = 'bits_admin/pgm_adm_report.html'
	ajax_url = 'bits_admin_payment:program-admissions-report-ajax'

@method_decorator([login_required,staff_member_required,],name='dispatch')
class ProgramAdmissionsReportAjax(BasePgmAdmReportAjaxData):
	token = pgm_adm_report_paging(ajax_url='bits_admin_payment:program-admissions-report-ajax',).token

# inbound
@method_decorator([login_required,staff_member_required,],name='dispatch')
class InboundView(BaseInboundView):pass

@method_decorator([login_required, staff_member_required],name='dispatch')
class InboundLogAjax(BaseInboundLogAjax):pass
	
# Outbound
@method_decorator([login_required,staff_member_required,],name='dispatch')
class OutboundView(BaseOutboundView):pass

@method_decorator([login_required, staff_member_required],name='dispatch')
class OutboundLogAjax(BaseOutboundLogAjax):pass


@method_decorator([login_required, staff_member_required],name='dispatch')
class EMIReportEduvAppData(BaseEMIReportEduvAppData):	
	template_name = 'bits_admin/emi_eduv_report.html'
	ajax_url = 'bits_admin_payment:emi-report-eduv-ajax'
	action_url = 'bits_admin:admin-application-views'


@method_decorator([login_required, staff_member_required],name='dispatch')
class EMIReportEduvAppAjaxData(BaseEMIReportEduvAppAjaxData):
	token = eduv_report_paging(ajax_url='bits_admin_payment:emi-report-eduv-ajax', action_url = 'bits_admin:admin-application-views').token

@method_decorator([login_required, staff_member_required],name='dispatch')
class AdhocReportEduvAppData(BaseAdhocReportEduvAppData):
	ajax_url = 'bits_admin_payment:adhoc-eduv-report-ajax'

@method_decorator([login_required, staff_member_required],name='dispatch')
class AjaxAdhocReportEduv(BaseAjaxAdhocReportEduv):
	token = adhoc_eduv_paging(ajax_url='bits_admin_payment:adhoc-eduv-report-ajax').token

@method_decorator([login_required, staff_member_required],name='dispatch')
class EMIReportEzcredAppData(BaseEMIReportEzcredAppData):	
	template_name = 'bits_admin/emi_ezcred_report.html'
	ajax_url = 'bits_admin_payment:emi-report-ezcred-ajax'
	action_url = 'bits_admin:admin-application-views'

@method_decorator([login_required, staff_member_required],name='dispatch')
class EMIReportEzcredAppAjaxData(BaseEMIReportEzcredAppAjaxData):
	token = ezcred_report_paging(ajax_url='bits_admin_payment:emi-report-ezcred-ajax', action_url = 'bits_admin:admin-application-views').token

@method_decorator([login_required, staff_member_required],name='dispatch')
class EMIReportPropelldAppData(BaseEMIReportPropelldAppData):	
	template_name = 'bits_admin/emi_propelld_report.html'
	ajax_url = 'bits_admin_payment:emi-report-propelld-ajax'
	action_url = 'bits_admin:admin-application-views'

@method_decorator([login_required, staff_member_required],name='dispatch')
class EMIReportPropelldAppAjaxData(BaseEMIReportPropelldAppAjaxData):
	token = propelld_report_paging(ajax_url='bits_admin_payment:emi-report-propelld-ajax', action_url = 'bits_admin:admin-application-views').token	

@method_decorator([login_required, staff_member_required],name='dispatch')
class AdhocReportPropelldAppData(BaseAdhocReportPropelldAppData):
	ajax_url = 'bits_admin_payment:adhoc-propelld-report-ajax'

@method_decorator([login_required, staff_member_required],name='dispatch')
class AjaxAdhocReportPropelld(BaseAjaxAdhocReportPropelld):
	token = adhoc_propelld_paging(ajax_url='bits_admin_payment:adhoc-propelld-report-ajax').token

