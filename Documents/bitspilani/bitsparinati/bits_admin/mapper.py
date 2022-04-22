from registrations.models import *
from bits_admin.models import *
from bits_rest.models import ZestEmiTransaction, EduvanzApplication
from payment_reviewer.models import PaymentGatewayRecord, ManualPaymentDataUpload
from django.db.models import *
from django.db.models.functions import *
from django.db.models import  CharField, IntegerField
from django.contrib.auth import get_user_model
import uuid

archive_model = {
	get_user_model()._meta.model_name:CandidateLoginArchived,
	StudentCandidateApplicationArchived._meta.model_name:StudentCandidateApplicationArchived,
	CandidateLoginArchived._meta.model_name:CandidateLoginArchived,
	CandidateSelectionArchived._meta.model_name:CandidateSelectionArchived,
	ApplicationPaymentArchived._meta.model_name:ApplicationPaymentArchived,
	StudentCandidateWorkExperienceArchived._meta.model_name:StudentCandidateWorkExperienceArchived,
	StudentCandidateQualificationArchived._meta.model_name:StudentCandidateQualificationArchived,
	ApplicationDocumentArchived._meta.model_name:ApplicationDocumentArchived,
	ApplicantExceptionsArchived._meta.model_name:ApplicantExceptionsArchived,
	ExceptionListOrgApplicantsArchived._meta.model_name:ExceptionListOrgApplicantsArchived,
	ZestEmiTransactionArchived._meta.model_name:ZestEmiTransactionArchived,
	StudentElectiveSelectionArchived._meta.model_name:StudentElectiveSelectionArchived,
	StudentCandidateApplicationSpecificArchived._meta.model_name:StudentCandidateApplicationSpecificArchived,
	ManualPaymentDataUploadArchived._meta.model_name:ManualPaymentDataUploadArchived,
	EduvanzApplicationArchived._meta.model_name:EduvanzApplicationArchived,
	PaymentGatewayRecordArchived._meta.model_name:PaymentGatewayRecordArchived,
}

def bulk_instance_create(queryset, model, argument, alter_argument, reverted_model):
	bulk_instances = []
	for q in queryset.iterator():
		params = {}
		params.update({ x: getattr(q, x) for x in argument}) ##argument
		if alter_argument is not None:
			params.update({ k: getattr(q, v) for k, v in alter_argument.items()}) ##alt argument
		if reverted_model is not None:
			params.update({ k: l[getattr(q, v)] for k, l, v in reverted_model})
		bulk_instances.append(model(**params))
	return (model, queryset, bulk_instances)

def sca_mapper(program_mapping, sca_queryset, run):
	trial_id = str(uuid.uuid4().hex)
	
	return (
		trial_id,
		run, 
		bulk_instance_create(
			sca_queryset.annotate(
				work_location_name=F('work_location__location_name'),
				email=F('login_email__email'),
				current_location_name=F('current_location__location_name'),
				current_org_industry_name=F('current_org_industry__industry_name'),
				program_code=F('program__program_code'),
				trial_id=Value(trial_id, output_field=CharField()),
				run=Value(run, output_field=IntegerField()),
			), 
			archive_model[StudentCandidateApplicationArchived._meta.model_name], 
			[ 'full_name', 'first_name', 'middle_name', 'last_name', 'gender', 
				'date_of_birth', 'address_line_1', 'address_line_2', 'address_line_3', 'city', 'pin_code', 
				'state', 'country', 'application_status', 'current_organization', 'current_location', 
				'fathers_name', 'mothers_name', 'nationality', 'phone', 'mobile', 'email_id', 
				'current_employment_status', 'employer_consent_flag', 'employer_mentor_flag', 
				'current_org_employee_number', 'current_designation', 'fee_payment_owner', 
				'current_org_industry', 'current_org_employment_date', 'work_location', 'exam_location', 
				'total_work_experience_in_months', 'math_proficiency_level', 'prior_student_flag', 
				'bits_student_id', 'parallel_studies_flag', 'bonafide_flag', 'created_on_datetime', 
				'last_updated_on_datetime', 'student_application_id', 'admit_year', 'admit_sem_cohort', 
				'admit_batch', 'teaching_mode', 'pre_selected_flag', 'pre_selected_rejected_on_datetime', 
				'programming_flag', 'trial_id', 'run',
			], 
			{'login_email':'email', 'work_location':'work_location_name',
				'current_location':'current_location_name', 
				'current_org_industry':'current_org_industry_name',
				'application_id':'pk',
			}, 
			[('program', program_mapping, 'program_code'),],
		)
	)

