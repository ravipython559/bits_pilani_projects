"""Django Models for Bits Project."""
from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User, UserManager, AbstractBaseUser
from phonenumber_field.modelfields import PhoneNumberField
from django_countries.fields import CountryField
from ckeditor.fields import RichTextField
from django.core.validators import MaxValueValidator,RegexValidator,MinValueValidator
from django.utils.translation import ugettext_lazy as _
from easy_thumbnails.fields import ThumbnailerImageField
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from bits.bits_storage import MediaStorage
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime as dt
from decimal import Decimal
import jsonfield
import uuid

GENDER_CHOICES = (
	(None,'Choose Gender'),
	('F', 'Female'),
	('M', 'Male'),
)

FEE_TYPE_CHOICE = (
	(None,'FEE TYPE'),
	('1', 'APPLICATION FEE'),
	('2', 'ADMISSION FEE'),
)

EDUVANZ_FEE_TYPE = '6'
ZEST_FEE_TYPE = '5'
ADMISSION_FEE = '1'
APPLICATION_FEE = '2'
EZCRED_FEE_TYPE = '7'
PROPELLD_FEE_TYPE = '8'


FEE_TYPE_CHOICES = (
	(None, 'Choose Fee Type'),
	(ADMISSION_FEE, 'Admission Fee'),
	(APPLICATION_FEE, 'Application Fee'),
	('3', 'REVERSAL-APPLICATION FEE'),
	('4', 'REVERSAL-ADMISSION FEE'),
	(ZEST_FEE_TYPE, 'Zest Loan Amount'),
	(EDUVANZ_FEE_TYPE, 'Eduvanz Loan Amount'),
	(EZCRED_FEE_TYPE, 'Ezcred Loan Amount'),
	(PROPELLD_FEE_TYPE, 'Propelld Loan Amount')

)

DURATION_CHOICES = (
	(None,'Choose Duration'),
	('1', '6 months'),
	('2', '1 year'),
	('3', '1.5 year'),
	('4', '2 year'),
	('5', '2.5 year'),
	('6', '3 year'),
	('7', '3.5 year'),
	('8', '4 year'),
	('9', '> 4 year'),
)

DIVISION_CHOICES = (
	(None,'Choose Division'),
	('1', '1st division'),
	('2', '2nd division'),
	('3', '3rd division'),
	('4', 'NA'),
)

NATIONALITY_CHOICES = (
	(None,'Choose Nationality'),
	('1', 'Indian'),
	('3', 'Non-Indian'),
	('2', 'NRI'),
)

STATE_CHOICES = (
	(None,'Choose State(India)'),
	('1', 'Andhra Pradesh'),
	('35','Andaman and Nicobar Islands'),
	('2', 'Arunachal Pradesh'),
	('3', 'Assam'),
	('4', 'Bihar'),
	('34','Chandigarh'),
	('5', 'Chhattisgarh'),
	('33', 'Dadra and Nagar Haveli'),
	('32', 'Daman and Diu'),
	('31', 'Delhi'),
	('6', 'Goa'),
	('7', 'Gujarat'),
	('8', 'Haryana'),
	('9', 'Himachal Pradesh'),
	('10', 'Jammu and Kashmir'),
	('11', 'Jharkhand'),
	('12', 'Karnataka'),
	('13', 'Kerala'),
	('36', 'Lakshadweep'),
	('14', 'Madhya Pradesh'),
	('15', 'Maharashtra'),
	('16', 'Manipur'),
	('17', 'Meghalaya'),
	('18', 'Mizoram'),
	('19', 'Nagaland'),
	('20', 'Odisha (Orissa)'),
	('30', 'Out Side India'),
	('37', 'Pondicherry'),
	('21', 'Punjab'),
	('22', 'Rajasthan'),
	('23', 'Sikkim'),
	('24', 'Tamil Nadu'),
	('25', 'Telangana'),
	('26', 'Tripura'),
	('27', 'Uttar Pradesh'),
	('28', 'Uttarakhand'),
	('29', 'West Bengal'),
)


EMPLOYMENTSTATUS_CHOICES= (

	(None,'Choose Employment Status'),    
	('1', 'Employed'),    
	('3', 'Self Employed'),
	('2', 'Unemployed'),
	('4', 'Not Applicable'),  
)

FEEPAYMENT_CHOICES= (
	(None,'Choose who will pay the fees'),
	('1', 'Full Fees by Employer'),
	('3', 'Full payment by self'),
	('4', 'Not Applicable'),
	('2', 'Part payment by Employer,part by self'),
)

LEVEL_CHOICES= (
	(None,'Choose Level'),

	('1', 'Till Matriculation(Std. X)'),
	('2', 'Till Intermediate(Std. XII)'),
	('3', 'Graduate Studies (Engg. And Science)'),
	('4', 'Graduate Studies in Maths'),
	('5', 'Post Graduate Studies (Engg. And Science)'),
	('6', 'Post Graduate Studies  in Maths'),
	('7', 'Not Studied'),
)

PRIOR_CHOICES= (
	(None,'Choose'),
	('1', 'YES'),
	('2', 'NO'),
)

APPLICATION_PDF_TEMPLATE_CHOICES = ((None,'Choose'),
	('app_pdf/oracle-pdf.html','Oracle'),
	('app_pdf/wipro-pdf.html','Wipro'),
	('app_pdf/specific-pdf.html','Specific Program Application Template'),
	('app_pdf/hcl_org.html', 'HCL Collaboration - BSc Program'),
	('app_pdf/delloitte1-pdf.html', 'Delloitte Application Form Template-1'),
	('app_pdf/SAP_Application_form2020-21.html', 'SAP Application form 2020-21'),
	('app_pdf/Cluster-Program-template-2020-21.html', 'Cluster Program template 2020-21')
	)

