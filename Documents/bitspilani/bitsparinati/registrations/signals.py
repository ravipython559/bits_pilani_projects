from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.db import IntegrityError, transaction
from django.dispatch import receiver
from django.conf import settings as S
from bits import settings
from django.db.models import Q
from .saleforce import serializers as sf_serializers
from .saleforce.utils import saleforce_async_api as sf_api
from registrations.models import (ApplicationDocument as AD, CandidateSelection as CS,
	ProgramDocumentMap as PDM, StudentCandidateApplication as SCA,
	ApplicantExceptions as AE, ApplicationPayment as AP, ADMISSION_FEE, APPLICATION_FEE,
	StudentCandidateQualification as SCQ, StudentCandidateWorkExperience as SCWE, BitsUser, SpecificAdmissionSummary)
from registrations.models import ( SaleForceLeadDataLog, SaleForceQualificationDataLog,
			SaleForceWorkExperienceDataLog, SaleForceDocumentDataLog, SpecificAdmissionDataLog)

from bits_rest.models import InBoundCall, InBoundPhone, OutBoundCall, OutBoundPhone
from django.utils import timezone
import datetime


sca_queryset = lambda program: SCA.objects.filter(
	program=program,
	).exclude(
	application_status__in=[
		S.APP_STATUS[12][0],
		S.APP_STATUS[13][0],
		S.APP_STATUS[14][0]
		],
	)

@receiver(post_save, sender=PDM)
def save_user_profile(sender, instance, **kwargs):
	if instance.mandatory_flag or instance.deffered_submission_flag:
		for app in sca_queryset(instance.program).iterator():
			AD.objects.update_or_create(application=app,
				document=instance.document_type,
				defaults={'program_document_map':instance}
			)

@receiver(post_save, sender=InBoundCall)
def save_inbound_profile(sender, instance, **kwargs):
	sca = SCA.objects.filter(login_email__email=instance.cust_email)
	instance.application.clear()
	instance.application.set(sca)

@receiver(post_save, sender=InBoundPhone)
def save_inboundphone_profile(sender, instance, **kwargs):
	sca = SCA.objects.filter(Q(phone=instance.phone)|Q(mobile=instance.phone))
	instance.bound.application.add(*[x for x in sca.iterator()])

@receiver(post_save, sender=OutBoundCall)
def save_outbound_profile(sender, instance, **kwargs):
	sca = SCA.objects.filter(login_email__email=instance.cust_email)
	instance.application.clear()
	instance.application.set(sca)

@receiver(post_save, sender=OutBoundPhone)
def save_outboundphone_profile(sender, instance, **kwargs):
	sca = SCA.objects.filter(Q(phone=instance.phone)|Q(mobile=instance.phone))
	instance.bound.application.add(*[x for x in sca.iterator()])

@receiver(post_save, sender=SCA)
def save_sca_profile(sender, instance, created, **kwargs):
	instance.inboundcall_set.clear()
	instance.outboundcall_set.clear()

	inboundcall = InBoundCall.objects.filter(cust_email=instance.login_email.email)
	inbound_phone = InBoundPhone.objects.filter(Q(phone=instance.mobile)|Q(phone=instance.phone))
	instance.inboundcall_set.set([ x.bound for x in inbound_phone.iterator()] + list(inboundcall))

	outboundcall = OutBoundCall.objects.filter(cust_email=instance.login_email.email)
	outbound_phone = OutBoundPhone.objects.filter(Q(phone=instance.mobile)|Q(phone=instance.phone))
	instance.outboundcall_set.set([ x.bound for x in outbound_phone.iterator()] + list(outboundcall))

	if instance.student_application_id and instance.program.program_type != 'specific':
		transaction.on_commit(lambda: sf_api('contact', instance,
				sf_serializers.StudentCandidateApplicationSerializer, SaleForceLeadDataLog,
				{'user': instance.login_email}
			)
		)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, created, **kwargs):
	if created:
		if instance._program == None:
			transaction.on_commit(lambda: sf_api('contact', instance,
												 sf_serializers.UserSerializer, SaleForceLeadDataLog, {'user': instance}
												 )
								  )
		else:
			if instance._program.program_type != 'specific':
				transaction.on_commit(lambda: sf_api('contact', instance,
						sf_serializers.UserSerializer, SaleForceLeadDataLog, {'user': instance}
					)
				)

@receiver(post_save, sender=BitsUser)
def save_bitsuser_profile(sender, instance, created, **kwargs):
	user_object = User.objects.get(id=instance.user_id)
	if user_object.last_login:
		if instance.register_program_id == None:
			if instance.utm_source_last != instance.utm_source_last_current or instance.utm_medium_last != instance.utm_medium_last_current or instance.utm_campaign_last != instance.utm_campaign_last_current:
				instance = User.objects.get(id=instance.user_id)
				transaction.on_commit(lambda: sf_api('contact', instance,
													 sf_serializers.UserSerializer, SaleForceLeadDataLog,
													 {'user': instance}
													 )
									  )
		else:
			if instance.register_program_id.program_type != 'specific':
				if instance.utm_source_last != instance.utm_source_last_current or instance.utm_medium_last != instance.utm_medium_last_current or instance.utm_campaign_last != instance.utm_campaign_last_current:
					instance = User.objects.get(id=instance.user_id)
					transaction.on_commit(lambda: sf_api('contact', instance,
							sf_serializers.UserSerializer, SaleForceLeadDataLog, {'user': instance}
						)
					)

