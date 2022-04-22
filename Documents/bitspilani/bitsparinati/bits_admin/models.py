from __future__ import unicode_literals
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User, UserManager, AbstractBaseUser
from django.db import models
import uuid
from phonenumber_field.modelfields import PhoneNumberField
from registrations.models import StudentCandidateApplication, Location, Program, Degree
from bits.bits_storage import MediaStorage
from easy_thumbnails.fields import ThumbnailerImageField
import jsonfield


def user_directory_path(instance, filename):
	return 'archived/{}/{}'.format(uuid.uuid4(),filename)

def document_upload_page_path(instance, filename):
	return 'pg_doc_archive/{}/{}'.format(uuid.uuid4(),filename)

class ArchiveAuditTable(models.Model):
	run = models.IntegerField()
	table_name = models.CharField(max_length=100,blank=True, null=True)
	archive_start_datetime = models.DateTimeField(blank=True, null=True)
	rows_inserted = models.PositiveIntegerField()
	archive_end_datetime = models.DateTimeField(blank=True, null=True)
	success_flag = models.BooleanField(default=False)
	arch_filter = jsonfield.JSONField(blank=True, null=True)
	failed_result = models.CharField(max_length=100,blank=True, null=True)

	def __unicode__(self):
		"""Return Unicode First Name."""
		return unicode(self.run)

class ProgramArchived(models.Model):
	program_code = models.CharField(max_length=6)  # Field name made lowercase.
	program_name = models.CharField(max_length=60,)  # Field name made lowercase.
	form_title = models.CharField(max_length=200,)
	program_type = models.CharField(max_length=30)
	mentor_id_req = models.BooleanField(default=True)
	hr_cont_req = models.BooleanField(default=True)
	offer_letter_template = models.CharField(max_length=60, blank=True, null=True)
	program = models.ForeignKey(Program, related_name='%(class)s_1', blank=True, null=True, on_delete=models.SET_NULL)

	def __unicode__(self):
		"""Return Unicode Program Names."""
		return unicode("{0} - {1} ({2})".format(self.program_code,self.program_name,
			self.program_type.upper()))