OFFER_LETTER_TEMPLATE_CHOICES =((None,'Choose'),
	('offer_pdf/oracle.html','oracle'),
	('offer_pdf/non-specific-sem2.html','Non Specific 2016 2nd Sem'),
	('offer_pdf/non-specific-sem2-2018-19.html','Non-Specific 2018-19'),
	('offer_pdf/non-specific-2019-2020.html','Non-Specific 2019-20'),
	('offer_pdf/mahindra_vehicles2019_20.html','Offer letter Mahindra Vehicles - 2019-20'),
    ('offer_pdf/Specific-program-template.html','Specific-program template'),
    ('offer_pdf/spc-pgm-2018-19.html','Specific 2018-19'),
	('offer_pdf/wipro.html','Wipro Offer letter'),
	('offer_pdf/wipro_sim.html','Wipro-SIM'),
	('offer_pdf/wipro_wims.html','Wipro-WIMS'),
	('offer_pdf/wipro_wase.html','Wipro-WASE'),
	('offer_pdf/cluster.html','Cluster Offer Letter'),
	('offer_pdf/cluster1.html','Cluster Offer Letter 1'),
	('offer_pdf/cluster_pg_2018.html','Cluster Program Offer Letter - 2018'),
	('offer_pdf/cluster_pg_2018_2019.html','Cluster 2018-19'),
	('offer_pdf/cluster_pg_mtech_dt_sc_2018_19.html','Cluster Offer Letter - MTech Data Science 2018-19'),
	('offer_pdf/bosch_man.html','Bosch Offer Letter Manufacturing'),
	('offer_pdf/bosch_pg_man.html','Bosch Offer Letter PG Diploma Manufacturing'),
	('offer_pdf/mtech_pom_mum_hyd.html','M.Tech POM Offer Letter-Mumbai-Hyd'),
	('offer_pdf/mtech_pom_ahmd.html','M.Tech POM Offer Letter-Ahmedabad'),
	('offer_pdf/embedded_sys_cluster.html','Embedded System Cluster Offer Letter 2017-18 Sem1'),
	('offer_pdf/iot_certificate.html','IOT Certification Offer Letter'),
	('offer_pdf/iot_certificate_cohort_2.html','IOT Certification Offer Letter Cohort - 2'),
	('offer_pdf/iot_certificate_cohort_3.html','CIOT Offer Letter 2018 Cohort 1'),
	('offer_pdf/iot_certificate_revised.html','IOT Offer Letter Revised'),
	('offer_pdf/wipro_wase_2017-18_sem2.html','Wipro-WASE-2017-18-Sem2'),
	('offer_pdf/wipro_wims_2017-18_sem2.html','Wipro-WIMS-2017-18-Sem2'),
	('offer_pdf/wipro_wims_2018-19_sem2.html','Wipro-WIMS-2018-19-Sem2'),
	('offer_pdf/wipro_wims_2019-20_sem2.html','Wipro-WIMS-2019-20-Sem2'),
	('offer_pdf/wipro_wims_2020-21_sem1.html','Wipro-WIMS-2020-21'),
	('offer_pdf/wipro_wase_2020-21_sem1.html','Wipro-WASE-2020-21'),
	('offer_pdf/sap_offer_hs70_2018-1_sem.html','SAP Offer Letter HS70 2018-1 Sem'),
	('offer_pdf/sap_offer_sp93_2018-1_sem.html','SAP Offer Letter SP93 2018-1 Sem'),
	('offer_pdf/vmware_offer_letter.html','VMWare Offer Letter'),
	('offer_pdf/mtech_dt_sc_engg_2018_19.html','Cluster Offer Letter - MTech in Data Science - with readiness exam 2018-19'),
	('offer_pdf/clstr_design_engg_pune_2018_19.html','Cluster Design Engineering Pune 2018-19.html'),
	('offer_pdf/bosch_diploma_manf_2020_21.html','Certificate Programme in Manufacturing Practice for Diploma 2020-21 Bosch'),
	('offer_pdf/bosch_iti.html','Certificate Programme in Manufacturing Practice for ITI 2020-21 Bosch'),
    ('offer_pdf/bosch_pg_manf_2020_21.html','Post Graduate Certificate in Manufacturing Practice 2020-21 Bosch'),
	('offer_pdf/bosch_iti_manf_2018_19.html','Certificate Programme in Manufacturing Practice for ITI-2018-19-Bosch'),
	('offer_pdf/hcl_offer_letter.html','HCL Offer Letter'),
	('offer_pdf/aiml_offer_letter.html','AIML Offer Letter'),
	('offer_pdf/sap_offer_hs70_2019-1_sem.html','SAP Offer Letter HS70 2019-1 Sem'),
	('offer_pdf/sap_offer_sp93_2019-1_sem.html','SAP Offer Letter SP93 2019-1 Sem'),
	('offer_pdf/aiml_offer_letter_2019.html','AIML-2019'),
	('offer_pdf/iot_certificate_cohort_2019.html','CIOT-2019'),
	('offer_pdf/aiml_offer_letter_20192.html','AIML 20192'),
	('offer_pdf/cluster_pg_mtech_dse_2019_20.html', 'Cluster Offer Letter - MTech in Data Science 2019-20'),
	('offer_pdf/nsp_offer_letter_2020_21.html', 'NSP Offer Letter 2020-21'),
	('offer_pdf/hcl_bsc_offer_2020.html', 'HCL BSc Offer letter - 2020'),
	('offer_pdf/sap_offer_2020_21sem.html','SAP Offer letter 2020-21'),
	('offer_pdf/aiml_offer_letter_2020_21-sem1.html','AIML 2020-21 Sem1'),
	('offer_pdf/aiml_offer_letter_2020_21-sem2.html','AIML 2020-21 Sem2'),
	('offer_pdf/ciot_offer_letter_2020_21-sem1.html','CIOT 2020-21 Sem1'),
	('offer_pdf/DSE-Offer-Letter-2020-21.html','DSE Offer Letter 2020-21'),
	('offer_pdf/DSE-OffLet-2-sem-2020-21.html','DSE Offer Letter Second Sem 2020-21'),
	('offer_pdf/PGD_cluster_offer_letter_2020.html', 'PGD cluster Offer Letter 2020-21'),
	('offer_pdf/PGD_cluster_offer_letter_2020_21_sem2.html', 'PGD cluster Offer Letter 2020-21 Sem2'),
    ('offer_pdf/FSE_offer_letter_2020.html', 'FSE Offer Letter 2020'),
	('offer_pdf/nsp_offer_letter_2021_22.html', 'NSP Offer Letter 2021-22'),
	('offer_pdf/offer_letter_comcast_2021.html', 'Offer letter Mahindra Vehicles - 2019-20'),
	('offer_pdf/sap_offer_letter_2021_22.html','SAP Offer letter 2021-22'),
	('offer_pdf/DSE-Offer-Letter-2021-22.html','DSE Offer Letter 2021-22'),
	('offer_pdf/PGD_cluster_offer_letter_2021_22.html','PGD Cluster Offer Letter 2021-22'),
	('offer_pdf/iot_offer_letter_2021_22.html','IOT Offer Letter 2021-22'),
	('offer_pdf/FSE_offer_letter_2021_2022.html','FSE Offer Letter 2021-22'),
	)

PARALLEL_CHOICES= (
	(None,'Choose'),
	('1', 'YES'),
	('2', 'NO'),
)


DOCUMENT_UPLOAD_CHOICES =(
	(None,'Choose Document To Upload'),
	('guidelines_document/oracle.html','Oracle'),
	('guidelines_document/wipro.html','Wipro'),
	('guidelines_document/certification_programs.html', 'Certification Programs'),
	('guidelines_document/hcl_org.html', 'HCL Collaboration'),
	)

PROGRAM_TYPE_CHOICES =(
	(None,'Choose Program Type'),
	('specific','SPECIFIC'),
	('non-specific','NON-SPECIFIC'),
	('cluster','CLUSTER'),
	('others','OTHERS'),
	('certification','CERTIFICATION'),)


def user_directory_path(instance, filename):
	date = timezone.now()
	return 'documents/{0}/{1}/{2}/{3}/{4}/{5}'.format(
		date.year,date.strftime('%B'),date.day,
		instance.application.student_application_id,
		uuid.uuid4(),filename)

def saleforce_directory_path(instance, filename):
	date = timezone.now()
	return 'saleforce/{0}/{1}/{2}/{3}/{4}/{5}'.format(
		date.year,date.strftime('%B'),date.day,
		instance.application.student_application_id,
		uuid.uuid4(),filename)

def document_upload_page_path(instance, filename):
	return 'program_documents/{}/{}'.format(uuid.uuid4(),filename)




class BitsRejectionReason(models.Model): #length of reason max_length
	"""Bits Rejectoin Reason Model."""
	reason = models.CharField(
		max_length=100, unique=True,)

	def __unicode__(self):
		"""Return Unicode Document Name."""
		return self.reason




class ApplicantRejectionReason(models.Model): #alphanumeric 
	"""Applicant Rejection Reason Model."""
	reason = models.CharField(max_length=100, unique=True,)

	def __unicode__(self):
		"""Return Unicode Document Name."""
		return unicode(self.reason)


class ApplicantionDocumentReason(models.Model):  #Application spell
	"Applicant Document Reason."
	reason = models.CharField(
		max_length=100, unique=True,)

	def __unicode__(self):
		"""Return Unicode Document Name."""
		return unicode(self.reason)

	class Meta:
		verbose_name = 'Application Document Rejection Reason'

class DocumentType(models.Model):
	"""Model for Documents Types."""

	document_name = models.CharField(max_length=45,unique=True,)
	mandatory_document = models.BooleanField(default=False)
	n_v_flag = models.BooleanField('use for name verification',default=False)

	def __unicode__(self):
		"""Return Unicode Document Name."""
		return self.document_name

	class Meta:
		"""Order By Mandatory Document."""
		ordering = ['-mandatory_document']