@receiver(post_save, sender=SpecificAdmissionSummary)
def save_user_profile1(sender, instance, created, **kwargs):
	transaction.on_commit(lambda: sf_api('B2B_Admission_Details__c', instance,
			sf_serializers.SpecificAdmissionSummarySerializer, SpecificAdmissionDataLog, {'specificadmission': instance}
		)
	)

@receiver(post_save, sender=CS)
def save_cs_profile(sender, instance, created, **kwargs):
    dps_datetime = instance.dps_datetime
    mins_before_datetime = timezone.localtime(timezone.now()) - datetime.timedelta(minutes = 15)
    if instance.application.program.program_type != 'specific':
		if dps_datetime:
			if timezone.localtime(dps_datetime) < mins_before_datetime:
				if instance.application.application_status != settings.APP_STATUS[12][0]:
					if instance.application.application_status != settings.APP_STATUS[11][0]:
						transaction.on_commit(lambda: sf_api('contact', instance,
								sf_serializers.CandidateSelectionSerializer, SaleForceLeadDataLog,
								{'user': instance.application.login_email}
							)
						)
					elif instance.application.application_status == settings.APP_STATUS[11][0] and instance.student_id:
						transaction.on_commit(lambda: sf_api('contact', instance,
								sf_serializers.CandidateSelectionSerializer, SaleForceLeadDataLog,
								{'user': instance.application.login_email}
							)
						)
		else:
			if instance.application.application_status != settings.APP_STATUS[12][0]:
				if instance.application.application_status != settings.APP_STATUS[11][0]:
					transaction.on_commit(lambda: sf_api('contact', instance,
							sf_serializers.CandidateSelectionSerializer, SaleForceLeadDataLog,
							{'user': instance.application.login_email}
						)
					)
				elif instance.application.application_status == settings.APP_STATUS[11][0] and instance.student_id:
					transaction.on_commit(lambda: sf_api('contact', instance,
							sf_serializers.CandidateSelectionSerializer, SaleForceLeadDataLog,
							{'user': instance.application.login_email}
						)
					)

@receiver(post_save, sender=AE)
def save_ae_profile(sender, instance, created, **kwargs):
	if instance.application and instance.application.program.program_type != 'specific':
		if instance.application.application_status != settings.APP_STATUS[12][0]:
			transaction.on_commit(lambda: sf_api('contact', instance,
					sf_serializers.ApplicantExceptionsSeializer, SaleForceLeadDataLog,
					{'user': instance.application.login_email}
				)
			)

@receiver(post_save, sender=AP)
def save_ap_profile(sender, instance, created, **kwargs):
	if instance.fee_type == ADMISSION_FEE:
		sf_fields = ('Email', 'LastName',
			'Fee_Amount__c', 'Fee_Paid_Date_Time__c',
			'Admission_Fee_Payment_Date__c', 'Fee_Payment_Mode__c',
			'attributes', 'Application_ID__c', )
	elif instance.fee_type == APPLICATION_FEE:
		sf_fields = ('Email', 'LastName',
			'Fee_Payment_Mode__c',
			'Application_Fee_Paid_Date_Time__c',
			'attributes', 'Application_ID__c', 'Application_Fee_Amount__c', )
	else:
		sf_fields = ('Email', 'LastName', 'Application_ID__c')

	if instance.application.program.program_type != 'specific':
		transaction.on_commit(lambda: sf_api('contact', instance,
				sf_serializers.ApplicationPaymentSeializer, SaleForceLeadDataLog,
				{'user': instance.application.login_email}, serializer_fields=sf_fields,
			)
		)

@receiver(post_save, sender=SCQ)
def save_scq_profile(sender, instance, created, **kwargs):
	if instance.application.program.program_type != 'specific':
		transaction.on_commit(lambda: sf_api('Education__c',
				instance, sf_serializers.StudentCandidateQualificationSeializer,
				SaleForceQualificationDataLog, {'qualification': instance}
			)
		)

@receiver(post_save, sender=SCWE)
def save_scwe_profile(sender, instance, created, **kwargs):
	if instance.application.program.program_type != 'specific':
		transaction.on_commit(lambda: sf_api('Experience__c',
			instance, sf_serializers.StudentCandidateWorkExpierenceSerializer,
			SaleForceWorkExperienceDataLog, {'work_experience': instance}
			)
		)

@receiver(post_save, sender=AD)
def save_AD_profile(sender, instance, created, **kwargs):

	api_call_cond = (
		(instance.file and instance.last_uploaded_on) or
		instance.accepted_verified_by_bits_flag or
		instance.rejected_by_bits_flag or instance.reload_flag
	)

	if api_call_cond and instance.application.program.program_type != 'specific':
		transaction.on_commit(lambda: sf_api('Document__c',
				instance, sf_serializers.ApplicationDocumentSerializer,
				SaleForceDocumentDataLog, {'document': instance},
				seconds=10,
			)
		)