class StudentCandidateApplicationArchived(models.Model):
	"""Model for Student Candidate Application."""

	table_name = 'StudentCandidateApplication'
	run = models.IntegerField()
	login_email = models.EmailField(max_length=50, blank=True, null=True)
	full_name = models.CharField(max_length=100, blank=True, null=True)
	pin_code = models.PositiveIntegerField(blank=True, null=True)
	first_name = models.CharField(max_length=50, blank=True, null=True) 
	middle_name = models.CharField(max_length=50, blank=True, null=True)
	last_name = models.CharField(max_length=50, blank=True, null=True)  
	gender = models.CharField(max_length=10,)
	date_of_birth = models.DateField()
	address_line_1 = models.CharField(max_length=100)
	address_line_2 = models.CharField(max_length=100, blank=True, null=True)
	address_line_3 = models.CharField(max_length=100, blank=True, null=True)
	city = models.CharField(max_length=20, blank=True, null=True)
	state = models.CharField(max_length=20,)
	country = models.CharField(max_length=20,)
	application_status = models.CharField(max_length=70, blank=True, null=True)
	current_organization = models.CharField(max_length=50, blank=True,null=True)
	program_code = models.CharField(max_length=50,blank=True, null=True)
	program = models.ForeignKey(ProgramArchived, related_name='%(class)s_requests_created_6',blank=True, null=True)
	current_location = models.CharField(max_length=50,blank=True,null=True) 
	fathers_name = models.CharField(max_length=100, blank=True, null=True)
	mothers_name = models.CharField(max_length=100, blank=True, null=True)
	nationality = models.CharField(max_length=15, blank=True, null=True)
	phone = models.CharField(max_length=20, blank=True, null=True)  
	mobile = models.CharField(max_length=20, blank=True, null=True)  
	email_id = models.EmailField(blank=True, null=True)
	current_employment_status = models.CharField(max_length=20, blank=True, null=True)
	employer_consent_flag = models.BooleanField(default=False)
	employer_mentor_flag = models.BooleanField(default=False)
	current_org_employee_number = models.CharField(max_length=15, blank=True, null=True)  
	current_designation = models.CharField(max_length=30, blank=True, null=True)  
	fee_payment_owner = models.CharField(max_length=50, blank=True, null=True) 
	current_org_industry = models.CharField( max_length=50, blank=True,null=True)  
	current_org_employment_date = models.DateField()
	work_location = models.CharField(max_length=50, blank=True,null=True)  
	exam_location = models.CharField(max_length=45, blank=True, null=True)

	total_work_experience_in_months = models.IntegerField(blank=True, null=True)
	math_proficiency_level = models.CharField(max_length=45,blank=True, null=True)
	prior_student_flag = models.CharField(max_length=45,blank=True, null=True)
	bits_student_id = models.CharField(max_length=15, blank=True, null=True)
	parallel_studies_flag = models.CharField(max_length=45,blank=True, null=True) 
	bonafide_flag = models.BooleanField(default=True)
	created_on_datetime = models.DateTimeField( blank=True)
	last_updated_on_datetime = models.DateTimeField( blank=True)  
	student_application_id = models.CharField(max_length=20, blank=True, null=True) 
	admit_year = models.PositiveIntegerField()
	admit_sem_cohort = models.PositiveIntegerField(blank=True, null=True,)
	admit_batch = models.CharField(max_length=50, blank=True, null=True)
	teaching_mode = models.CharField(max_length=45, blank=True, null=True)
	pre_selected_flag = models.CharField(max_length=10, blank=True, null=True)
	pre_selected_rejected_on_datetime = models.DateTimeField(blank=True, null=True)
	programming_flag = models.CharField(max_length=10, blank=True, null=True)
	application = models.ForeignKey(StudentCandidateApplication, 
		related_name='%(class)s_1', blank=True, null=True, on_delete=models.SET_NULL)
	trial_id = models.CharField(max_length=100, blank=True, null=True)
	alternate_email_id = models.EmailField(max_length=50, blank=True, null=True)


	def __unicode__(self):
		"""Return Unicode First Name."""
		return unicode(self.full_name)

	def fullname(self):
		return self.full_name