class ApplicationPayment(models.Model):
	"""Model with Applicantion Payment Information."""

	application = models.ForeignKey('StudentCandidateApplication',
									related_name='%(class)s_requests_created_3'
									)  # Field name made lowercase.
	payment_id = models.CharField(max_length=45)  # Field name made lowercase.
	payment_amount = models.CharField(max_length=45)
	payment_date = models.DateTimeField()
	payment_bank = models.CharField(max_length=45)
	transaction_id = models.CharField(max_length=45)
	fee_type = models.CharField(max_length=16, choices=FEE_TYPE_CHOICES)

	tpsl_transaction = models.CharField(max_length=45,blank=True, null=True)
	matched_with_payment_gateway = models.BooleanField(default=False)
	missing_from_gateway_file = models.BooleanField(default=False)
	manual_upload_flag = models.BooleanField(default=False)
	inserted_from_gateway_file = models.BooleanField(default=False)
	insertion_datetime = models.DateTimeField(blank=True, null=True)
	insertion_approved_by = models.CharField(max_length=50, blank=True, null=True)

	def __unicode__(self):
		"""Return unicode Payment Id."""
		return self.payment_id

	class Meta:
		unique_together = ('fee_type', 'application')

class PaytmTransactionStatus(models.Model):
	order_id = models.CharField(max_length=100, primary_key=True)
	application = models.ForeignKey('StudentCandidateApplication',
									related_name='%(class)s_requests_created_713'
									)  # Field name made lowercase.
	email = models.CharField(max_length=100, blank=True, null=True)
	payment_application_id = models.CharField(max_length=100, blank=True, null=True)
	created_on = models.DateTimeField(blank=True, null=True)
	transaction_date = models.DateTimeField(blank=True, null=True)
	request_amount = models.CharField(max_length=100, blank=True, null=True)
	transaction_amount = models.CharField(max_length=100, blank=True, null=True)
	mobile = models.CharField(max_length=30, blank=True, null=True)
	transaction_id = models.CharField(max_length=100, blank=True, null=True)
	bank_transaction_id = models.CharField(max_length=100, blank=True, null=True)
	bank_name = models.CharField(max_length=100, blank=True, null=True)
	payment_mode = models.CharField(max_length=100, blank=True, null=True)
	currency = models.CharField(max_length=100, blank=True, null=True)
	gateway_name = models.CharField(max_length=100, blank=True, null=True)
	merchant_id = models.CharField(max_length=100, blank=True, null=True)
	response_message = models.TextField(max_length=500, blank=True, null=True)
	status = models.CharField(max_length=20, blank=True, null=True)
	resp_json = jsonfield.JSONField(blank=True, null=True)
	fee_type = models.CharField(max_length=16, choices=FEE_TYPE_CHOICES)


class Discpline(models.Model):
	"""Model with Descpline."""

	discipline_name = models.CharField(max_length=40, unique=True,
		validators=[ RegexValidator(regex='^[\w\s_.()]+$',
			message=_('discipline name must be Alphanumeric'),
			code=_('invalid_discipline_name')),
		])

	discipline_long_name = models.CharField(max_length=60,
		validators=[ RegexValidator(regex='^[\w\s_.()]+$',
			message=_('discipline long name must be Alphanumeric'),
			code=_('invalid_discipline_long_name')),
		])

	def __unicode__(self):
		"""Return Unicode Descipline Name."""
		return self.discipline_name

	class Meta:
		"""Order By Descpline Names."""

		ordering = ['discipline_long_name']
		verbose_name = 'Discipline'
		verbose_name_plural = 'Disciplines'





class Industry(models.Model):
	"""Model for Industry Names."""

	industry_name = models.CharField(max_length=45,unique=True,)

	def __unicode__(self):
		"""Return Unicode Industry Name."""
		return self.industry_name

	class Meta:
		"""Order By Industry Names."""

		ordering = ['industry_name']
		verbose_name_plural = 'Industries'


class Location(models.Model):
	location_name = models.CharField(max_length=50,unique=True,)
	is_exam_location = models.BooleanField()  # Field name made lowercase.

	def __unicode__(self):
		return unicode(self.location_name)

	class Meta:
		ordering = ['location_name']

class ZestProgramMap(models.Model):
	merchant_name = models.CharField(max_length=45)
	client_id = models.TextField('Merchant ID')
	client_secret = models.TextField('Merchant Password')

	def __unicode__(self):
		return unicode(self.merchant_name)


class PropelldProgramMap(models.Model):
	propelld_name = models.CharField('PROPELLD NAME', max_length=45)
	client_id = models.TextField('Merchant ID')
	client_secret = models.TextField('Merchant Password')

	def __unicode__(self):
		return unicode(self.propelld_name)


class Program(models.Model):
	"""Model for Programs."""

	program_code = models.CharField(max_length=6,unique=True,
		validators=[ RegexValidator(regex='^[a-zA-Z0-9]{4}$',
			message=_('program code must be Alphanumeric'),
			code=_('invalid_program_code')),
		])  # Field name made lowercase.
	program_name = models.CharField(max_length=60,)  # Field name made lowercase.
	form_title = models.CharField(max_length=200,)
	available_in_cities = models.ManyToManyField('Location')
	alternative_program_code = models.CharField(max_length=45,blank=True, null=True)
	program_type = models.CharField(max_length=30, choices=PROGRAM_TYPE_CHOICES,)
	application_pdf_template = models.CharField(max_length=60, choices=APPLICATION_PDF_TEMPLATE_CHOICES,blank=True, null=True)
	offer_letter_template = models.CharField(max_length=60, choices=OFFER_LETTER_TEMPLATE_CHOICES,blank=True, null=True)
	collaborating_organization = models.ForeignKey('CollaboratingOrganization',
								related_name='%(class)s_requests_created_4',
								blank=True, null=True)
	org_logo_image = ThumbnailerImageField(upload_to=document_upload_page_path, blank=True, null=True)
	document_upload_page_path = models.CharField(max_length=100,
		choices=DOCUMENT_UPLOAD_CHOICES,
		blank=True, null=True)
	active_for_applicaton_flag = models.BooleanField(default=False)
	document_submission_flag = models.BooleanField('Allow Submission and Re-submission of Documents by Applicants',
												   default=False)
	active_for_admission_flag = models.BooleanField(default=False)
	show_on_page_flag = models.BooleanField(default=False)
	serial_number_on_page = models.PositiveIntegerField()
	show_to_fee_wvr_appl_flag = models.BooleanField('Show Program to Applicants with fee waivers in other Programs',default=False)
	work_exp_check_req = models.BooleanField('Work Experience Check Required',default=True)
	mentor_id_req = models.BooleanField('Mentor Consent Required',default=True)
	min_work_exp_in_months = models.PositiveIntegerField('Minimum Work Experience in Months',
		blank = True,null = True)
	hr_cont_req = models.BooleanField('HR Contact Required', default=True)
	is_zest_emi_enable = models.BooleanField('Enable Zest for Admission Fee Payment',default=False)
	is_eduvanz_emi_enable = models.BooleanField('Enable Eduvanz for Admission Fee Payment',default=False)
	is_ezcred_emi_enable = models.BooleanField('Enable EzCred (ABFL) for Admission Fee Payment',default=False)
	is_propelld_emi_enable = models.BooleanField('Enable Propelld for Admission Fee Payment',default=False)
	zest_location = models.ManyToManyField('Location', related_name='%(class)s_zest_loc', blank=True,)
	eduvanz_location = models.ManyToManyField('Location', related_name='%(class)s_edu_loc', blank=True,)
	zest = models.ForeignKey(ZestProgramMap,related_name='%(class)s_zest', blank=True, null=True,verbose_name='Choose Zest EMI Plan')
	propelld = models.ForeignKey(PropelldProgramMap,related_name='%(class)s_propelld', blank=True, null=True, verbose_name = 'Choose Propelld EMI Plan')
	propelld_course_id = models.IntegerField('Enter Propelld Course ID',max_length=30,blank=True,null=True)
	enable_pre_selection_flag = models.BooleanField(default=False)
	

	def __unicode__(self):
		"""Return Unicode Program Names."""
		return unicode("{0} - {1} ({2})".format(self.program_code,self.program_name,
			self.program_type.upper()))

	class Meta:
		"""Order By Program Names."""

		ordering = ['serial_number_on_page']
	def clean(self):
		if self.is_propelld_emi_enable ==True:
				if not self.propelld:
					raise ValidationError("Please Choose Propelld Program Map")
		if self.is_propelld_emi_enable ==True:
			if not self.propelld_course_id:
				raise ValidationError("Please Provide the Propelld Course ID. Course ID should be a numeric value")		
			
	

