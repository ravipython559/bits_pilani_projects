from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from registrations.models import *
from datetime import date as DATE
import socket
import cPickle
from django.utils import timezone
from django.utils.timezone import make_aware
import pytz
from datetime import datetime, timedelta

class SFSerializer(serializers.ModelSerializer):
	def __init__(self, *args, **kwargs):
		self.sf_fields = kwargs.pop('sf_fields', None)
		super(SFSerializer, self).__init__(*args, **kwargs)
		
	def get_field_names(self, declared_fields, info):
		if self.sf_fields and not isinstance(self.sf_fields, (list, tuple, set)):
			raise TypeError(
			    'The `fields` option must be a list or tuple or "__all__". '
			    'Got %s.' % type(self.sf_fields).__name__
			)
		if self.sf_fields:
			fields = set(self.sf_fields)
			fields.add('attributes')
			return fields

		return super(SFSerializer, self).get_field_names(declared_fields, info)

class UserSerializer(SFSerializer):
	attributes = serializers.SerializerMethodField()
	Email = serializers.ReadOnlyField(source='email')
	LastName = serializers.ReadOnlyField(source='email')
	Application_Status__c = serializers.SerializerMethodField()
	Bitsuser_program_code__c= serializers.SerializerMethodField()
	Utm_source_first__c= serializers.SerializerMethodField()
	Utm_medium_first__c= serializers.SerializerMethodField()
	Utm_campaign_first__c= serializers.SerializerMethodField()
	Utm_source_last__c= serializers.SerializerMethodField()
	Utm_medium_last__c= serializers.SerializerMethodField()
	Utm_campaign_last__c= serializers.SerializerMethodField()
	
	def get_Reference_Key__c(self, obj):
		return '%s_%s' %(str(obj.username), socket.gethostname())

	def get_attributes(self, obj):
		return {
			'type': 'contact',
			'referenceId': self.get_Reference_Key__c(obj)
		}
	def get_Application_Status__c(self,obj):
		return 'Registered'

	def get_Bitsuser_program_code__c(self,obj):
		bits_user_object = BitsUser.objects.filter(user=obj.id).first()
		if bits_user_object.register_program_id:
			return bits_user_object.register_program_id.program_code
		else:
			return ''

	def get_Utm_source_first__c(self,obj):
		bits_user_object = BitsUser.objects.filter(user=obj.id).first()
		if bits_user_object.utm_source_first:
			return bits_user_object.utm_source_first
		else:
			return ''

	def get_Utm_medium_first__c(self,obj):
		bits_user_object = BitsUser.objects.filter(user=obj.id).first()
		if bits_user_object.utm_medium_first:
			return bits_user_object.utm_medium_first
		else:
			return ''

	def get_Utm_campaign_first__c(self,obj):
		bits_user_object = BitsUser.objects.filter(user=obj.id).first()
		if bits_user_object.utm_campaign_first:
			return bits_user_object.utm_campaign_first
		else:
			return ''

	def get_Utm_source_last__c(self,obj):
		bits_user_object = BitsUser.objects.filter(user=obj.id).first()
		if bits_user_object.utm_source_last:
			return bits_user_object.utm_source_last
		else:
			return ''

	def get_Utm_medium_last__c(self,obj):
		bits_user_object = BitsUser.objects.filter(user=obj.id).first()
		if bits_user_object.utm_medium_last:
			return bits_user_object.utm_medium_last
		else:
			return ''

	def get_Utm_campaign_last__c(self,obj):
		bits_user_object = BitsUser.objects.filter(user=obj.id).first()
		if bits_user_object.utm_campaign_last:
			return bits_user_object.utm_campaign_last
		else:
			return ''
	
	class Meta:
		model = User
		fields = ('attributes', 'Email', 'LastName','Application_Status__c','Bitsuser_program_code__c',
				  'Utm_source_first__c', 'Utm_medium_first__c', 'Utm_campaign_first__c',
				  'Utm_source_last__c', 'Utm_medium_last__c', 'Utm_campaign_last__c')