class CandidateSelectionArchived(models.Model):
	table_name = 'CandidateSelection'
	run = models.IntegerField()
	application = models.ForeignKey(StudentCandidateApplicationArchived,
									related_name='%(class)s_1',blank=True, null=True)
	application_pk = models.CharField(max_length=20,blank=True, null=True)
	student_id = models.CharField(max_length=11,blank=True, null=True)
	old_student_id = models.CharField(max_length=11,blank=True, null=True)
	verified_student_name = models.CharField(max_length=100,blank=True, null=True)
	name_verified_on = models.DateTimeField(blank=True, null=True)
	name_verified_by = models.CharField(max_length=45,blank=True, null=True)
	selected_rejected_on = models.DateTimeField(blank=True, null=True)
	bits_rejection_reason = models.TextField(blank=True, null=True)
	selection_rejection_comments = models.CharField(max_length=45,blank=True, null=True)
	bits_selection_rejection_by = models.CharField(max_length=45,blank=True, null=True)
	accepted_rejected_by_candidate = models.DateTimeField(blank=True, null=True)
	rejection_by_candidate_reason = models.CharField(max_length=250,blank=True, null=True)
	rejection_by_candidate_comments = models.CharField(max_length=50,blank=True, null=True)
	offer_reject_mail_sent = models.DateTimeField(blank=True, null=True)


	es_to_su_rev = models.BooleanField(default=False)
	es_com = models.CharField(max_length=100,blank=True, null=True)
	su_rev_app = models.BooleanField(default=False)
	su_rev_com = models.CharField(max_length=100,blank=True, null=True)
	es_to_su_rev_dt = models.DateTimeField(blank=True, null=True)
	app_rej_by_su_rev_dt = models.DateTimeField(blank=True, null=True)
	prog_ch_flag = models.BooleanField(default=False)
	new_sel_prog = models.CharField(max_length=20,blank=True, null=True)
	prior_status = models.CharField(max_length=70,blank=True, null=True)
	new_application_id = models.CharField(max_length=60, blank=True, null=True)


	m_name = models.CharField(max_length=60,blank=True, null=True)
	m_des = models.CharField(max_length=30,blank=True, null=True)
	m_mob_no = PhoneNumberField(blank=True, null=True)
	m_email = models.EmailField(blank=True, null=True)

	hr_cont_name = models.CharField(max_length=60,blank=True, null=True)
	hr_cont_des = models.CharField(max_length=30,blank=True, null=True)
	hr_cont_mob_no = PhoneNumberField(blank=True, null=True)
	hr_cont_email = models.EmailField(blank=True, null=True)

	dps_flag = models.BooleanField(default=False)
	dps_datetime = models.DateTimeField(blank=True, null=True)

	doc_resubmission_dt = models.DateTimeField(blank=True, null=True)
	fee_payment_deadline_dt = models.DateTimeField(blank=True, null=True)
	orientation_dt = models.DateTimeField(blank=True, null=True)
	lecture_start_dt = models.DateTimeField(blank=True, null=True)
	orientation_venue = models.CharField(max_length=100,blank=True, null=True)
	lecture_venue = models.CharField(max_length=100,blank=True, null=True)
	admin_contact_person = models.CharField(max_length=50,blank=True, null=True)
	acad_contact_person = models.CharField(max_length=50,blank=True, null=True)
	admin_contact_phone = PhoneNumberField(blank=True, null=True)
	acad_contact_phone = PhoneNumberField(blank=True, null=True)
	adm_fees = models.FloatField(blank=True, null=True)
	offer_letter_generated_flag = models.BooleanField(default=False)
	offer_letter_regenerated_dt = models.DateTimeField(blank=True, null=True)
	admitted_to_program = models.CharField(max_length=50, blank=True, null=True)
	offer_letter_template = models.CharField(max_length=50, blank=True, null=True)
	offer_letter_tmp = models.TextField(blank=True, null=True)
	offer_letter = models.FileField(upload_to=user_directory_path, 
		blank=True, null=True, max_length=1000)

	def __unicode__(self):
		return unicode(self.application)


class ApplicationPaymentArchived(models.Model):

	table_name = 'ApplicationPayment'
	run = models.IntegerField()
	application = models.ForeignKey(StudentCandidateApplicationArchived,
									related_name='%(class)s_2',blank=True, null=True)
	application_pk = models.CharField(max_length=45)  
	payment_id = models.CharField(max_length=45)  
	payment_amount = models.CharField(max_length=45)
	payment_date = models.DateTimeField()
	payment_bank = models.CharField(max_length=45)
	transaction_id = models.CharField(max_length=45)
	fee_type = models.CharField(max_length=16)

	tpsl_transaction = models.CharField(max_length=45,blank=True, null=True)
	matched_with_payment_gateway = models.BooleanField(default=False)
	missing_from_gateway_file = models.BooleanField(default=False)
	manual_upload_flag = models.BooleanField(default=False)
	inserted_from_gateway_file = models.BooleanField(default=False)
	insertion_datetime = models.DateTimeField(blank=True, null=True)
	insertion_approved_by = models.CharField(max_length=50, blank=True, null=True)

	def __unicode__(self):
		return unicode(self.payment_id)


class StudentCandidateWorkExperienceArchived(models.Model):

	table_name = 'StudentCandidateWorkExperience'
	run = models.IntegerField()
	application = models.ForeignKey(StudentCandidateApplicationArchived,
									related_name='%(class)s_3',blank=True, null=True)
	application_pk = models.CharField(max_length=50,blank=True, null=True)  
	organization = models.CharField(max_length=50,blank=True, null=True)
	start_date = models.DateField(blank=True, null=True)
	end_date = models.DateField(blank=True, null=True)
	designations = models.CharField(max_length=100,blank=True, null=True)

	def __unicode__(self):
		return unicode(self.designations)