Program.available_in_cities.through.__unicode__ = lambda x: x.location.location_name

class QualificationCategory(models.Model):
	category_name = models.CharField(max_length = 45,unique=True)

	def __unicode__(self):
		return self.category_name

	class Meta:
		ordering = ['category_name']
		verbose_name = 'Qualification Category'
		verbose_name_plural = 'Qualification Categories'


class ProgramQualificationRequirements(models.Model):
	program = models.ForeignKey(Program,
		related_name='%(class)s_requests_created_1')
	qualification_category = models.ForeignKey(QualificationCategory,
		related_name='%(class)s_requests_created_2')

	def __unicode__(self):
		return unicode( self.qualification_category.category_name )

	class Meta:
		verbose_name = 'Program Qualification Category Mapping'
		verbose_name_plural = 'Program Qualification Category Mapping'
		unique_together=('program','qualification_category')



class Degree(models.Model):

	degree_short_name = models.CharField(max_length=30,unique=True,)
	degree_long_name = models.CharField(max_length=45,)
	qualification_category = models.ForeignKey(QualificationCategory,
		related_name='%(class)s_requests_created_1',blank=True, null=True)

	def __unicode__(self):
		"""Return unicode Degree Name."""
		return unicode( self.degree_short_name )

	class Meta:
		"""Order the Degree Names by Long Names."""

		ordering = ['degree_short_name']


class PROGRAM_FEES_ADMISSION(models.Model):
	"""Model for Program Admission Fees."""

	admit_year = models.IntegerField(validators=[MaxValueValidator(9999)])
	program = models.ForeignKey(Program,related_name='%(class)s_requests_created_4')
	latest_fee_amount_flag = models.BooleanField( default = True )
	sequence_number = models.IntegerField(blank=True, null=True)  # Field name made lowercase.
	fee_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(1)])
	fee_type = models.CharField(max_length=16, choices=FEE_TYPE_CHOICES)
	fee_expiry = models.DateField( blank=True, null=True )
	stud_id_gen_st_num = models.PositiveIntegerField('student id generate start number', blank=True, null=True)
	admit_sem_des = models.CharField('Admit Semester Description',
		help_text='This text will show up as the semester detail in the candidate offer letter for this program.',
		max_length=30,blank=True, null=True)
	admit_sem_cohort = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(9999)])
	is_paytm_enable = models.BooleanField(default=False)

	def __unicode__(self):
		"""Return Uniocde Sequence Number."""
		return unicode(self.program.program_code)

	def save(self,*args,**kwargs):
		if not self.pk:
			query=PROGRAM_FEES_ADMISSION.objects.filter(
				admit_year=self.admit_year,
				program=self.program,
				fee_type=self.fee_type,
				)
			if len(query)==0:
				self.sequence_number=1
			else:
				value=query.aggregate(max_seq=models.Max('sequence_number'))
				self.sequence_number=value['max_seq']+1

		if self.latest_fee_amount_flag == True:
			for x in PROGRAM_FEES_ADMISSION.objects.filter(program=self.program,
				fee_type=self.fee_type):
				x.latest_fee_amount_flag=False
				x.save()

		super(PROGRAM_FEES_ADMISSION, self).save(*args, **kwargs)

	class Meta:
		verbose_name = 'Program fees admission'
		verbose_name_plural = 'Program fees admissions'



class Instruction(models.Model):
	"""Model for User Instructions."""

	text = RichTextField(verbose_name=" ")


class StudentCandidateApplication(models.Model):
	"""Model for Student Candidate Application."""

	TEACHING_CHOICES = (
		(None,'Choose Teaching Mode'),
		('ONLINE', 'ONLINE'),
		('FACE-TO-FACE', 'FACE-TO-FACE'),
	)

	PRE_SELECTION_FLAG_CHOICES = (
		(None, ''), 
		('Accepted', 'True'), 
		('Rejected', 'False'),
	)#Instead of Bool Field we are using choice field Accepted = True & Rejected = False

	PROGRAMMING_FLAG_CHOICES = (
		('True', 'Yes'), 
		('False', 'No'),
	)
	
	login_email = models.ForeignKey(User,related_name='%(class)s_requests_created_5',
		unique=True)
	full_name = models.CharField('Full Name',max_length=100)
	first_name = models.CharField('First Name',max_length=25, blank=True, null=True)
	middle_name = models.CharField(max_length=25, blank=True, null=True)
	last_name = models.CharField(max_length=25,blank=True, null=True)
	gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
	date_of_birth = models.DateField()  # Field name made lowercase.
	address_line_1 = models.CharField(max_length=60)
	address_line_2 = models.CharField(max_length=40, blank=True, null=True)
	address_line_3 = models.CharField(max_length=40, blank=True, null=True)
	city = models.CharField(max_length=20, blank=True, null=True)
	pin_code = models.PositiveIntegerField(blank=True, null=True)
	state = models.CharField(max_length=20, choices=STATE_CHOICES)
	country = CountryField(blank_label='Select country')
	application_status = models.CharField(max_length=70, blank=True, null=True)
	current_organization = models.CharField(max_length=50, blank=True,null=True)
	program = models.ForeignKey(Program,related_name='%(class)s_requests_created_6',blank=True, null=True)
	current_location = models.ForeignKey(
		Location,verbose_name='Preferred Exam Location',
		related_name='%(class)s_requests_created_7',
		related_query_name='%(class)s_requests_created_7s', blank=True,
		null=True)  # Field name made lowercase.
	fathers_name = models.CharField(max_length=100, blank=True, null=True)
	mothers_name = models.CharField(max_length=100, blank=True, null=True)
	nationality = models.CharField(max_length=15, choices=NATIONALITY_CHOICES)
	phone = PhoneNumberField()  # Field name made lowercase.
	mobile = PhoneNumberField()  # Field name made lowercase.
	email_id = models.EmailField(max_length=50, blank=True, null=True)
	current_employment_status = models.CharField(
		max_length=20, choices=EMPLOYMENTSTATUS_CHOICES)
	employer_consent_flag = models.BooleanField(default=False)
	employer_mentor_flag = models.BooleanField(default=False)
	current_org_employee_number = models.CharField(
		max_length=15, blank=True, null=True)  # Field name made lowercase.
	current_designation = models.CharField(
		max_length=30, blank=True, null=True)  # Field name made lowercase.
	fee_payment_owner = models.CharField(
		max_length=50, choices=FEEPAYMENT_CHOICES)  # Field name made lowercase
	current_org_industry = models.ForeignKey(
		Industry, related_name='%(class)s_requests_created_8', blank=True,
		null=True)  # Field name made lowercase.
	current_org_employment_date = models.DateField()
	work_location = models.ForeignKey(
		Location, related_name='%(class)s_requests_created_109',
		related_query_name='%(class)s_requests_created_7s1', blank=True,
		null=True)  # Field name made lowercase.
	exam_location = models.CharField(max_length=45, blank=True, null=True)
	total_work_experience_in_months = models.DecimalField("total Experience",
		max_digits=10, decimal_places=2,
		blank=True, null=True)
	math_proficiency_level = models.CharField(
		max_length=45, choices=LEVEL_CHOICES)  # Field name made lowercase.
	prior_student_flag = models.CharField(
		max_length=45, choices=PRIOR_CHOICES)  # Field name made lowercase.
	bits_student_id = models.CharField(max_length=15, blank=True, null=True)
	parallel_studies_flag = models.CharField(
		max_length=45, choices=PARALLEL_CHOICES)  # Field name made lowercase.
	bonafide_flag = models.BooleanField(default=True)
	created_on_datetime = models.DateTimeField(auto_now_add=True, blank=True)
	last_updated_on_datetime = models.DateTimeField(
		auto_now=True, blank=True)  # Field name made lowercase.
	student_application_id = models.CharField(
		max_length=20, blank=True, null=True)  # Field name made lowercase.
	admit_year = models.PositiveIntegerField(validators=[MaxValueValidator(9999)])
	admit_sem_cohort = models.PositiveIntegerField(default=0, blank=True, null=True,
		validators=[MaxValueValidator(9999)])
	admit_batch = models.CharField(max_length=50, blank=True, null=True)
	teaching_mode = models.CharField(
		max_length=45, choices=TEACHING_CHOICES, blank=True, null=True)
	pre_selected_flag = models.CharField(
		max_length=10, choices=PRE_SELECTION_FLAG_CHOICES, blank=True, null=True)
	pre_selected_rejected_on_datetime = models.DateTimeField(blank=True, null=True)
	programming_flag = models.CharField(
		max_length=10, choices=PROGRAMMING_FLAG_CHOICES, blank=True, null=True)
	alternate_email_id = models.EmailField(max_length=50, blank=True, null=True)

	def fullname(self):
		return self.full_name

	def application_id(self):
		"""Return Application Id."""
		return self.student_application_id

	def user_email(self):
		"""Return User Email Id."""
		return self.login_email.email

	def program_name(self):
		"""Return Program Name."""
		return self.program.program_name

	def current_status(self):
		"""Return Application Status."""
		return self.application_status

	def __unicode__(self):
		"""Return Unicode First Name."""
		return self.full_name

