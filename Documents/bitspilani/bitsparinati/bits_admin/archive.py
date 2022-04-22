from registrations.models import *
from bits_admin.models import *
from bits_rest.models import ZestEmiTransaction, EduvanzApplication
from payment_reviewer.models import PaymentGatewayRecord, ManualPaymentDataUpload
from bits_admin.mapper import *
import uuid

def get_or_create_program(programs):
	program_mapping = {}
	for program in Program.objects.filter(pk__in=programs).iterator():
		instance, created = ProgramArchived.objects.get_or_create(
			program_code=program.program_code,
			defaults={
				'program': program,
				'program_name':program.program_name,
				'program_type':program.program_type,
				'form_title':program.form_title,
				'mentor_id_req':program.mentor_id_req,
				'hr_cont_req':program.hr_cont_req,
				'offer_letter_template':program.offer_letter_template,
			}
		)
		program_mapping[program.program_code] = instance
	return program_mapping

def get_or_create_degree(applications):
	degree_mapping = {}
	for x in StudentCandidateQualification.objects.filter(application__pk__in=applications).iterator():
		instance, created = DegreeArchived.objects.get_or_create(
			degree_short_name=x.degree.degree_short_name,
			defaults={
				'degree':x.degree,
				'degree_long_name':x.degree.degree_long_name,
				'qualification_category':x.degree.qualification_category and x.degree.qualification_category.category_name
			}
		)
		degree_mapping[x.degree.degree_short_name] = instance
	return degree_mapping

def create_initial_bulk_query(sca_queryset, run):
	program_mapping = get_or_create_program(sca_queryset.values_list('program', flat=True))
	degree_mapping = get_or_create_degree(sca_queryset.values_list('pk', flat=True).distinct())
	trial_id, tmp_run, (model, main_queryset, bulk_instances) = sca_mapper(program_mapping, sca_queryset, '-1')
	
	bulk_creation = StudentCandidateApplicationArchived.objects.bulk_create(bulk_instances)
	sca_arch_queryset = StudentCandidateApplicationArchived.objects.filter(
		application__in=sca_queryset.values_list('pk', flat=True),
		trial_id=trial_id
	)
	application_mapping = { x.application.pk:x.pk for x in sca_arch_queryset.iterator() }

	other_bulk_entries = related_model_mapper(program_mapping, degree_mapping, application_mapping, sca_queryset, run)

	return {
		'trail_id':trial_id, 'run':run, 'tmp_run':tmp_run, 'application_mapping':application_mapping, 
		'program_mapping':program_mapping, 'degree_mapping':degree_mapping, 'sca_queryset':sca_queryset,
		'other_bulk_entries':other_bulk_entries, 'sca_arch_queryset':sca_arch_queryset,
	}