class DegreeArchived(models.Model):

	degree_short_name = models.CharField(max_length=30, blank=True, null=True)
	degree_long_name = models.CharField(max_length=45, blank=True, null=True)
	qualification_category = models.CharField(max_length=70, blank=True, null=True)
	degree = models.ForeignKey(Degree, related_name='%(class)s_1', 
		blank=True, null=True, on_delete=models.SET_NULL)

	def __unicode__(self):
		return unicode( self.degree_short_name )

class StudentCandidateQualificationArchived(models.Model):

	table_name = 'StudentCandidateQualification'
	run = models.IntegerField()
	application = models.ForeignKey(StudentCandidateApplicationArchived,
		related_name='%(class)s_4',blank=True, null=True)
	application_pk = models.CharField(max_length=45, blank=True, null=True)
	school_college = models.CharField(max_length=45, blank=True, null=True)
	duration = models.CharField(max_length=45, blank=True, null=True)
	percentage_marks_cgpa = models.DecimalField(max_digits=10, decimal_places=2,
	 blank=True, null=True)  
	completion_year = models.CharField(max_length=5, blank=True, null=True)
	division = models.CharField(max_length=20, blank=True, null=True)
	degree = models.ForeignKey(DegreeArchived,
		related_name='%(class)s_1',blank=True, null=True)
	degree_pk = models.CharField(max_length=50, blank=True, null=True)
	discipline = models.CharField(max_length=100, blank=True, null=True)
	other_degree = models.CharField(max_length=100, blank=True, null=True)
	other_discipline = models.CharField(max_length=100, blank=True, null=True)

	def __unicode__(self):
		"""Return College."""
		return unicode(self.school_college)

class ApplicationDocumentArchived(models.Model):

	table_name = 'ApplicationDocument'
	run = models.IntegerField()
	application = models.ForeignKey(StudentCandidateApplicationArchived,
									related_name='%(class)s_5',blank=True, null=True)
	application_pk = models.CharField(max_length = 20, blank=True, null=True) 
	document = models.CharField(max_length = 100, blank=True, null=True)
	file = models.FileField(upload_to = user_directory_path, blank=True, null=True, max_length=1000)
	last_uploaded_on = models.DateTimeField(blank=True, null=True)
	certification_flag = models.BooleanField(default=False)
	reload_flag = models.BooleanField(default=False)
	accepted_verified_by_bits_flag = models.BooleanField(default=False)
	inspected_on = models.DateTimeField(blank=True, null=True)
	rejected_by_bits_flag = models.BooleanField(default=False)
	rejection_reason = models.CharField(max_length=100, blank=True, null=True)
	verified_rejected_by = models.CharField(max_length=100,blank=True, null=True)
	exception_notes = models.CharField(max_length=100,blank=True, null=True)

	def __unicode__(self):
		"""Return unicode."""
		return unicode(self.file.name.split("/")[-1])

class CandidateLoginArchived(models.Model):
	table_name = 'CandidateLogin'
	run = models.IntegerField()
	date_joined = models.DateTimeField(blank=True, null=True)
	email = models.EmailField(blank=True, null=True)
	first_name = models.CharField(max_length = 50, blank=True, null=True)
	is_active = models.BooleanField(default=False)
	is_staff = models.BooleanField(default=False)
	is_superuser = models.BooleanField(default=False)
	last_login = models.DateTimeField(blank=True, null=True)
	last_name = models.CharField(max_length = 50, blank=True, null=True)
	password = models.CharField(max_length = 128, blank=True, null=True)
	username = models.CharField(max_length = 254, blank=True, null=True)
        
        def __unicode__(self):
		"""Return unicode."""
		return unicode(self.email)

