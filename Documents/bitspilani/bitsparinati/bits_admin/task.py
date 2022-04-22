from __future__ import absolute_import, unicode_literals
from django.db import IntegrityError, transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import *
from django.db.models.functions import *
from datetime import datetime as dt
from bits_rest.models import ZestEmiTransaction,EduvanzApplication
from payment_reviewer.models import PaymentGatewayRecord,ManualPaymentDataUpload
from .models import *
from registrations.models import *
from celery import shared_task
from celery import task, current_task
from celery.result import AsyncResult
from registrations.bits_api import name_verify_api
import json
import time
from django.conf import settings
import datetime
import operator
from django.template.loader import render_to_string
from django.core.mail import send_mail

models_map = {
	StudentCandidateApplication._meta.model_name:
	{
		'popout':('id',),
		'relation_field':{
			'login_email_id':('login_email', 'pk', get_user_model(), 'email'),
			'current_location_id':('current_location', 'pk', Location, 'location_name'),
			'current_org_industry_id':('current_org_industry', 'pk', Industry, 'industry_name'),
			'work_location_id':('work_location', 'pk', Location, 'location_name'),
		},
		'reverted_relation_field':{
			'program_id':(
				'program',
				{
					'related_model':('pk', Program, 'program_code'),
					'reverted_model':('program_code', ProgramArchived),
				}
			),
		},
		'arch_model':StudentCandidateApplicationArchived,
	},
	CandidateSelection._meta.model_name:
	{
		'popout':('id',),
		'relation_field':{
			'rejection_by_candidate_reason_id':('rejection_by_candidate_reason', 'pk', ApplicantRejectionReason, 'reason'),
			'new_sel_prog_id':('new_sel_prog', 'pk', Program, 'program_code'),
			'admitted_to_program_id':('admitted_to_program', 'pk', Program, 'program_code'),
		},
		'reverted_relation_field':{
			'application_id':(
				'application',
				{
					'related_model':('pk', StudentCandidateApplication, 'student_application_id'),
					'reverted_model':('student_application_id', StudentCandidateApplicationArchived),
				}
			),
		},
		'arch_model':CandidateSelectionArchived,

	},
	ApplicationPayment._meta.model_name:
	{
		'popout':('id',),
		'relation_field':{},
		'reverted_relation_field':{
			'application_id':(
				'application',
				{
					'related_model':('pk', StudentCandidateApplication, 'student_application_id'),
					'reverted_model':('student_application_id', StudentCandidateApplicationArchived),
				}
			),
		},
		'arch_model':ApplicationPaymentArchived,

	},
	StudentCandidateWorkExperience._meta.model_name:
	{
		'popout':('id',),
		'relation_field':{},
		'reverted_relation_field':{
			'application_id':(
				'application',
				{
					'related_model':('pk', StudentCandidateApplication, 'student_application_id'),
					'reverted_model':('student_application_id', StudentCandidateApplicationArchived),
				}
			),
		},
		'arch_model':StudentCandidateWorkExperienceArchived,
	},
	StudentCandidateQualification._meta.model_name:
	{
		'popout':('id',),
		'relation_field':{
			'discipline_id':('discipline', 'pk', Discpline, 'discipline_name'),
		},

		'reverted_relation_field':{
			'application_id':(
				'application',
				{
					'related_model':('pk', StudentCandidateApplication, 'student_application_id'),
					'reverted_model':('student_application_id', StudentCandidateApplicationArchived),
				}
			),
			'degree_id':(
				'degree',
				{
					'related_model':('pk', Degree, 'degree_short_name'),
					'reverted_model':('degree_short_name', DegreeArchived),
				}
			),
		},
		'arch_model':StudentCandidateQualificationArchived,
	},
	ApplicationDocument._meta.model_name:
	{
		'popout':('program_document_map_id', 'id'),
		'relation_field':{
			'document_id':('document', 'pk', DocumentType, 'document_name'),
			'rejection_reason_id':('rejection_reason', 'pk', ApplicantionDocumentReason, 'reason'),

		},
		'reverted_relation_field':{
			'application_id':(
				'application',
				{
					'related_model':('pk', StudentCandidateApplication, 'student_application_id'),
					'reverted_model':('student_application_id', StudentCandidateApplicationArchived),
				}
			),
		},
		'arch_model':ApplicationDocumentArchived,

	},
	get_user_model()._meta.model_name:
	{
		'popout':('id',),
		'relation_field':{},
		'reverted_relation_field':{},
		'arch_model':CandidateLoginArchived,
	},
	ApplicantExceptions._meta.model_name:
	{
		'popout':('id', 'application_id',),
		'relation_field':{
			'program_id':('program', 'pk', Program, 'program_code'),
			'transfer_program_id':('transfer_program', 'pk', Program, 'program_code'),
			'org_id':('org', 'pk', CollaboratingOrganization, 'org_name'),

		},
		'reverted_relation_field':{},
		'arch_model':ApplicantExceptionsArchived,

	},
	ExceptionListOrgApplicants._meta.model_name:
	{
		'popout':('id',),
		'relation_field':{
			'program_id':('program', 'pk', Program, 'program_code'),
			'org_id':('org', 'pk', CollaboratingOrganization, 'org_name'),

		},
		'reverted_relation_field':{
			'application_id':(
				'application',
				{
					'related_model':('pk', StudentCandidateApplication, 'student_application_id'),
					'reverted_model':('student_application_id', StudentCandidateApplicationArchived),
				}
			),

		},
		'arch_model':ExceptionListOrgApplicantsArchived,
	},
	ZestEmiTransaction._meta.model_name:
	{
		'popout':('id',),
		'relation_field':{
			'program_id':('program', 'pk', Program, 'program_code'),
		},
		'reverted_relation_field':{
			'application_id':(
				'application',
				{
					'related_model':('pk', StudentCandidateApplication, 'student_application_id'),
					'reverted_model':('student_application_id', StudentCandidateApplicationArchived),
				}
			),
		},
		'arch_model':ZestEmiTransactionArchived,
	},
	StudentElectiveSelection._meta.model_name:
	{
		'popout':('id',),
		'relation_field':{
			'program_id':('program', 'pk', Program, 'program_code'),
			'student_id_id':('student_id', 'pk', CandidateSelection, 'student_id'),
			'course_id_slot_id':('course_id_slot', 'pk', FirstSemCourseList, 'course_id'),
			'course_units_id':('course_units', 'pk', ElectiveCourseList, 'course_units'),
			'course_id':('course', 'pk', ElectiveCourseList, 'course_id'),
			
		},
		'reverted_relation_field':{
			'application_id':(
				'application',
				{
					'related_model':('pk', StudentCandidateApplication, 'student_application_id'),
					'reverted_model':('student_application_id', StudentCandidateApplicationArchived),
				}
			),
		},
		'arch_model':StudentElectiveSelectionArchived,

	},
	StudentCandidateApplicationSpecific._meta.model_name:
	{
		'popout':('id',),
		'relation_field':{
			'collaborating_organization_id':('collaborating_organization', 'pk', CollaboratingOrganization, 'org_name'),
		},
		'reverted_relation_field':{
			'application_id':(
				'application',
				{
					'related_model':('pk', StudentCandidateApplication, 'student_application_id'),
					'reverted_model':('student_application_id', StudentCandidateApplicationArchived),
				}
			),
		},

		'arch_model':StudentCandidateApplicationSpecificArchived,
	},
	PaymentGatewayRecord._meta.model_name:{
		'popout':('id',),
		'relation_field':{},
		'reverted_relation_field':{
			'src_itc_application_id':(
				'src_itc_application',
				{
					'related_model':('pk', StudentCandidateApplication, 'student_application_id'),
					'reverted_model':('student_application_id', StudentCandidateApplicationArchived),
				}
			),
		},
		'arch_model':PaymentGatewayRecordArchived,
	},
	ManualPaymentDataUpload._meta.model_name:{
		'popout':('id',),
		'relation_field':{},
		'reverted_relation_field':{
			'application_id':(
				'application',
				{
					'related_model':('pk', StudentCandidateApplication, 'student_application_id'),
					'reverted_model':('student_application_id', StudentCandidateApplicationArchived),
				}
			),
		},
		'arch_model':ManualPaymentDataUploadArchived,
	},
	EduvanzApplication._meta.model_name:
	{
		'popout':('id',),
		'relation_field':{},
		'reverted_relation_field':{
			'application_id':(
				'application',
				{
					'related_model':('pk', StudentCandidateApplication, 'student_application_id'),
					'reverted_model':('student_application_id', StudentCandidateApplicationArchived),
				}
			),
		},
		'arch_model':EduvanzApplicationArchived,
	},
}