class StudentCandidateQualification(models.Model):
	"""Model for Student Candidate Qualification."""

	application = models.ForeignKey(
		StudentCandidateApplication,
		related_name='%(class)s_requests_created_12')
	school_college = models.CharField(
		max_length=45, blank=True, null=True)  # Field name made lowercase.
	duration = models.CharField(
		max_length=45, choices=DURATION_CHOICES)  # Field name made lowercase.
	percentage_marks_cgpa = models.DecimalField(
		max_digits=10, decimal_places=2)  # Field name made lowercase.
	completion_year = models.CharField(max_length=5, blank=True, null=True)
	division = models.CharField(max_length=10, choices=DIVISION_CHOICES)
	degree = models.ForeignKey(
		Degree, related_name='%(class)s_requests_created_13')
	discipline = models.ForeignKey(
		Discpline, related_name='%(class)s_requests_created_14')
	other_degree = models.CharField(max_length=30, blank=True, null=True)
	other_discipline = models.CharField(max_length=40, blank=True, null=True)

	def __unicode__(self):
		"""Return College."""
		return self.school_college


class StudentCandidateWorkExperience(models.Model):
	"""Model for Student Candidate Work Experience."""

	application = models.ForeignKey(
		StudentCandidateApplication,
		related_name='%(class)s_requests_created_15',
		blank=True, null=True)  # Field name made lowercase.
	organization = models.CharField(max_length=50)
	start_date = models.DateField(blank=True, null=True)
	end_date = models.DateField(blank=True, null=True)
	designations = models.CharField(max_length=100)

	def __unicode__(self):
		"""Return Unicode Designation."""
		return self.designations

class Reviewer(models.Model):
	REVIEWER_CHOICES = (
		(None,'Choose User'),
		('super-reviewer', 'Super Reviewer'),
		('payment-reviewer', 'Payment Reviewer'),
		('business-developer', 'Business Developer'),
		('sub-reviewer', 'Sub Reviewer'),
		)
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	reviewer = models.BooleanField(default=False)
	payment_reviewer = models.BooleanField(default=False)
	user_role = models.CharField(max_length=100,
		choices=REVIEWER_CHOICES,blank=True, null=True)

	def __unicode__(self):
		"""Return unicode."""
		return unicode(self.reviewer)


class CollaboratingOrganization(models.Model):
	org_name = models.CharField(max_length=60,unique=True,)

	def __unicode__(self):
		"""Return Unicode org_name."""
		return unicode(self.org_name)

class ExceptionListOrgApplicants(models.Model):
	application = models.ForeignKey(StudentCandidateApplication,
		related_name='%(class)s_app',blank=True, null=True)
	employee_email = models.EmailField(max_length=50,db_index=True)
	exception_type = models.CharField(max_length=2,choices=FEE_TYPE_CHOICE,db_index=True)
	org = models.ForeignKey(CollaboratingOrganization,
		related_name='%(class)s_requests_created_100')
	program = models.ForeignKey(Program,
		related_name='%(class)s_requests_created_101')
	employee_id = models.CharField(max_length=15)
	employee_name = models.CharField(max_length=50)
	fee_amount = models.DecimalField(max_digits=10, 
		validators=[MinValueValidator(Decimal('0.01'))], 
		decimal_places=2, 
		blank=True, null=True)

	def __unicode__(self):
		"""Return Unicode Designation."""
		return self.employee_name

	def save(self,*args,**kwargs):

		try:
			sca = StudentCandidateApplication.objects.get(
				login_email__email = self.employee_email,
				program = self.program)
		except StudentCandidateApplication.DoesNotExist :pass 
		else :
			ExceptionListOrgApplicants.objects.filter(
					employee_email = sca.login_email.email,
					).exclude(
						program = sca.program,).update( application = None ) 
			ExceptionListOrgApplicants.objects.filter(
				employee_email = sca.login_email.email,
				program = sca.program).update( application = sca )

			self.application = sca

		super(ExceptionListOrgApplicants, self).save(*args, **kwargs)

	class Meta:
		"""Order By Exception List OrgApplicants."""

		verbose_name = 'Exception List for Applicant Fee Waivers'
		verbose_name_plural = 'Exception List for Applicant Fee Waivers'
		unique_together = (('employee_email', 'exception_type','program'),)



class ApplicationDocument(models.Model):
	"""Model which stores the Applicant Document with last updated time."""
	application = models.ForeignKey(StudentCandidateApplication,related_name='%(class)s_requests_created_1')  # Field name made lowercase.
	document = models.ForeignKey(DocumentType,related_name='%(class)s_requests_created_2')  # Field name made lowercase.
	file = models.FileField(verbose_name='Student File Upload', upload_to=user_directory_path, blank=True, null=True, max_length=1000)
	last_uploaded_on = models.DateTimeField(blank=True, null=True)
	certification_flag = models.BooleanField(default=False)
	reload_flag = models.BooleanField(default=False)
	accepted_verified_by_bits_flag = models.BooleanField(default=False)
	inspected_on = models.DateTimeField(blank=True, null=True)
	rejected_by_bits_flag = models.BooleanField(default=False)
	rejection_reason = models.ForeignKey(ApplicantionDocumentReason, related_name='%(class)s_requests_created_5859',blank=True, null=True)
	verified_rejected_by = models.CharField(max_length=255, blank=True, null=True)
	exception_notes = models.CharField(max_length=100,blank=True, null=True)
	program_document_map = models.ForeignKey('ProgramDocumentMap', related_name='%(class)s_1', blank=True, null=True)

	def __unicode__(self):
		"""Return unicode."""
		return self.file.name.split("/")[-1]

	class Meta:
		"""Order By Mandatory Document."""

		ordering = ['-document__mandatory_document']
		unique_together = ('document', 'application')