class SpecificAdmissionSummarySerializer(SFSerializer):
	attributes = serializers.SerializerMethodField()
	Program_Code__c = serializers.SerializerMethodField()
	Program_Name__c = serializers.SerializerMethodField()
	Admission_Count__c = serializers.SerializerMethodField()
	Admit_Batch__c = serializers.SerializerMethodField()
	Admit_Sem_Cohort__c = serializers.SerializerMethodField()
	Application_Count__c = serializers.SerializerMethodField()
	Full_Submission_Count__c = serializers.SerializerMethodField()
	Offered_Count__c = serializers.SerializerMethodField()
	Reject_Count__c = serializers.SerializerMethodField()
	Specific_Program_Id__c = serializers.SerializerMethodField()

	def get_Reference_Key__c(self, obj):
		return '%s_%s' % (obj.program_code+'-'+obj.admit_batch+'-'+str(obj.admit_sem_cohort), socket.gethostname())

	def get_attributes(self, obj):
		return {
			'type': 'B2B_Admission_Details__c',
			'referenceId': self.get_Reference_Key__c(obj)
		}

	def get_Program_Code__c(self, obj):
		return obj.specific_program_id.program_code

	def get_Program_Name__c (self, obj):
		return obj.specific_program_id.program_name

	def get_Admission_Count__c(self, obj):
		return obj.admission_count

	def get_Admit_Batch__c(self, obj):
		return obj.admit_batch

	def get_Admit_Sem_Cohort__c(self, obj):
		return obj.admit_sem_cohort

	def get_Application_Count__c(self, obj):
		return obj.application_count

	def get_Full_Submission_Count__c(self, obj):
		return obj.full_submission_count

	def get_Offered_Count__c (self, obj):
		return obj.offered_count

	def get_Reject_Count__c(self, obj):
		return obj.reject_count

	def get_Specific_Program_Id__c (self, obj):
		return obj.specific_program_id.id


	class Meta:
		model = SpecificAdmissionSummary
		fields = ('attributes','Program_Code__c','Program_Name__c','Admission_Count__c','Admit_Batch__c',
				  'Admit_Sem_Cohort__c', 'Application_Count__c', 'Full_Submission_Count__c',
				  'Offered_Count__c', 'Reject_Count__c', 'Specific_Program_Id__c')