@shared_task
def archive_test(from_date=None,to_date=None,programs=None):

	print current_task ,"dfsfdfdfdfdfdfdfdf,"

	current_task.update_state(state="PROGRESS", meta={'message':'Archival Process Initiated'})
	time.sleep(12)
	current_task.update_state(state="PROGRESS", meta={'message':'Archival Process Initiated 2'})
	time.sleep(12)
	current_task.update_state(state="PROGRESS", meta={'message':'Archival Process Initiated 3'})
	time.sleep(12)
	current_task.update_state(state="PROGRESS", meta={'message':'Archival Process Initiated 4'})
	time.sleep(12)


error_tables = [
	StudentCandidateApplicationArchived, 
	CandidateSelectionArchived,
	ApplicationPaymentArchived, 
	StudentCandidateWorkExperienceArchived,
	StudentCandidateQualificationArchived, 
	ApplicationDocumentArchived,
	CandidateLoginArchived, 
	ApplicantExceptionsArchived, 
	ExceptionListOrgApplicantsArchived,
	ZestEmiTransactionArchived,StudentElectiveSelectionArchived,
	StudentCandidateApplicationSpecificArchived,
	PaymentGatewayRecordArchived,
	ManualPaymentDataUploadArchived,
	EduvanzApplicationArchived
]