class CandidateSelection(models.Model):
	"""Model which stores the selected or rejected Applicants Details."""

	application = models.ForeignKey(StudentCandidateApplication,
		related_name='%(class)s_requests_created_5550',unique=True)
	student_id = models.CharField(max_length=11,blank=True, null=True)
	old_student_id = models.CharField(max_length=11,blank=True, null=True)
	verified_student_name = models.CharField(max_length=60,blank=True, null=True)
	name_verified_on = models.DateTimeField(blank=True, null=True)
	name_verified_by = models.CharField(max_length=45,blank=True, null=True)
	selected_rejected_on = models.DateTimeField(blank=True, null=True)
	bits_rejection_reason = models.TextField(blank=True, null=True)
	selection_rejection_comments = models.CharField(max_length=45,blank=True, null=True)
	bits_selection_rejection_by = models.CharField(max_length=45,blank=True, null=True)
	accepted_rejected_by_candidate = models.DateTimeField(blank=True, null=True)
	rejection_by_candidate_reason = models.ForeignKey(ApplicantRejectionReason,
		related_name='%(class)s_requests_created_5651',blank=True, null=True)
	rejection_by_candidate_comments = models.CharField(max_length=50,blank=True, null=True)
	offer_reject_mail_sent = models.DateTimeField(blank=True, null=True)


	es_to_su_rev = models.BooleanField(default=False)
	es_com = models.CharField(max_length=100,blank=True, null=True)
	su_rev_app = models.BooleanField(default=False)
	su_rev_com = models.CharField(max_length=100,blank=True, null=True)
	es_to_su_rev_dt = models.DateTimeField(blank=True, null=True)
	app_rej_by_su_rev_dt = models.DateTimeField(blank=True, null=True)
	prog_ch_flag = models.BooleanField(default=False)
	new_sel_prog = models.ForeignKey(Program,
		related_name='%(class)s_program',blank=True, null=True)
	prior_status = models.CharField(max_length=70,blank=True, null=True)
	new_application_id = models.CharField(
		max_length=60, blank=True, null=True)


	m_name = models.CharField('Mentor Name',
		max_length=60,blank=True, null=True)
	m_des = models.CharField('Mentor Designation',
		max_length=30,blank=True, null=True)
	m_mob_no = PhoneNumberField('Mentor Mobile Number',
		blank=True, null=True)
	m_email = models.EmailField('Mentor Email',blank=True, null=True)

	hr_cont_name = models.CharField('HR Contact Name',
		max_length=60,blank=True, null=True)
	hr_cont_des = models.CharField('HR Contact Designation',
		max_length=30,blank=True, null=True)
	hr_cont_mob_no = PhoneNumberField('HR Contact Mobile Number',
		blank=True, null=True)
	hr_cont_email = models.EmailField('HR Contact Email',blank=True, null=True)

	dps_flag = models.BooleanField('data_ported_to_sdms_flag',
	default=False)
	dps_datetime = models.DateTimeField('data_ported_to_sdms_datetime',
	blank=True, null=True)

	doc_resubmission_dt = models.DateTimeField(blank=True, null=True)
	fee_payment_deadline_dt = models.DateTimeField(blank=True, null=True)
	orientation_dt = models.DateTimeField(blank=True, null=True)
	lecture_start_dt = models.DateTimeField(blank=True, null=True)
	orientation_venue = models.CharField(max_length=100,blank=True, null=True)
	lecture_venue = models.CharField(max_length=100,blank=True, null=True)
	admin_contact_person = models.CharField(max_length=50,blank=True, null=True)
	acad_contact_person = models.CharField(max_length=50,blank=True, null=True)
	admin_contact_phone = PhoneNumberField(blank=True, null=True,help_text='eg +918326974266')
	acad_contact_phone = PhoneNumberField(blank=True, null=True,help_text='eg +918326974266')
	adm_fees = models.FloatField(blank=True, null=True)
	offer_letter_generated_flag = models.BooleanField(default=False)
	offer_letter_regenerated_dt = models.DateTimeField(blank=True, null=True)
	admitted_to_program = models.ForeignKey(Program,
		related_name='%(class)s_admit_pg',blank=True, null=True)
	offer_letter_template = models.CharField(max_length=45,
		choices=OFFER_LETTER_TEMPLATE_CHOICES,blank=True, null=True)
	offer_letter_tmp = models.TextField(blank=True, null=True)
	offer_letter = models.FileField(verbose_name='Offer Letter', upload_to=user_directory_path, blank=True, null=True, max_length=1000)

	def __unicode__(self):
		"""Return unicode."""
		return unicode(self.application.full_name)

class ProgramLocationDetails(models.Model):
	program = models.ForeignKey(Program,
		related_name='%(class)s_requests_created_8888')
	location = models.ForeignKey(
		Location, related_name='%(class)s_requests_created_13459')
	fee_payment_deadline_date = models.DateTimeField(
		help_text='''This date shows up in offer acceptance page for the applicant for the program as 
							well as on the offer letter issued to the applicant after acceptance of admission for the program.'''
		)
	orientation_date = models.DateTimeField(blank=True, null=True,
		help_text='''This date shows up in the offer letter for the program and location where the applicant 
							will be located while studying in the program.'''
		)
	lecture_start_date = models.DateTimeField(blank=True, null=True,
		help_text='''This date shows up in  the offer letter for the program and location where the applicant 
							will be located while studying in the program.'''
		)
	orientation_venue = models.CharField(max_length=100,blank=True, null=True,
		help_text='This location shows up in the offer letter based on the location from where the applicant will attend the program.'
		)
	lecture_venue = models.CharField(max_length=100,blank=True, null=True)
	admin_contact_person = models.CharField(max_length=50,blank=True, null=True)
	acad_contact_person = models.CharField(max_length=50,blank=True, null=True)
	admin_contact_phone = PhoneNumberField(blank=True, null=True,help_text='eg +918326974266')
	acad_contact_phone = PhoneNumberField(blank=True, null=True,help_text='eg +918326974266')

	def __unicode__(self):
		"""Return unicode."""
		return unicode(self.fee_payment_deadline_date)


	class Meta:
		verbose_name = 'Program and Location Details'
		verbose_name_plural = 'Program and Location Details'
		unique_together = ('program', 'location')



class MetaPayment(models.Model):
	application = models.ForeignKey(StudentCandidateApplication,
		related_name='%(class)s_requests_created_9830')
	order_id = models.CharField(max_length=100, blank=True, null=True)
	req_pay_req_date = models.DateTimeField(blank=True, null=True)
	req_pay_status = models.IntegerField(blank=True, null=True)
	req_json_data =  jsonfield.JSONField(blank=True, null=True)
	req_json_return_data =  jsonfield.JSONField(blank=True, null=True)
	req_pay_res_date = models.DateTimeField(blank=True, null=True)

	res_pay_req_date = models.DateTimeField(blank=True, null=True)
	res_pay_status = models.IntegerField(blank=True, null=True)
	res_json_data =  jsonfield.JSONField(blank=True, null=True)
	res_json_return_data =  jsonfield.JSONField(blank=True, null=True)
	res_pay_res_date = models.DateTimeField(blank=True, null=True)

	fee_type = models.CharField(max_length=16, choices=FEE_TYPE_CHOICES)
	sequence_number = models.IntegerField()

	def __unicode__(self):
		"""Return unicode."""
		return self.application.student_application_id

class ProgramDomainMapping(models.Model):
	program = models.ForeignKey(Program,related_name='%(class)s_requests_created_1')
	email_domain = models.CharField(max_length=45,blank=True, null=True)
	email = models.EmailField(max_length=45,blank=True, null=True)

	def __unicode__(self):
		"""Return Unicode First Name."""
		return unicode(self.email_domain)