class ApplicantExceptionsArchived(models.Model):
	table_name = 'ApplicantExceptions'
	run = models.IntegerField()
	applicant_email = models.EmailField('Applicant email ID / user ID')
	program =  models.CharField(max_length=50,blank=True, null=True)
	work_ex_waiver = models.BooleanField('Work Experience waiver required?',default=False)
	employment_waiver = models.BooleanField('Employment waiver required (candidate can be unemployed while applying)?',
		default=False)
	mentor_waiver = models.BooleanField('Mentor details not required to be provided?',
		default=False)
	offer_letter = models.CharField(max_length=50,blank=True, null=True)
	hr_contact_waiver = models.BooleanField('HR contact details not required to be provided?',
		default=False)
	org = models.CharField(max_length=50,blank=True, null=True)
	created_on_datetime = models.DateTimeField(auto_now_add=True, blank=True)
	transfer_program = models.CharField(max_length=50,blank=True, null=True)

	def __unicode__(self):
		"""Return Unicode Applicant Email."""
		return unicode(self.applicant_email)


class ExceptionListOrgApplicantsArchived(models.Model):
	table_name = 'ExceptionListOrgApplicants'
	run = models.IntegerField()
	application = models.ForeignKey(
		StudentCandidateApplicationArchived, related_name='%(class)s_5',
		blank=True, null=True
	)
	employee_email = models.EmailField(max_length=50)
	exception_type = models.CharField(max_length=50,blank=True, null=True)
	org = models.CharField(max_length=50,blank=True, null=True)
	program = models.CharField(max_length=50,blank=True, null=True)
	employee_id = models.CharField(max_length=15,blank=True, null=True)
	employee_name = models.CharField(max_length=50,blank=True, null=True)
	fee_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

	def __unicode__(self):
		"""Return Unicode Designation."""
		return self.employee_name

class ZestEmiTransactionArchived(models.Model):
	table_name = 'ZestEmiTransaction'
	run = models.IntegerField()
	application = models.ForeignKey(StudentCandidateApplicationArchived,
									related_name='%(class)s_6',blank=True, null=True)
	application_pk = models.CharField(max_length=20,blank=True, null=True)
	program = models.CharField(max_length=50,blank=True, null=True)
	order_id = models.TextField(blank=True, null=True)
	customer_id = models.TextField(blank=True, null=True)
	requested_on = models.DateTimeField(blank=True, null=True)
	is_application_complete = models.BooleanField(default=False)
	approved_or_rejected_on = models.DateTimeField(blank=True, null=True)
	is_approved = models.BooleanField(default=False)
	is_terms_and_condition_accepted = models.BooleanField(default=False)
	req_json_data = jsonfield.JSONField(blank=True, null=True)
	amount_requested = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
	amount_approved = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
	status = models.CharField(max_length=50, blank=True, null=True)
	is_cancelled = models.BooleanField(default=False)
	cancelled_on = models.DateTimeField(blank=True, null=True)
	zest_emi_link = models.TextField(null=True, blank=True)
	callback_meta = jsonfield.JSONField(blank=True, null=True)

	def __unicode__(self):
		"""Return unicode."""
		return unicode(self.customer_id)

class MetaZestArchived(models.Model):
	table_name = 'MetaZest'
	run = models.IntegerField()
	user = models.CharField(max_length=20,blank=True, null=True)
	errors = jsonfield.JSONField(blank=True, null=True)
	created_on_datetime = models.DateTimeField()

	def __unicode__(self):
		"""Return unicode."""
		return unicode(self.created_on_datetime)

class StudentElectiveSelectionArchived(models.Model):
	table_name = 'StudentElectiveSelection'
	run = models.IntegerField()
	student_id = models.CharField(max_length=11, blank=True, null=True)
	program = models.CharField(max_length=50, blank=True, null=True)
	application = models.ForeignKey(StudentCandidateApplicationArchived,
									related_name='%(class)s_7',blank=True, null=True)
	application_pk = models.CharField(max_length=20, blank=True, null=True)
	course_id_slot = models.CharField(max_length = 20, blank=True, null=True)
	course_units = models.PositiveIntegerField(blank=True, null=True)
	course = models.CharField(max_length = 20, blank=True, null=True)
	inserted_on_datetime = models.DateTimeField()
	last_updated_on_datetime = models.DateTimeField()
	is_locked = models.BooleanField(default=False)

	def __unicode__(self):
		return unicode(self.student_id)