class StudentCandidateApplicationSerializer(SFSerializer):
	Gender__c = serializers.ReadOnlyField(source='get_gender_display')
	Email = serializers.ReadOnlyField(source='login_email.email')
	Birthdate = serializers.ReadOnlyField(source='date_of_birth')
	LastName = serializers.ReadOnlyField(source='full_name')
	Exam_Location__c = serializers.ReadOnlyField(source='current_location.location_name')
	Program__c = serializers.SerializerMethodField()
	MailingPostalCode = serializers.ReadOnlyField(source='pin_code')
	MailingCity = serializers.ReadOnlyField(source='city')
	MailingState = serializers.ReadOnlyField(source='get_state_display')
	Application_ID__c = serializers.ReadOnlyField(source='student_application_id')
	Application_Status__c = serializers.ReadOnlyField(source='application_status')
	Submitted_Date_time__c = serializers.ReadOnlyField(source='created_on_datetime')
	Current_Employment_Status__c = serializers.ReadOnlyField(source='get_current_employment_status_display')
	Current_Designation__c = serializers.ReadOnlyField(source='current_designation')
	Current_Organization__c = serializers.ReadOnlyField(source='current_organization')
	Date_of_Joining_Current_Organization__c = serializers.ReadOnlyField(source='current_org_employment_date')
	Current_Industry__c = serializers.ReadOnlyField(source='current_org_industry.industry_name')
	Work_Location__c = serializers.ReadOnlyField(source='work_location.location_name')
	Prior_Student__c = serializers.SerializerMethodField()
	Admit_Batch__c = serializers.ReadOnlyField(source='admit_batch')
	Lecture_Mode__c = serializers.ReadOnlyField(source='teaching_mode')
	Coding_Proficiency__c = serializers.ReadOnlyField(source='programming_flag')
	Pre_Selection_Date_Time__c = serializers.ReadOnlyField(source='pre_selected_rejected_on_datetime')
	Mentor_Consent__c = serializers.ReadOnlyField(source='employer_mentor_flag')
	Organization_Consent__c = serializers.ReadOnlyField(source='employer_consent_flag')
	Bonafide__c = serializers.ReadOnlyField(source='bonafide_flag')
	Father_Name__c = serializers.ReadOnlyField(source='fathers_name')
	Mother_Name__c = serializers.ReadOnlyField(source='mothers_name')
	Prior_Student_ID__c = serializers.ReadOnlyField(source='bits_student_id')
	attributes = serializers.SerializerMethodField()
	Total_Work_Experience__c = serializers.SerializerMethodField()
	Phone = serializers.ReadOnlyField(source='phone.as_e164')
	MailingCountry = serializers.ReadOnlyField(source='country.name')
	Nationality__c = serializers.ReadOnlyField(source='get_nationality_display')
	Math_Proficiency_Level__c = serializers.ReadOnlyField(source='get_math_proficiency_level_display')
	MobilePhone = serializers.ReadOnlyField(source='mobile.as_e164')

	def get_Total_Work_Experience__c(self, obj):
	
		if obj.program.program_type == 'certification':
			return obj.total_work_experience_in_months

		exp = StudentCandidateWorkExperience.objects.filter(application=obj)
		tmp = obj.last_updated_on_datetime.date() - obj.current_org_employment_date
		for x in exp.iterator():
			tmp += x.end_date - x.start_date
		d = DATE.fromordinal(tmp.days)
		return d.month + 12 * d.year
	
	def get_Reference_Key__c(self, obj):
		return '%s_%s' %(obj.login_email.username, socket.gethostname()) 

	def get_Prior_Student__c(self,obj):
		if obj.prior_student_flag == '1':
			return True
		else:
			return False

	def get_Program__c(self, obj):
		return obj.program.program_code + ',' + obj.program.program_name

	def get_attributes(self, obj):
		return {
			'type': 'contact',
			'referenceId': self.get_Reference_Key__c(obj)
		}

	class Meta:
		model = StudentCandidateApplication
		fields = (
			'Email', 'LastName', 'Gender__c', 'attributes', 'Exam_Location__c', 'Program__c', 'MailingPostalCode',
			'Phone', 'MobilePhone', 'MailingCity', 'MailingState', 'MailingCountry', 'Nationality__c',
			'Application_ID__c', 'Application_Status__c', 'Submitted_Date_time__c', 
			'Current_Employment_Status__c', 'Current_Designation__c', 'Current_Organization__c',
			'Current_Industry__c', 'Work_Location__c', 'Total_Work_Experience__c',
			'Math_Proficiency_Level__c', 'Prior_Student__c', 'Admit_Batch__c', 'Lecture_Mode__c',
			'Coding_Proficiency__c', 'Pre_Selection_Date_Time__c', 'Mentor_Consent__c',
			'Organization_Consent__c', 'Bonafide__c', 'Father_Name__c', 'Mother_Name__c',
			'Prior_Student_ID__c', 'Birthdate', 'Date_of_Joining_Current_Organization__c',
		)

class ApplicantExceptionsSeializer(SFSerializer):
	Email = serializers.ReadOnlyField(source='application.login_email.email')
	LastName = serializers.ReadOnlyField(source='application.full_name')
	Application_ID__c = serializers.ReadOnlyField(source='application.student_application_id')
	Transfer_Program_Name__c = serializers.ReadOnlyField(source='transfer_program.program_code')
	Transfer_On__c = serializers.ReadOnlyField(source='created_on_datetime')
	attributes = serializers.SerializerMethodField()

	def get_Reference_Key__c(self, obj):
		return '%s_%s' %(obj.application.login_email.username, socket.gethostname())

	def get_attributes(self, obj):
		return {
			'type': 'contact',
			'referenceId': self.get_Reference_Key__c(obj)
		}

	class Meta:
		model = ApplicantExceptions
		fields = ('Email', 'LastName', 'Transfer_Program_Name__c',
			'Transfer_On__c', 'attributes', 'Application_ID__c',)