def related_model_mapper(program_mapping, degree_mapping, application_mapping, sca_queryset, run):
	applications_pk = sca_queryset.values_list('pk', flat=True)
	emails = sca_queryset.values_list('login_email__email', flat=True)
	return {
		get_user_model()._meta.model_name:bulk_instance_create(
			get_user_model().objects.filter(email__in=emails).annotate(
				run=Value(run, output_field=IntegerField()),
				), 
			archive_model[CandidateLoginArchived._meta.model_name],
			['date_joined', 'email', 'first_name', 'is_active', 'is_staff', 'is_superuser',
				'last_login', 'last_name', 'password', 'username', 'run',
			], 
			None, 
			None
		),
		CandidateSelection._meta.model_name:bulk_instance_create(
			CandidateSelection.objects.filter(
				application__in=applications_pk
			).annotate(
				rej_reason=F('rejection_by_candidate_reason__reason'),
				new_pg_code=F('new_sel_prog__program_code'),
				admitted_pg_code=F('admitted_to_program__program_code'),
				application_pk=F('application__pk'),
				run=Value(run, output_field=IntegerField()),
			), 
			
			archive_model[CandidateSelectionArchived._meta.model_name], 
			[
				'student_id', 'old_student_id', 'verified_student_name', 'name_verified_on',
				'name_verified_by', 'selected_rejected_on', 'bits_rejection_reason',
				'selection_rejection_comments', 'bits_selection_rejection_by', 'accepted_rejected_by_candidate',
				'rejection_by_candidate_comments', 'offer_reject_mail_sent', 'es_to_su_rev',
				'es_com', 'su_rev_app', 'su_rev_com', 'es_to_su_rev_dt', 'app_rej_by_su_rev_dt',
				'prog_ch_flag', 'prior_status', 'new_application_id', 'm_name', 'm_des', 'm_mob_no',
				'm_email', 'hr_cont_name', 'hr_cont_des', 'hr_cont_mob_no', 'hr_cont_email', 'dps_flag',
				'dps_datetime', 'doc_resubmission_dt', 'fee_payment_deadline_dt', 'orientation_dt',
				'lecture_start_dt', 'orientation_venue', 'lecture_venue', 'admin_contact_person',
				'acad_contact_person', 'admin_contact_phone', 'acad_contact_phone', 'adm_fees',
				'offer_letter_generated_flag', 'offer_letter_regenerated_dt', 'offer_letter_template',
				'offer_letter', 'run',
			], 
			{
				'rejection_by_candidate_reason': 'rej_reason', 'new_sel_prog': 'new_pg_code', 
				'admitted_to_program':'admitted_pg_code',
			}, 
			[('application_id', application_mapping, 'application_pk'),],
		),
		ApplicationPayment._meta.model_name:bulk_instance_create(
			ApplicationPayment.objects.filter(
				application__in=applications_pk
			).annotate(
				application_pk=F('application__pk'),
				run=Value(run, output_field=IntegerField()),
			), 
			
			archive_model[ApplicationPaymentArchived._meta.model_name], 
			['payment_id', 'payment_amount', 'payment_date', 'payment_bank', 'transaction_id', 'run',
				'fee_type', 'tpsl_transaction', 'matched_with_payment_gateway','missing_from_gateway_file',
				'manual_upload_flag', 'inserted_from_gateway_file', 'insertion_datetime', 'insertion_approved_by',
			], 
			None, 
			[('application_id', application_mapping, 'application_pk'),]
		),
		StudentCandidateWorkExperience._meta.model_name:bulk_instance_create(
			StudentCandidateWorkExperience.objects.filter(
				application__in=applications_pk
			).annotate(
				application_pk=F('application__pk'),
				run=Value(run, output_field=IntegerField()),
			), 
			
			archive_model[StudentCandidateWorkExperienceArchived._meta.model_name], 
			[ 'organization', 'start_date', 'end_date', 'designations', 'run',], 
			None, 
			[('application_id', application_mapping, 'application_pk'),]
		),
		StudentCandidateQualification._meta.model_name:bulk_instance_create(
			StudentCandidateQualification.objects.filter(
				application__in=applications_pk
			).annotate(
				application_pk=F('application__pk'),
				degree_short_name=F('degree__degree_short_name'),
				run=Value(run, output_field=IntegerField()),
			), 
			
			archive_model[StudentCandidateQualificationArchived._meta.model_name], 
			['school_college', 'duration', 'percentage_marks_cgpa', 'completion_year',
				'division', 'degree', 'discipline', 'other_degree', 'other_discipline', 'run',
			], 
			None, 
			[('application_id', application_mapping, 'application_pk'), 
				('degree', degree_mapping, 'degree_short_name')
			]
		),
		ApplicationDocument._meta.model_name:bulk_instance_create(
			ApplicationDocument.objects.filter(
				application__in=applications_pk
			).annotate(
				application_pk=F('application__pk'),
				rej_reason=F('rejection_reason__reason'),
				document_name=F('document__document_name'),
				run=Value(run, output_field=IntegerField()),
			), 
			
			archive_model[ApplicationDocumentArchived._meta.model_name], 
			['file', 'last_uploaded_on', 'certification_flag', 'reload_flag',
				'accepted_verified_by_bits_flag', 'inspected_on', 'rejected_by_bits_flag',
				'verified_rejected_by', 'exception_notes', 'run',
			], 
			{'rejection_reason': 'rej_reason', 'document': 'document_name'}, 
			[('application_id', application_mapping, 'application_pk'),]
		),
		ApplicantExceptions._meta.model_name:bulk_instance_create(
			ApplicantExceptions.objects.filter(applicant_email__in=emails).annotate(
				application_pk=F('application__pk'),
				org_name=F('org__org_name'),
				transfer_pg_code=F('transfer_program__program_code'),
				program_code=F('program__program_code'),
				run=Value(run, output_field=IntegerField()),
			), 
			
			archive_model[ApplicantExceptionsArchived._meta.model_name], 
			[ 'applicant_email', 'work_ex_waiver', 'employment_waiver', 'mentor_waiver',
				'offer_letter', 'hr_contact_waiver', 'created_on_datetime', 'run',
			], 
			{'org': 'org_name', 'transfer_program': 'transfer_pg_code', 'program':'program_code'}, 
			None
		),
		ExceptionListOrgApplicants._meta.model_name:bulk_instance_create(
			ExceptionListOrgApplicants.objects.filter(
				application__in=applications_pk
			).annotate(
				application_pk=F('application__pk'),
				org_name=F('org__org_name'),
				program_code=F('program__program_code'),
				run=Value(run, output_field=IntegerField()),
			), 
			
			archive_model[ExceptionListOrgApplicantsArchived._meta.model_name], 
			['employee_email', 'exception_type', 'employee_id', 'employee_name', 'fee_amount', 'run',], 
			{'org':'org_name', 'program':'program_code'}, 
			[('application_id', application_mapping, 'application_pk'),]
		),
		ZestEmiTransaction._meta.model_name:bulk_instance_create(
			ZestEmiTransaction.objects.filter(
				application__in=applications_pk
			).annotate(
				application_pk=F('application__pk'),
				program_code=F('program__program_code'),
				run=Value(run, output_field=IntegerField()),
			), 
			
			archive_model[ZestEmiTransactionArchived._meta.model_name], 
			[ 'order_id', 'customer_id', 'requested_on', 'is_application_complete', 'run',
				'approved_or_rejected_on', 'is_approved', 'is_terms_and_condition_accepted', 'req_json_data',
				'amount_requested', 'amount_approved', 'status', 'is_cancelled', 'cancelled_on',
			], 
			{'program':'program_code'}, 
			[('application_id', application_mapping, 'application_pk'),]
		),
		StudentElectiveSelection._meta.model_name:bulk_instance_create(
			StudentElectiveSelection.objects.filter(
				application__in=applications_pk
			).annotate(
				application_pk=F('application__pk'),
				program_code=F('program__program_code'),
				student_id_stud=F('student_id__student_id'),
				course_id_slot_c_id=F('course_id_slot__course_id'),
				course_units_c_u=F('course_units__course_units'),
				course_c_id=F('course__course_id'),
				run=Value(run, output_field=IntegerField()),
			), 
			
			archive_model[StudentElectiveSelectionArchived._meta.model_name], 
			['inserted_on_datetime', 'last_updated_on_datetime', 'is_locked', 'run',], 
			{'program':'program_code', 'student_id':'student_id_stud', 'course':'course_c_id',
				'course_id_slot':'course_id_slot_c_id', 'course_units': 'course_units_c_u',
			}, 
			[('application_id', application_mapping, 'application_pk'),]
		),
		StudentCandidateApplicationSpecific._meta.model_name:bulk_instance_create(
			StudentCandidateApplicationSpecific.objects.filter(
				application__in=applications_pk
			).annotate(
				application_pk=F('application__pk'),
				organization=F('collaborating_organization__org_name'),
				run=Value(run, output_field=IntegerField()),
			), 
			
			archive_model[StudentCandidateApplicationSpecificArchived._meta.model_name], 
			['run',], 
			{'collaborating_organization':'organization'}, 
			[('application_id', application_mapping, 'application_pk'),]
		),
		ManualPaymentDataUpload._meta.model_name:bulk_instance_create(
			ManualPaymentDataUpload.objects.filter(
				application__in=applications_pk
			).annotate(
				application_pk=F('application__pk'),
				run=Value(run, output_field=IntegerField()),
			), 
			archive_model[ManualPaymentDataUploadArchived._meta.model_name], 
			[
				'payment_id','payment_type','payment_date','payment_amount','payment_mode','uploaded_by',
				'uploaded_on_date','payment_reversal_flag','status','accepted_rejected_datetime',
				'accepted_rejected_by','upload_filename', 'run',
			], 
			None, 
			[('application_id', application_mapping, 'application_pk'),]
		),
		EduvanzApplication._meta.model_name:bulk_instance_create(
			EduvanzApplication.objects.filter(
				application__in=applications_pk
			).annotate(
				application_pk=F('application__pk'),
				run=Value(run, output_field=IntegerField()),
			),
			archive_model[EduvanzApplicationArchived._meta.model_name], 
			[ 'order_id', 'is_approved', 'is_terms_and_condition_accepted', 
				'amount_requested', 'amount_approved', 'status_code', 'created_on', 'updated_on', 
				'approved_or_rejected_on', 'lead_id', 'callback_meta', 'run',
			], 
			None, 
			[('application_id', application_mapping, 'application_pk'),]
		),
		PaymentGatewayRecord._meta.model_name:bulk_instance_create(
			PaymentGatewayRecord.objects.filter(
				src_itc_application__in=applications_pk
			).annotate(
				application_pk=F('src_itc_application__pk'),
				run=Value(run, output_field=IntegerField()),
			), 
			archive_model[PaymentGatewayRecordArchived._meta.model_name], 
			[ 'tpsl_transaction_id', 'bank_id', 'bank_name', 'sm_transaction_id', 
				'bank_transaction_id', 'total_amount', 'charges', 'service_tax', 'net_amount', 
				'transaction_date', 'src_itc_user_id', 'src_itc_user_name', 'src_itc_mobile', 
				'uploaded_by', 'uploaded_on_datetime', 'payment_file_name', 'payment_report_date', 
				'status', 'missing_in_application_center', 'accepted_rejected_datetime', 
				'accepted_rejected_by', 'run',
			], 
			None, 
			[('src_itc_application_id', application_mapping, 'application_pk'),]
		),
	}