def get_max_run():
	max_id = ArchiveAuditTable.objects.aggregate(Max('run'))['run__max']
	return max_id + 1 if max_id else 1

def get_or_create_program(programs):
	for program in programs.iterator():
		ProgramArchived.objects.get_or_create(
			program_code=program.program_code,
			defaults={
				'program_name':program.program_name,
				'program_type':program.program_type,
				'form_title':program.form_title,
				'mentor_id_req':program.mentor_id_req,
				'hr_cont_req':program.hr_cont_req,
				'offer_letter_template':program.offer_letter_template,
			}
		) 

def get_or_degree(applications):
	for x in StudentCandidateQualification.objects.filter(application__pk__in=applications).iterator():
		DegreeArchived.objects.get_or_create(
			degree_short_name=x.degree.degree_short_name,
			defaults={
				'degree_long_name':x.degree.degree_long_name,
				'qualification_category':x.degree.qualification_category and x.degree.qualification_category.category_name
			}
		)

def sca_filtered_model(admit_batch, programs, from_date, to_date):

	get_or_create_program(programs)

	sca = StudentCandidateApplication.objects.filter(program__active_for_applicaton_flag=False)

	filter_list = [
		('admit_batch', admit_batch), 
		('program__in', programs), 
		('created_on_datetime__range', 
			[
				settings.INDIAN_TIME_ZONE.localize(
					dt.combine(
						from_date if from_date else sca.aggregate(dt=Min('created_on_datetime'),)['dt'], 
						datetime.time.min
					)
				), 
				settings.INDIAN_TIME_ZONE.localize(
					dt.combine(
						to_date if to_date else sca.aggregate(dt=Max('created_on_datetime'),)['dt'], 
						datetime.time.max
					)
				)
			]
		),
	]
	sca = sca.filter(reduce(operator.and_, [ Q(**{x:y}) for (x,y) in filter_list if y ]))
	get_or_degree(sca.values_list('pk', flat=True))

	return sca

def filtered_model(programs, sca):

	return (
		get_user_model().objects.filter(pk__in=list(sca.values_list('login_email',flat=True))), 
		CandidateSelection.objects.filter(application__in=sca), 
		ApplicationPayment.objects.filter(application__in=sca), 
		StudentCandidateWorkExperience.objects.filter(application__in=sca ), 
		StudentCandidateQualification.objects.filter( application__in=sca), 
		ApplicationDocument.objects.filter(application__in=sca), 
		ExceptionListOrgApplicants.objects.filter(program__in=programs), 
		ZestEmiTransaction.objects.filter(application__in=sca), 
		StudentElectiveSelection.objects.filter(application__in=sca), 
		StudentCandidateApplicationSpecific.objects.filter(application__in=sca), 
		PaymentGatewayRecord.objects.filter(src_itc_application__in=sca), 
		ManualPaymentDataUpload.objects.filter(application__in=sca),
		EduvanzApplication.objects.filter(application__in=sca),
		ApplicantExceptions.objects.filter( 
			Q(program__in=programs)| 
			Q(application__candidateselection_requests_created_5550__admitted_to_program__in=programs) 
		).distinct(),
	)