class ApplicationPaymentSeializer(SFSerializer):
	Email = serializers.ReadOnlyField(source='application.login_email.email')
	LastName = serializers.ReadOnlyField(source='application.full_name')
	Fee_Payment_Mode__c = serializers.SerializerMethodField()
	Application_ID__c = serializers.ReadOnlyField(source='application.student_application_id')
	attributes = serializers.SerializerMethodField()

	Fee_Amount__c = serializers.ReadOnlyField(source='payment_amount')
	Application_Fee_Amount__c = serializers.ReadOnlyField(source='payment_amount')

	Admission_Fee_Payment_Date__c = serializers.SerializerMethodField()
	Fee_Paid_Date_Time__c = serializers.SerializerMethodField()
	Application_Fee_Paid_Date_Time__c = serializers.SerializerMethodField()

	def get_Fee_Payment_Mode__c(self, obj):
		if obj.payment_bank.isdigit():
			return 'Tech Process'
		else:
			return obj.payment_bank

	def get_Admission_Fee_Payment_Date__c(self,obj):
		try:
			tt1 = timezone.localtime(obj.payment_date)
			tt1 = tt1.astimezone(pytz.timezone('Asia/Kolkata'))
			tt1 = tt1 - timedelta(hours=5, minutes=30)
			tt = tt1.strftime('%Y-%m-%dT%H:%M:%SZ')
		except ValueError:
			tt1 = make_aware(obj.payment_date)
			tt1 = tt1.astimezone(pytz.timezone('Asia/Kolkata'))
			tt1 = tt1 - timedelta(hours=5, minutes=30)
			tt = tt1.strftime('%Y-%m-%dT%H:%M:%SZ')
		return tt

	def get_Fee_Paid_Date_Time__c(self,obj):
		try:
			tt1 = timezone.localtime(obj.payment_date)
			tt1 = tt1.astimezone(pytz.timezone('Asia/Kolkata'))
			tt1 = tt1 - timedelta(hours=5, minutes=30)
			tt = tt1.strftime('%Y-%m-%dT%H:%M:%SZ')
		except ValueError:
			tt1 = make_aware(obj.payment_date)
			tt1 = tt1.astimezone(pytz.timezone('Asia/Kolkata'))
			tt1 = tt1 - timedelta(hours=5, minutes=30)
			tt = tt1.strftime('%Y-%m-%dT%H:%M:%SZ')
		return tt

	def get_Application_Fee_Paid_Date_Time__c(self,obj):
		try:
			tt1 = timezone.localtime(obj.payment_date)
			tt1 = tt1.astimezone(pytz.timezone('Asia/Kolkata'))
			tt1 = tt1 - timedelta(hours=5, minutes=30)
			tt = tt1.strftime('%Y-%m-%dT%H:%M:%SZ')
		except ValueError:
			tt1 = make_aware(obj.payment_date)
			tt1 = tt1.astimezone(pytz.timezone('Asia/Kolkata'))
			tt1 = tt1 - timedelta(hours=5, minutes=30)
			tt = tt1.strftime('%Y-%m-%dT%H:%M:%SZ')
		return tt

	def get_Reference_Key__c(self, obj):
		return '%s_%s' %(obj.application.login_email.username, socket.gethostname())

	def get_attributes(self, obj):
		return {
			'type': 'contact',
			'referenceId': self.get_Reference_Key__c(obj)
		}

	class Meta:
		model = ApplicationPayment
		fields = ('Email', 'LastName', 'Fee_Amount__c', 'Fee_Paid_Date_Time__c', 
			'Admission_Fee_Payment_Date__c', 'Fee_Payment_Mode__c', 'Application_Fee_Paid_Date_Time__c',
			'attributes', 'Application_ID__c', 'Application_Fee_Amount__c', )