class ProgramDocumentMap(models.Model):
	program = models.ForeignKey(Program,related_name='%(class)s_requests_created_1')

	document_type = models.ForeignKey(DocumentType,
		related_name='%(class)s_requests_created_2')
	mandatory_flag = models.BooleanField(default=False)
	deffered_submission_flag = models.BooleanField('Deferred Submission Flag', default=False)

	def __unicode__(self):
		"""Return Unicode First Name."""
		return self.program.program_code

	class Meta:
		unique_together=('program','document_type')
		ordering = ['-mandatory_flag']


class  FormFieldPopulationSpecific(models.Model):
	program = models.ForeignKey(Program,related_name='%(class)s_requests_created_1')
	field_name = models.CharField(max_length=45,)
	show_on_form = models.BooleanField(default=True)
	default_value = models.CharField(max_length = 45,blank = True,null = True)
	is_editable = models.BooleanField(default = True)

	def __unicode__(self):
		"""Return Unicode First Name."""
		return self.field_name

	class Meta:
		unique_together = ('program','field_name')


class StudentCandidateApplicationSpecific(models.Model):
	application = models.OneToOneField(StudentCandidateApplication,
		on_delete=models.CASCADE)
	collaborating_organization = models.ForeignKey(CollaboratingOrganization,
		related_name='%(class)s_requests_created_1')

	def __unicode__(self):
		"""Return unicode."""
		return unicode(self.collaborating_organization)

class FirstSemCourseList(models.Model):
	program = models.ForeignKey(Program,related_name='%(class)s_requests_created_1')
	admit_year = models.PositiveIntegerField(validators=[MaxValueValidator(9999)],)
	course_id = models.CharField(max_length = 10,)
	course_name = models.CharField(max_length = 60,)
	course_unit = models.PositiveIntegerField()
	active_flag = models.BooleanField(default = True)
	is_elective = models.BooleanField(default = False)

	def __unicode__(self):
		return unicode(self.course_id)

	class Meta:
		verbose_name = 'Course List'
		verbose_name_plural = 'Course List'
		ordering = ['course_id']

class ElectiveCourseList(models.Model):
	program = models.ForeignKey(Program,related_name='%(class)s_1')
	course_id = models.CharField(max_length=10)
	course_id_slot = models.ForeignKey(FirstSemCourseList, 
		related_name='%(class)s_2', 
		verbose_name = 'elective slot')
	course_name = models.CharField(max_length=60)
	course_units = models.PositiveIntegerField(blank=True, null=True)
	is_active = models.BooleanField(default=True)

	def __unicode__(self):
		return unicode("{0} - {1}".format(self.course_id.upper(),self.course_name.title()))

	class Meta:
		verbose_name = 'Elective Courses'
		verbose_name_plural = 'Elective Courses'

class StudentElectiveSelection(models.Model):
	student_id = models.ForeignKey(CandidateSelection, related_name='%(class)s_1')
	program = models.ForeignKey(Program, related_name='%(class)s_2')
	application = models.ForeignKey(StudentCandidateApplication,
		related_name='%(class)s_3')
	course_id_slot = models.ForeignKey(FirstSemCourseList,
		related_name='%(class)s_4')
	course_units = models.ForeignKey(ElectiveCourseList,
		related_name='%(class)s_5', null=True)
	course = models.ForeignKey(ElectiveCourseList,
		related_name='%(class)s_6', null=True)
	inserted_on_datetime = models.DateTimeField(auto_now_add=True)
	last_updated_on_datetime = models.DateTimeField(auto_now=True)
	is_locked = models.BooleanField(default=False)

	def __unicode__(self):
		return unicode(self.student_id.student_id)

class BitsUser(models.Model):
	SOURCE_SITE_CHOICES = (
		(None,'choose site'),
		('bits_websites','BITS WEBSITES'),
		('email_campaign','EMAIL CAMPAIGN'),
		('advertisement','ADVERTISEMENT'),
		('others','OTHERS'),
		)
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='%(class)s_user')
	last_followup_mail_sent_on = models.DateTimeField( null = True, blank=True )
	mails_sent_count = models.PositiveIntegerField( default = 0 )
	last_followup_app_fee_mail_sent = models.DateTimeField( null = True, blank=True )
	app_fee_mail_sent_count = models.PositiveIntegerField( default = 0 )
	source_program = models.ForeignKey(Program, related_name='%(class)s_pg',
	 null=True, blank=True)
	source_site = models.CharField(max_length=50, choices=SOURCE_SITE_CHOICES,
		null=True, blank=True)
	register_program_id = models.ForeignKey(Program, related_name='%(class)s_pgm',
	 null=True, blank=True)
	utm_source_first = models.CharField(max_length=50, null=True, blank=True)
	utm_medium_first = models.CharField(max_length=45, null=True, blank=True)
	utm_campaign_first = models.CharField(max_length=50, null=True, blank=True)
	utm_source_last = models.CharField(max_length=50, null=True, blank=True)
	utm_medium_last = models.CharField(max_length=45, null=True, blank=True)
	utm_campaign_last = models.CharField(max_length=50, null=True, blank=True)

	def __unicode__(self):
		return unicode('mails_sent_count:{0} and app_fee_mail_sent_count:{1}'.format(
			self.last_followup_mail_sent_on,
			self.app_fee_mail_sent_count)
		)

	@receiver(post_save, sender=User)
	def create_user_profile(sender, instance, created, **kwargs):
		if created:
			BitsUser.objects.create(user=instance)

	@receiver(post_save, sender=User)
	def save_user_profile(sender, instance, **kwargs):
		instance.bitsuser_user.save()

	def __init__(self, *args, **kwargs):
		super(BitsUser, self).__init__(*args, **kwargs)
		self.utm_source_last_current = self.utm_source_last
		self.utm_medium_last_current = self.utm_medium_last
		self.utm_campaign_last_current = self.utm_campaign_last

class FollowUpMailLog(models.Model):

	MAIL_CHOICES =(
		('1','FOLLOW UP MAIL. APPLICATION NOT FILLED'),
		('2','FOLLOW UP MAIL. APPLICATION FEE PAYMENT'),
		)

	run = models.PositiveIntegerField(default = 0)
	mail_type = models.CharField(max_length = 45, choices = MAIL_CHOICES)
	mail_sent_time = models.DateTimeField(auto_now_add=True, blank=True)
	no_of_mails_sent = models.PositiveIntegerField( default = 0 )

	def __unicode__(self):
		return unicode(self.run)


class BatchMailConfig(models.Model):
	MAIL_CHOICES = (
		(None,'Choose Mail'),
		('1', 'Config for Automated Emailers Registered Users who are yet to Apply'),
		('2', 'Config for Automated Emailers to Applications who are yet to pay Application Fees'),
	)
	initial_day = models.PositiveIntegerField('Initial Gap')
	cutoff_date = models.DateField()
	mail_type = models.CharField(max_length=16, choices=MAIL_CHOICES)

	def __unicode__(self):
		return unicode('{0} to {1}'.format(self.initial_day,self.cutoff_date))