def bulk_create(queryset, run_id):
	bulk_model = []
	relationship = models_map[queryset.model._meta.model_name]

	# current_task.update_state(
	# 	state="PROGRESS",
	# 	meta={
	# 		'message':'{} table Snapshot inprocess :{}/{}'.format(
	# 			queryset.model._meta.model_name,
	# 			len(bulk_model),
	# 			queryset.count()
	# 		)
	# 	}
	# )

	for query in queryset.values().iterator():
		params = query.copy()
		params['run'] = run_id

		for x in relationship['popout']:
			params.pop(x)

		for k,v in relationship['relation_field'].items():
			value = params.pop(k)
			try:
				model = v[2].objects.get(**{v[1]:value})
			except v[2].DoesNotExist as e:
				model = None
			params[v[0]] = getattr(model, v[3], None)

		for k,v in relationship['reverted_relation_field'].items():
			value = params.pop(k)
			try:
				model = v[1]['related_model'][1].objects.get(**{v[1]['related_model'][0]:value})
			except v[1]['related_model'][1].DoesNotExist as e:
				model = None


			try:
				r_model = v[1]['reverted_model'][1].objects.get(**{
						v[1]['reverted_model'][0]:getattr(model, v[1]['related_model'][2], None)
					}
				)
			except :
				r_model = None

			params[v[0]] = r_model

		bulk_model.append(relationship['arch_model'](**params))

		# current_task.update_state(
		# 	state="PROGRESS",
		# 	meta={
		# 		'message':'{} table Snapshot inprocess :{}/{}'.format(
		# 			queryset.model._meta.model_name,
		# 			len(bulk_model),
		# 			queryset.count()
		# 		)
		# 	}
		# )

	# current_task.update_state(state="PROGRESS", meta={
	# 		'message':'%s table Snapshot  created' % (queryset.model._meta.model_name,)
	# 	}
	# )

	return bulk_model


def upload_arch_model(queryset, arch_bulk, run_id, arch_filter):
	arch_model = models_map[queryset.model._meta.model_name]['arch_model']
	start_date = dt.now()
	arch_model.objects.bulk_create(arch_bulk)
	end_date = dt.now()
	ArchiveAuditTable.objects.create(run=run_id,
		table_name=queryset.model._meta.model_name,
		archive_start_datetime=start_date,
		rows_inserted=queryset.count(),
		archive_end_datetime = end_date,
		success_flag=True,
		arch_filter=arch_filter,
	)
	# current_task.update_state(
	# 	state="PROGRESS", 
	# 	meta={'message':'{0} tables archived'.format(queryset.model._meta.model_name)}
	# )

def delete_model(query_list):
	
	for x in query_list:
		if x.model.__name__=="User":
			records=x.delete()
		else:
			x.delete()	
	current_task.update_state(state="PROGRESS", meta={'message':'Data from source tables removed'})
	return records	
	