class CandidateSelectionSerializer(SFSerializer):
	Email = serializers.ReadOnlyField(source='application.login_email.email')
	LastName = serializers.ReadOnlyField(source='application.full_name')
	Escalation_Date_Time__c = serializers.ReadOnlyField(source='es_to_su_rev_dt')
	Escalation_Comments__c = serializers.ReadOnlyField(source='es_com')
	Shortlisted_Date_Time__c = serializers.ReadOnlyField(source='selected_rejected_on')
	# Rejection_Date_Time__c = serializers.ReadOnlyField(source='app_rej_by_su_rev_dt')
	Rejection_Comments__c = serializers.ReadOnlyField(source='selection_rejection_comments')
	# Rejection_Mail_Sent_Date_Time__c = serializers.ReadOnlyField(source='offer_reject_mail_sent')
	Shortlisted_Mail_Sent_Date_Time__c = serializers.ReadOnlyField(source='offer_reject_mail_sent')
	Rejection_Reason__c = serializers.SerializerMethodField()
	Acceptance_Declination_Date_Time__c = serializers.ReadOnlyField(source='accepted_rejected_by_candidate')
	Student_ID__c = serializers.ReadOnlyField(source='student_id')
	Decline_Reason__c = serializers.SerializerMethodField()
	Lecture_Start_Date__c = serializers.ReadOnlyField(source='lecture_start_dt')
	Orientation_Date__c = serializers.ReadOnlyField(source='orientation_dt')
	New_application_ID__c = serializers.ReadOnlyField(source='new_application_id')
	Application_ID__c = serializers.ReadOnlyField(source='application.student_application_id')
	attributes = serializers.SerializerMethodField()
	# Application_Status__c = serializers.ReadOnlyField(source='application.application_status')
	Fee_Payment_DeadLine_Date__c = serializers.ReadOnlyField(source='fee_payment_deadline_dt')
	Transfer_Program_Name__c = serializers.SerializerMethodField()
	Transfer_On__c = serializers.SerializerMethodField()

	def get_Rejection_Reason__c(self, obj):
		try:
			bits_rej_reason = ', '.join(cPickle.loads(str(obj.bits_rejection_reason)) or [] )
		except cPickle.UnpicklingError: bits_rej_reason = ''
		return bits_rej_reason

	def get_Reference_Key__c(self, obj):
		return '%s_%s' %(obj.application.login_email.username, socket.gethostname())

	def get_Decline_Reason__c(self,obj):
		return '%s comment-%s' % (getattr(obj.rejection_by_candidate_reason, 'reason', '-'), obj.rejection_by_candidate_comments)

	def get_Transfer_Program_Name__c(self,obj):
		return '%s  %s' % (getattr(obj.new_sel_prog, 'program_code', ' '), getattr(obj.new_sel_prog, 'program_name', ' '))

	def get_Transfer_On__c(self,obj):
		if obj.new_application_id:
			return obj.app_rej_by_su_rev_dt

	def get_attributes(self, obj):
		return {
			'type': 'contact',
			'referenceId': self.get_Reference_Key__c(obj)
		}

	class Meta:
		model = CandidateSelection
		fields = ('Email', 'LastName', 'Escalation_Date_Time__c', 'Escalation_Comments__c', 
			'Shortlisted_Date_Time__c', 'Rejection_Comments__c','Shortlisted_Mail_Sent_Date_Time__c',
			'Rejection_Reason__c', 'Acceptance_Declination_Date_Time__c', 'Student_ID__c',
			'Decline_Reason__c', 'Lecture_Start_Date__c', 'Orientation_Date__c',
			'New_application_ID__c', 'attributes','Application_ID__c','Fee_Payment_DeadLine_Date__c',
			'Transfer_Program_Name__c','Transfer_On__c',)