class StudentCandidateApplicationSpecificArchived(models.Model):
	table_name = 'StudentCandidateApplicationSpecific'
	run = models.IntegerField()
	application = models.ForeignKey(StudentCandidateApplicationArchived,
									related_name='%(class)s_8',blank=True, null=True)
	application_pk = models.CharField(max_length=20, blank=True, null=True)
	collaborating_organization = models.CharField(max_length=60, blank=True, null=True)

	def __unicode__(self):
		"""Return unicode."""
		return unicode(self.collaborating_organization)

class PaymentGatewayRecordArchived(models.Model):

	table_name = 'PaymentGatewayRecord'
	run = models.IntegerField()
	src_itc_application = models.ForeignKey(StudentCandidateApplicationArchived,
		related_name='%(class)s_8', blank=True, null=True)
	src_itc_application_pk = models.CharField(max_length=20, blank=True, null=True)
	tpsl_transaction_id = models.CharField(max_length=20)
	bank_id = models.PositiveIntegerField()
	bank_name = models.CharField(max_length=50)
	sm_transaction_id = models.CharField(max_length=45)
	bank_transaction_id = models.CharField(max_length=45)
	total_amount = models.FloatField()
	charges = models.FloatField()
	service_tax = models.FloatField()
	net_amount = models.FloatField()
	transaction_date = models.DateTimeField()
	src_itc_user_id = models.CharField(max_length=50)
	src_itc_user_name = models.CharField(max_length=50)
	src_itc_mobile = PhoneNumberField()
	uploaded_by = models.CharField(max_length=50)
	uploaded_on_datetime = models.DateTimeField()
	payment_file_name = models.CharField(max_length=50)
	payment_report_date = models.DateTimeField(blank=True, null=True)
	status = models.CharField(max_length=30, blank=True, null=True)
	missing_in_application_center = models.BooleanField()
	accepted_rejected_datetime = models.DateTimeField(blank=True, null=True)
	accepted_rejected_by = models.CharField(max_length=50, blank=True, null=True)

	def __unicode__(self):
		return unicode('{0}'.format(self.tpsl_transaction_id))

class ManualPaymentDataUploadArchived(models.Model):
	
	table_name = 'ManualPaymentDataUpload'
	run = models.IntegerField()
	application = models.ForeignKey(StudentCandidateApplicationArchived,
		related_name='%(class)s_8', blank=True, null=True)
	application_pk = models.CharField(max_length=20, blank=True, null=True)
	payment_id = models.CharField(max_length=45, blank=True, null=True)
	payment_type = models.CharField(max_length=20, blank=True, null=True)
	payment_date = models.DateTimeField()
	payment_amount = models.FloatField()
	payment_mode = models.CharField(max_length=30, blank=True, null=True)
	uploaded_by = models.CharField(max_length=50)
	uploaded_on_date = models.DateTimeField()
	payment_reversal_flag = models.BooleanField()
	status = models.CharField( max_length=30, blank=True, null=True)
	accepted_rejected_datetime = models.DateTimeField(blank=True, null=True)
	accepted_rejected_by = models.CharField(max_length=50, blank=True, null=True)
	upload_filename = models.CharField(max_length=100)

	def __unicode__(self):
		return unicode('{0}'.format(self.payment_id))