@shared_task
def archive_task(user, from_date=None, to_date=None, programs=None, admit_batch=None):

	current_task.update_state(state="PROGRESS", meta={'message':'Archival Process Initiated. Please Do Not Refresh'})
	creation_table = []
	bulk_models = []
	arch_filter = {
		'from_date' : str(from_date) if from_date else '',
		'to_date' : str(to_date) if to_date else '',
		'programs' : ', '.join( ( lambda x:x.values_list('program_code',flat=True) )( 
				programs if programs.exists() else Program.objects.all()
			)
		),
		'admit_batch' : admit_batch if admit_batch else '',
	}

	run_id = get_max_run()

	sca = sca_filtered_model(admit_batch, programs, from_date, to_date)
	program_codes_list = [i.program.program_code for i in sca]
	programs_archived = ', '.join((lambda x: x)(set(program_codes_list)))
	arch_filter['programs'] = programs_archived


	try:
		with transaction.atomic():
			sca = sca_filtered_model(admit_batch, programs, from_date, to_date)
			sca_bulk = bulk_create(sca, run_id)
			upload_arch_model(sca, sca_bulk, run_id, arch_filter)

			query_list = filtered_model(programs, sca)
			bulk_models = [ { 'queryset':queryset, 'bulk':bulk_create(queryset, run_id)} for queryset in query_list ] 

			for x in bulk_models:
				upload_arch_model(x['queryset'], x['bulk'], run_id, arch_filter)

			records=delete_model(query_list)
			print(records)
			if 'registrations.SaleForceLeadDataLog' in records[1] and 'registrations.SaleForceDocumentDataLog' in records[1] and 'registrations.SaleForceQualificationDataLog' in records[1] and 'registrations.SaleForceWorkExperienceDataLog' in records[1]:
				SaleForceLogCleanup.objects.create(logdel_start_datetime=dt.now(),
					logdel_end_datetime=dt.now(),
					sf_lead_rows_deleted=records[1]['registrations.SaleForceLeadDataLog'],
					sf_document_rows_deleted=records[1]['registrations.SaleForceDocumentDataLog'],
					sf_qualification_rows_deleted=records[1]['registrations.SaleForceQualificationDataLog'],
					sf_workexp_rows_deleted=records[1]['registrations.SaleForceWorkExperienceDataLog'])
			
		current_task.update_state(state="PROGRESS", meta={'message':'Archiving of data successfull'})

	except Exception as e:
		ArchiveAuditTable.objects.bulk_create([
			ArchiveAuditTable(
				run = run_id,
				table_name = v['arch_model']._meta.model_name,
				archive_start_datetime = dt.now(),
				rows_inserted = 0,
				archive_end_datetime = dt.now(),
				success_flag = False,
				failed_result = '{0}'.format(e),
				arch_filter = arch_filter,
				) for k,v in models_map.items()
			]
		)

		# current_task.update_state(state="PROGRESS", meta={'message':'failed to archive error :{}'.format(e)})

		subject = "Archival Process Failed"
		msg_plain = render_to_string('archival_failure.txt', {'program_list': programs_archived, 'user': user.username})
		msg_html = render_to_string('archival_failure.html', {'program_list': programs_archived, 'user': user.username})
		send_mail(subject, msg_plain,
				  '<' + 'ravisankar.reddy@accionlabs.com' + '>',
				  [user.email], html_message=msg_html,
				  fail_silently=True)

		return 'Archived process failed {}'.format(e)

	subject = "Archival Process Completed Successfully"
	msg_plain = render_to_string('archival_success.txt', {'program_list': programs_archived, 'user': user.username})
	msg_html = render_to_string('archival_success.html', {'program_list': programs_archived, 'user': user.username})
	send_mail(subject, msg_plain,
			  '<' + 'ravisankar.reddy@accionlabs.com' + '>',
			  [user.email], html_message=msg_html,
			  fail_silently=True)

	return 'bulk is done'

@shared_task(time_limit=1000)
def sdms_sync_task(programs=None,program_type=None,admit_batch=None,user_name=None,unsynced_data=None):
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
	pg1 = programs
	ptype = program_type
	batch = admit_batch
	query = query.filter(application__program__program_type=ptype) if ptype else query
	query = query.filter(application__program=pg1) if pg1 else query
	query = query.filter(application__admit_batch=batch) if batch else query
	if unsynced_data==True:
		query = query.filter(dps_flag=False)

	sync_data = None
	sync_error = False
	sync_success = False
	try:
		sync_data,meta_id_list = name_verify_api( query, user_name)
	except Exception as e:
		sync_data = [{'id_no': x.student_id,
		'sdms_status_code': 400,
		'sdms_error':str(e)} for x in query]
		sync_error = True

	else:
		for x in sync_data:
			if x['sdms_status_code'] == 200:
				cs = CandidateSelection.objects.get(student_id = x['id_no'])
				cs.dps_flag = True
				cs.dps_datetime = timezone.localtime(timezone.now())
				cs.save()
				sync_success = True
			else:
				sync_error = True
	resp_data = {}
	resp_data['synced_list'] = meta_id_list
	resp_data['sync_success'] = sync_success
	resp_data['sync_error'] = sync_error
	resp_data['form_data'] = {'pg_type': ptype, 'admit_batch': batch, 'programs': pg1}
	return resp_data