class ApplicantExceptions(models.Model):
	application = models.ForeignKey(StudentCandidateApplication,
		related_name='%(class)s_app', blank=True, null=True)
	applicant_email = models.EmailField('Applicant email ID / user ID')
	program = models.ForeignKey(Program,related_name='%(class)s_pg',
		verbose_name='Choose Program')
	work_ex_waiver = models.BooleanField('Work Experience waiver required?',default=False)
	employment_waiver = models.BooleanField('Employment waiver required (candidate can be unemployed while applying)?',
		default=False)
	mentor_waiver = models.BooleanField('Mentor details not required to be provided?',
		default=False)
	hr_contact_waiver = models.BooleanField('HR contact details not required to be provided?',
		default=False)
	offer_letter = models.CharField('Choose custom offer letter template, if applicable',
		max_length=100,choices=OFFER_LETTER_TEMPLATE_CHOICES,help_text='If an offer letter template is chosen, the applicant will get their offer letter generated using this template. It will override offer letter templates set at program level in the program table',blank=True, null=True)
	org = models.ForeignKey(CollaboratingOrganization,
		related_name ='%(class)s_coll_org', blank=True, null=True,
		verbose_name='Choose organization')
	created_on_datetime = models.DateTimeField(auto_now_add=True, blank=True)
	transfer_program = models.ForeignKey(Program,related_name='%(class)s_trans_pg',
		verbose_name='Choose Transfer Program',blank=True, null=True,
		help_text='If a transfer program is chosen, post accceptance of admission offer, the applicant will be admitted to this program and NOT the program they have applied for. You may have to regenerate the offer letter in case the transfer program entry is made post acceptance of admission offer by the applicant')

	def __unicode__(self):
		"""Return Unicode Applicant Email."""
		return unicode(self.applicant_email)

	def save(self,*args,**kwargs):

		try:
			sca = StudentCandidateApplication.objects.get(
				login_email__email = self.applicant_email,
				program = self.program)
		except StudentCandidateApplication.DoesNotExist :pass 
		else :
			ApplicantExceptions.objects.filter(
					applicant_email = sca.login_email.email,
					).exclude(
						program = sca.program,).update( application = None ) 
			ApplicantExceptions.objects.filter(
				applicant_email = sca.login_email.email,
				program = sca.program).update( application = sca )

			self.application = sca

		super(ApplicantExceptions, self).save(*args, **kwargs)

	class Meta:
		verbose_name = 'Applicant Exception'
		ordering = ['applicant_email']
		unique_together = ('applicant_email','program')


from django.core.exceptions import ValidationError
class OtherFeePayment(models.Model):
	"""Model with Other Fee Payment Information."""

	email = models.EmailField()
	program = models.ForeignKey(Program, related_name='%(class)s_prog')
	fee_type = models.CharField(max_length=45)
	fee_amount = models.DecimalField(max_digits=10, decimal_places=2,
		validators=[MinValueValidator(Decimal('0.01'))],)
	Zest_Program_Map = models.ForeignKey(ZestProgramMap, related_name='%(class)s_zest_adhoc', blank=True, null=True)
	Propelld_Program_Map = models.ForeignKey(PropelldProgramMap, related_name='%(class)s_propelld_adhoc', blank=True, null=True)
	propelld_course_id = models.IntegerField('Enter Propelld Course ID',max_length=30,blank=True,null=True)
	enable_zest_flag = models.BooleanField('Enable Zest',default=False)
	enable_eduvenz_flag = models.BooleanField('Enable Eduvanz',default=False)
	enable_propelld_flag = models.BooleanField('Enable PROPELLD',default=False)
	enable_ABFL_flag = models.BooleanField('Enable ABFL',default=False)
	created_on = models.DateTimeField(auto_now_add=True,)
	paid_on = models.DateTimeField(blank=True, null=True)
	transaction_id = models.CharField(max_length=45, blank=True, null=True)
	payment_bank = models.CharField(max_length=45, blank=True, null=True)
	gateway_total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
	gateway_net_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
	uploaded_on = models.DateTimeField(blank=True, null=True)
	student_application_id = models.CharField(max_length=20, blank=True, null=True)
	student_id = models.CharField(max_length=20, blank=True, null=True)
	full_name = models.CharField(max_length=100, blank=True, null=True)
	mobile = PhoneNumberField(blank=True, null=True)

	def __unicode__(self):
		return unicode(self.email)

	class Meta:
		unique_together = ('email','program','fee_type')


	def clean(self):
		if self.enable_zest_flag ==True:
			if not self.Zest_Program_Map:
				raise ValidationError("Please Choose Zest Program Map")

	def clean(self):
		if self.enable_propelld_flag ==True:
			if not self.Propelld_Program_Map:
				raise ValidationError("Please Choose Propelld Program Map")
		if self.enable_propelld_flag ==True:
			if not self.propelld_course_id:
				raise ValidationError("Please Provide the Propelld Course ID. Course ID should be a numeric value")		
		


class SaleForce(models.Model):
	is_inserted = models.BooleanField(default=False)
	created_on = models.DateTimeField(auto_now_add=True)
	updated_on = models.DateTimeField(auto_now=True)
	sent_to_sf_on = models.DateTimeField(blank=True, null=True)
	status = models.CharField(max_length=45)
	dataset = jsonfield.JSONField(blank=True, null=True)
	reference_id = models.CharField(max_length=100)
	response = jsonfield.JSONField()

	class Meta:
		abstract = True

	def __unicode__(self):
		return unicode(self.updated_on)

class SaleForceLeadDataLog(SaleForce):
	user = models.ForeignKey(User, related_name='%(class)s_user', blank=True, null=True)
	
class SaleForceQualificationDataLog(SaleForce):
	qualification = models.ForeignKey(StudentCandidateQualification, 
		related_name='%(class)s_qual', blank=True, null=True)

class SaleForceWorkExperienceDataLog(SaleForce):
	work_experience = models.ForeignKey(StudentCandidateWorkExperience, 
		related_name='%(class)s_exp', blank=True, null=True)

class SaleForceDocumentDataLog(SaleForce):
	document = models.ForeignKey(ApplicationDocument, 
		related_name='%(class)s_ad', blank=True, null=True)

class SaleForceAsyncTask(models.Model):
	SALE_FORCE_CHOICES = (
		(None, 'No Table choosen (might be old one)'),
		(SaleForceLeadDataLog._meta.model.__name__, 'lead'), 
		(SaleForceQualificationDataLog._meta.model.__name__, 'qual'),
		(SaleForceWorkExperienceDataLog._meta.model.__name__, 'exp'),
		(SaleForceDocumentDataLog._meta.model.__name__, 'doc'),
	)
	model_type = models.CharField(max_length=30, choices=SALE_FORCE_CHOICES, blank=True, null=True)
	job = models.CharField(max_length=100)
	status = models.CharField(max_length=20)
	sf_status = models.CharField(max_length=20, blank=True, null=True)
	context = jsonfield.JSONField()

	def __unicode__(self):
		return unicode(self.job)

class ProgramFormNotesFields(models.Model):
	program = models.ForeignKey(Program,related_name='%(class)s_pg')
	notes = RichTextField(verbose_name='Form Notes')

	def __unicode__(self):
		return unicode(self.program)

	class Meta:
		verbose_name = 'Program Form Notes'
		verbose_name_plural = 'Program Form Notes'


class SpecificAdmissionSummary(models.Model):
	specific_program_id = models.ForeignKey(Program,related_name='%(class)s_pg')
	program_code = models.CharField(max_length=6)
	admit_batch = models.CharField(max_length=20)
	admit_sem_cohort = models.PositiveIntegerField()
	application_count = models.PositiveIntegerField(blank=True, null=True)
	full_submission_count = models.PositiveIntegerField(blank=True, null=True)
	offered_count = models.PositiveIntegerField(blank=True, null=True)
	admission_count = models.PositiveIntegerField(blank=True, null=True)
	reject_count = models.PositiveIntegerField(blank=True, null=True)
	last_updated_datetime = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return unicode(self.specific_program_id)


class SpecificAdmissionDataLog(SaleForce):
	specificadmission = models.ForeignKey(SpecificAdmissionSummary,
		related_name='%(class)s_sds', blank=True, null=True)


class SaleForceAuthResponse(models.Model):
	json_resp = jsonfield.JSONField()
	status_code = models.IntegerField(max_length=20)
	created_on = models.DateTimeField(auto_now_add=True)
	updated_on = models.DateTimeField(auto_now=True)