class AdhocZestEmiTransactionArchived(models.Model):
	table_name = 'AdhocZestEmiTransaction'
	run = models.IntegerField()
	email = models.EmailField(blank=True, null=True)
	order_id = models.TextField(blank=True, null=True)
	customer_id = models.TextField(blank=True, null=True)
	requested_on = models.DateTimeField(blank=True, null=True)
	is_application_complete = models.BooleanField()
	approved_or_rejected_on = models.DateTimeField(blank=True, null=True)
	is_approved = models.BooleanField()
	is_terms_and_condition_accepted = models.BooleanField()
	req_json_data = jsonfield.JSONField(blank=True, null=True)
	amount_requested = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
	amount_approved = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
	status = models.CharField(max_length=50, blank=True, null=True)
	zest_emi_link = models.TextField(null=True, blank=True)

	def __unicode__(self):
		"""Return unicode."""
		return unicode(self.customer_id)

class AdhocMetaEmiArchived(models.Model):
	table_name = 'AdhocMetaEmi'
	run = models.IntegerField()
	email = models.CharField(max_length=50)
	errors = jsonfield.JSONField(blank=True, null=True)
	created_on_datetime = models.DateTimeField()

	def __unicode__(self):
		"""Return unicode."""
		return unicode(self.created_on_datetime)	

class SemZestEmiTransactionArchived(models.Model):
	table_name = 'SemZestEmiTransaction'
	run = models.IntegerField()
	student_id = models.CharField(max_length=50,blank=True, null=True)
	order_id = models.TextField(blank=True, null=True)
	customer_id = models.TextField(blank=True, null=True)
	requested_on = models.DateTimeField(blank=True, null=True)
	is_application_complete = models.BooleanField()
	approved_or_rejected_on = models.DateTimeField(blank=True, null=True)
	is_approved = models.BooleanField()
	is_terms_and_condition_accepted = models.BooleanField()
	req_json_data = jsonfield.JSONField(blank=True, null=True)
	amount_requested = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
	amount_approved = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
	status = models.CharField(max_length=50, blank=True, null=True)

	def __unicode__(self):
		"""Return unicode."""
		return unicode(self.customer_id)

class SemMetaZestArchived(models.Model):
	table_name = 'SemMetaZest'
	run = models.IntegerField()
	student_id = models.CharField(max_length=50)
	errors = jsonfield.JSONField(blank=True, null=True)
	created_on_datetime = models.DateTimeField()

	def __unicode__(self):
		"""Return unicode."""
		return unicode(self.created_on_datetime)

class MetaApi(models.Model):
	user = models.ForeignKey(User)
	created_on_datetime = models.DateTimeField(auto_now_add=True, blank=True)
	api_request =  jsonfield.JSONField(blank=True, null=True)
	api_response =  jsonfield.JSONField(blank=True, null=True)

	def __unicode__(self):
		return unicode(self.created_on_datetime)

class EduvanzApplicationArchived(models.Model):
	table_name = 'EduvanzApplication'
	run = models.IntegerField()
	application = models.ForeignKey(StudentCandidateApplicationArchived,
		related_name='%(class)s_9',blank=True, null=True)
	order_id = models.CharField(max_length=100, blank=True, null=True)
	is_approved = models.BooleanField(default=False)
	is_terms_and_condition_accepted = models.BooleanField(default=False)
	amount_requested = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
	amount_approved = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
	status_code = models.CharField(max_length=25, blank=True, null=True)
	created_on = models.DateTimeField(blank=True, null=True)
	updated_on = models.DateTimeField(blank=True, null=True) 
	approved_or_rejected_on = models.DateTimeField(blank=True, null=True)
	lead_id = models.CharField(max_length=25, blank=True, null=True)
	callback_meta = jsonfield.JSONField(blank=True, null=True)


	def __unicode__(self):
		"""Return unicode."""
		return unicode(self.order_id)

class SaleForceLogCleanup(models.Model):
	
	logdel_start_datetime = models.DateTimeField(blank=True, null=True)
	logdel_end_datetime = models.DateTimeField(blank=True, null=True)
	sf_lead_rows_deleted = models.PositiveIntegerField()
	sf_document_rows_deleted = models.PositiveIntegerField()
	sf_qualification_rows_deleted = models.PositiveIntegerField()
	sf_workexp_rows_deleted = models.PositiveIntegerField()
	
	def __unicode__(self):
		"""Return unicode."""
		return unicode(self.id)