class StudentCandidateQualificationSeializer(SFSerializer):
	attributes = serializers.SerializerMethodField()
	Degree__c = serializers.ReadOnlyField(source='degree.degree_short_name')
	Discipline__c = serializers.ReadOnlyField(source='discipline.discipline_name')
	College_School__c = serializers.ReadOnlyField(source='school_college')
	Grade_CGPA__c = serializers.ReadOnlyField(source='percentage_marks_cgpa')
	Application_Id__c = serializers.ReadOnlyField(source='application.student_application_id')
	Reference_Key__c = serializers.SerializerMethodField()
	Completion_Year__c =  serializers.ReadOnlyField(source='completion_year')

	def get_Reference_Key__c(self, obj):
		return '%s_edu_%s_%s' % (obj.application.student_application_id, obj.pk, socket.gethostname())

	def get_attributes(self, obj):
		return {
            'type': 'Education__c',
            'referenceId': self.get_Reference_Key__c(obj)
        }
	
	class Meta:
		model = StudentCandidateQualification
		fields = ('attributes', 'Degree__c', 'Discipline__c', 'College_School__c', 
			'Grade_CGPA__c', 'Application_Id__c', 'Reference_Key__c','Completion_Year__c',
		)

class StudentCandidateWorkExpierenceSerializer(SFSerializer):
	attributes = serializers.SerializerMethodField()
	Organization__c = serializers.ReadOnlyField(source = 'organization')
	Designation__c = serializers.ReadOnlyField(source = 'designations')
	From__c = serializers.ReadOnlyField(source = 'start_date')
	To__c = serializers.ReadOnlyField(source = 'end_date')
	Application_Id__c = serializers.ReadOnlyField(source = 'application.student_application_id')
	Reference_Key__c = serializers.SerializerMethodField()

	def get_Reference_Key__c(self, obj):
		return '%s_exp_%s_%s' % (obj.application.student_application_id, obj.pk, socket.gethostname())

	def get_attributes(self, obj):
		return {
		'type': 'Experience__c',
		'referenceId': self.get_Reference_Key__c(obj)
		}

	class Meta:
		model = StudentCandidateWorkExperience
		fields = ('attributes', 'Organization__c', 'Designation__c', 'From__c', 
		'To__c', 'Application_Id__c', 'Reference_Key__c',
		) 

class ApplicationDocumentSerializer(SFSerializer):
	attributes = serializers.SerializerMethodField()
	Name = serializers.ReadOnlyField(source='document.document_name')
	Uploaded_on__c = serializers.ReadOnlyField(source='last_uploaded_on')
	Document_Status__c = serializers.SerializerMethodField()
	Review_Datetime__c = serializers.ReadOnlyField(source='inspected_on')
	Application_Id__c = serializers.ReadOnlyField(source='application.student_application_id')
	Reference_Key__c = serializers.SerializerMethodField()
	Rejection_Reason__c = serializers.ReadOnlyField(source='rejection_reason.reason')


	def get_Reference_Key__c(self, obj):
		return '%s_doc_%s_%s' % (obj.application.student_application_id, obj.document.document_name, socket.gethostname())

	def get_attributes(self, obj):

		return {
            'type': 'Document__c',
            'referenceId': self.get_Reference_Key__c(obj)
        }
	
	def get_Document_Status__c(self,obj):
		if obj.accepted_verified_by_bits_flag:
			return 'Accepted'
		elif obj.rejected_by_bits_flag:
			return 'Rejected'
		elif obj.reload_flag and not obj.rejected_by_bits_flag:
			return 'Review Pending'
		elif obj.reload_flag:
			return 'Resubmission Required'
		else:
			return 'Review Pending'

	class Meta:
		model = ApplicationDocument
		fields = ('attributes', 'Name', 'Uploaded_on__c', 'Document_Status__c', 
				'Review_Datetime__c', 'Application_Id__c', 'Reference_Key__c',
				'Rejection_Reason__c',
			)


