from django.contrib.auth.decorators import login_required
from django.views.generic import View, TemplateView
from django.utils.decorators import method_decorator
from django.shortcuts import render
from registrations.models import *
from bits_admin.models import *
from bits_admin.tables import *
from bits_admin.forms import *
from django.db.models.functions import *
from djqscsv import render_to_csv_response
from django.db.models import *
from django.conf import settings
from django.utils import timezone
from .db_tools import Datediff
import logging
import operator
logger = logging.getLogger("main")
from datetime import datetime
import pytz
from django_countries import countries
from django_mysql.models import GroupConcat
from dateutil.parser import parse
import csv
from django.http import HttpResponse
import tablib
import cPickle
from datetime import date
from datetime import  timedelta

class BaseCSVView(View):
	def get_choice_display(self, value, choices):
		for k,v in choices: 
			if k==value:return v
		return "Not Found"

	def display_waiver(self, x):
		email, pg_code = x.split('|')

		eloa=ExceptionListOrgApplicants.objects.filter(
				Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
				employee_email=email.strip(),
				program__program_code=pg_code.strip(),
			).values_list('exception_type',flat=True)

		return ' and '.join(map(lambda x:dict(FEE_TYPE_CHOICE)[x].capitalize(),eloa))

	def get_course_id(self,x,course_no):
		pg,ad_batch = x.split('|')
		try:
			return FirstSemCourseList.objects.filter(program=pg,
				admit_year=ad_batch,active_flag=True)[int(course_no)].course_id
		except Exception as e:
			return ''

	def get_bits_rej_reason(self,x):
		try:
			bits_rej_reason =', '.join(cPickle.loads(str(x)) or [] )
		except cPickle.UnpicklingError: bits_rej_reason = ''
		return bits_rej_reason

	def display_y_m_d(self, pk):
		sca=StudentCandidateApplication.objects.get(pk=pk)
		if sca.program.program_type == 'certification':
			return '%s years' %(sca.total_work_experience_in_months,)

		exp=StudentCandidateWorkExperience.objects.filter(application=sca)
		tmp = sca.last_updated_on_datetime.date() - sca.current_org_employment_date
		for x in exp.iterator():
			tmp += x.end_date - x.start_date
		d = date.fromordinal(tmp.days)
		return '{0} Years {1} Months'.format(d.year-1, d.month-1)



	csv_value = ['student_application_id','student_id',
		'full_name',
		'verified_student_name',
		'login_email__email','program__program_name','date_of_birth','gender','nationality',
		'fathers_name','mothers_name','current_location__location_name','address_line_1','address_line_2',
		'address_line_3','city','pin_code','state','country','phone','mobile','email_id',
		'current_employment_status','current_organization',
		'current_org_employee_number','current_designation',
		'work_location__location_name','current_org_industry__industry_name',
		'current_org_employment_date','fee_payment_owner',
		'total_work_experience_in_months','employer_mentor_flag',
		'employer_consent_flag','math_proficiency_level',
		'prior_student_flag','bits_student_id','parallel_studies_flag',
		'bonafide_flag','created_on_datetime','last_updated',
		'admit_year','current_status','eloa_pg_email',
		'bits_rej_reason','bits_comment','admit_sem_cohort','teaching_mode','pre_selected_flag',
		'pre_selected_rejected_on_datetime','programming_flag','alternate_email_id',]

	csv_header={'student_application_id':'Application ID',
		'student_id':'Student ID',
		'full_name':'Name',
		'verified_student_name':'Verified Student Name',
		'created_on_datetime':'Applied On',
		'login_email__email':'Login Id',
		'current_status':'Current Status',
		'gender':'Gender','address_line_1':'Address Line 1',
		'address_line_2':'Address Line 2',
		'address_line_3':'Address Line 3',
		'city':'City','pin_code':'Pin Code','state':'State','country':'Country',
		'current_organization':'Current Organization',
		'program__program_name':'Program',
		'current_location__location_name':'Current Location',
		'fathers_name':'Fathers Name',
		'mothers_name':'Mothers Name',
		'nationality':'Nationality','phone':'Phone','mobile':'Mobile',
		'current_employment_status':'Current Employment Status',
		'email_id':'Email Id','employer_consent_flag':'Employer Consent Flag',
		'employer_mentor_flag':'Employer Mentor Flag',
		'current_org_employee_number':'Current Org Employee Number',
		'current_designation':'Current Designation',
		'fee_payment_owner':'Fee Payment Owner',
		'current_org_industry__industry_name':'Current Org Industry',
		'current_org_employment_date':'Current Org Employment Date',
		'work_location__location_name':'Work Location',
		'total_work_experience_in_months':'Total Work Experience',
		'math_proficiency_level':'Math Proficiency Level',
		'prior_student_flag':'Prior Student Flag',
		'bits_student_id':'Bits Student Id',
		'parallel_studies_flag':'Parallel Studies Flag',
		'bonafide_flag':'Bonafide Flag',
		'last_updated':'Last Action / Update On',
		'admit_year':'Admit Batch',
		'eloa_pg_email':'Waiver',
		'bits_rej_reason':'BITS Rejection Reason',
		'bits_comment':'BITS Selection / Rejection Comments',
		'admit_sem_cohort': 'Admit Sem Cohort',
		'teaching_mode': 'Teaching Mode',
		'pre_selected_flag': 'Pre Selected Flag',
		'pre_selected_rejected_on_datetime': 'Pre Selected Rejected DateTime',
		'programming_flag': 'Coding Proficiency',
		'alternate_email_id': 'Alternate Email ID'
		}

	def field_serializer_map(self):
		return {
			'created_on_datetime': (lambda x: timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p")),
			'date_of_birth': (lambda x: x.strftime("%d-%m-%Y")),
			'state': (lambda x:self.get_choice_display(x,STATE_CHOICES)),
			'gender': (lambda x:self.get_choice_display(x,GENDER_CHOICES)),
			'nationality': (lambda x:self.get_choice_display(x,NATIONALITY_CHOICES)),
			'current_employment_status': (lambda x:self.get_choice_display(x,EMPLOYMENTSTATUS_CHOICES)),
			'fee_payment_owner':(lambda x:self.get_choice_display(x,FEEPAYMENT_CHOICES)),
			'math_proficiency_level':(lambda x:self.get_choice_display(x,LEVEL_CHOICES)),
			'prior_student_flag':(lambda x:self.get_choice_display(x,PRIOR_CHOICES)),
			'parallel_studies_flag':(lambda x:self.get_choice_display(x,PARALLEL_CHOICES)),
			'eloa_pg_email':(lambda x:self.display_waiver(x)),
			'last_updated': (lambda x: timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p") if x else ''),
			'country': (lambda x: dict(countries).get(x,"")),
			'bits_rej_reason':(lambda x:self.get_bits_rej_reason(x)),
			'pre_selected_rejected_on_datetime': (lambda x: timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p") if x else ''),
			'teaching_mode': (lambda x:self.get_choice_display(x,StudentCandidateApplication.TEACHING_CHOICES)),
			'programming_flag': (lambda x:self.get_choice_display(x,StudentCandidateApplication.PROGRAMMING_FLAG_CHOICES)),
		}

	def field_serializer_map_fee(self): 
		return {
			'application__created_on_datetime': (
				lambda x: timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p")
				),
			'payment_date':(
				lambda x: (x or '') and timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p")
			),}

	edu_csv_value =['application__student_application_id',
		'application__candidateselection_requests_created_5550__student_id',
		'application__application_status',
		'application__login_email__email',
		'application__full_name','application__gender',
		'application__current_location__location_name',
		'application__program__program_code',
		'application__program__program_name',
		'exp_application',
		'application__admit_year',
		'degree__qualification_category__category_name',
		'school_college',
		'completion_year',
		'degree__degree_short_name',
		'discipline__discipline_name',
		'duration',
		'percentage_marks_cgpa',
		'division',
		'application__current_employment_status',
		'application__current_organization',
		'application__current_designation',
		'application__current_org_industry__industry_name',
		'application__fee_payment_owner',
		'application__math_proficiency_level',
		
		]

	edu_csv_header={'application__student_application_id':'Application ID',
		'application__candidateselection_requests_created_5550__student_id':'Student ID',
		'application__application_status':'Current Status',
		'application__login_email__email':'Login Id',
		'application__full_name':'Name',
		'application__gender':'Gender',
		'application__current_location__location_name':'Current Location',
		'application__program__program_code':'Program Code',
		'application__program__program_name':'Program',
		'exp_application':'Total Work Experience',
		'application__admit_year':'Admit Batch',
		'degree__qualification_category__category_name':'Category',	
		'school_college':'Board/University',
		'completion_year':'Year of Passing',
		'degree__degree_short_name':'Degree',	
		'discipline__discipline_name':'Discipline Name',
		'duration':'Duration',
		'percentage_marks_cgpa':'Percentage Marks CGPA',
		'division':'Division',
		'application__current_employment_status':'Current Employment Status',
		'application__current_organization':'Current Organization',
		'application__current_designation': 'Current Designation',
		'application__current_org_industry__industry_name':'Current Org Industry',
		'application__fee_payment_owner': 'Fee Payment Owner',
		'application__math_proficiency_level':'Math Proficiency Level',
		}

	def edu_field_serializer_map(self):
		return {
			'application__gender': (lambda x:self.get_choice_display(x,GENDER_CHOICES)),
			'duration':(lambda x:self.get_choice_display(x,DURATION_CHOICES)),
			'division' : (lambda x:self.get_choice_display(x,DIVISION_CHOICES)),
			'application__current_employment_status': (lambda x:self.get_choice_display(x,EMPLOYMENTSTATUS_CHOICES)),
			'application__fee_payment_owner':(lambda x:self.get_choice_display(x,FEEPAYMENT_CHOICES)),
			'application__math_proficiency_level':(lambda x:self.get_choice_display(x,LEVEL_CHOICES)),
			'exp_application': (lambda x:self.display_y_m_d(x))
			}

	wexp_csv_value =['application__student_application_id',
		'application__candidateselection_requests_created_5550__student_id',
		'application__application_status',
		'application__login_email__email',
		'application__full_name',
		'application__gender',
		'application__current_location__location_name',
		'application__program__program_code',
		'application__program__program_name',
		'application__total_work_experience_in_months',
		'application__admit_year',
		'organization',
		'start_date',
		'end_date',
		'designations',
		'Duration',
		]

	wexp_csv_header={'application__student_application_id':'Application ID',
		'application__candidateselection_requests_created_5550__student_id':'Student ID',
		'application__application_status':'Current Status',
		'application__login_email__email':'Login Id',
		'application__full_name':'Name',
		'application__gender':'Gender',
		'application__current_location__location_name':'Current Location',
		'application__program__program_code':'Program Code',
		'application__program__program_name':'Program',
		'application__total_work_experience_in_months':'Total Work Experience',
		'application__admit_year':'Admit Batch',
		'organization':'Organization',
		'start_date':'Start Date',
		'end_date':'End Date',
		'designations':'Designation',
		'Duration':'Duration',
		}

	def wexp_field_serializer_map(self):
		return {'application__gender': (lambda x:self.get_choice_display(x,GENDER_CHOICES)),
			'current_employment_status': (lambda x:self.get_choice_display(x,EMPLOYMENTSTATUS_CHOICES)),
			}


	mhr_csv_value =['student_application_id',
		'login_email__email',
		'full_name','current_status',
		'program__program_code',
		'program__program_name',
		'candidateselection_requests_created_5550__new_application_id',
		'candidateselection_requests_created_5550__m_name',
		'candidateselection_requests_created_5550__m_des',
		'candidateselection_requests_created_5550__m_mob_no',
		'candidateselection_requests_created_5550__m_email',
		'candidateselection_requests_created_5550__hr_cont_name',
		'candidateselection_requests_created_5550__hr_cont_des',
		'candidateselection_requests_created_5550__hr_cont_mob_no',
		'candidateselection_requests_created_5550__hr_cont_email',
		'created_on_datetime',
		]

	mhr_csv_header={'student_application_id':'Application ID',
			'login_email__email':'Login Id',
			'full_name':'Name',
			'current_status':'Current Status',
			'program__program_code':'Program Code',
			'program__program_name':'Program',
			'candidateselection_requests_created_5550__new_application_id':'New Application ID',
			'candidateselection_requests_created_5550__m_name':'Mentor Name',
			'candidateselection_requests_created_5550__m_des':'Mentor Designation',
			'candidateselection_requests_created_5550__m_mob_no':'Mentor Mobile Number',
			'candidateselection_requests_created_5550__m_email':'Mentor Email',
			'candidateselection_requests_created_5550__hr_cont_name':'HR Contact Name',
			'candidateselection_requests_created_5550__hr_cont_des':'HR Contact Designation',
			'candidateselection_requests_created_5550__hr_cont_mob_no':'HR Contact Mobile Number',
			'candidateselection_requests_created_5550__hr_cont_email':'HR Contact Email',
			'created_on_datetime':'Applied On',
			}

	def mhr_field_serializer_map(self):
		return {
			'created_on_datetime': (
				lambda x: (x or '') and timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p")
			),
		}

	#Taxila User Data Extract
	tax_usr_csv_value =['user_name',
		'full_name',
		'last_name_csv',
		'email_csv',
		'auth',
		'student_id',
		'city',
		'institution',
		]

	tax_usr_csv_header={'user_name':'username',
		'full_name':'firstname',
		'last_name_csv':'lastname',
		'email_csv':'email',
		'auth':'auth',
		'student_id':'idnumber',
		'city':'city',
		'institution':'institution',
		}

	#Taxila Course Data
	tax_cour_csv_value =['user_name',
		'full_name',
		'last_name_csv',
		'email_csv',
		'course1',
		'role1',
		'course2',
		'role2',
		'course3',
		'role3',
		'course4',
		'role4',
		]

	tax_cour_csv_header={'user_name':'Username',
		'full_name':'firstname',
		'last_name_csv':'lastname',
		'email_csv':'email',
		'course1': 'course1',
		'role1':'role1',
		'course2': 'course2',
		'role2':'role2',
		'course3': 'course3',
		'role3':'role3',
		'course4': 'course4',
		'role4':'role4',
		}

	def tax_cour_field_serializer_map(self):
		return {
			'course1': (lambda x:self.get_course_id(x,'0')),
			'course2': (lambda x:self.get_course_id(x,'1')),
			'course3': (lambda x:self.get_course_id(x,'2')),
			'course4': (lambda x:self.get_course_id(x,'3')),
			}

	#Mail User Data Extract
	mail_usr_csv_value =['user_name',
		'full_name',
		'last_name_csv',
		'date_of_birth',
		]

	mail_usr_csv_header={'user_name':'username',
		'full_name':'firstname',
		'last_name_csv':'lastname',
		'date_of_birth':'password',
		}

	def mail_usr_field_serializer_map(self):
		return {
			'date_of_birth': (lambda x: x.strftime("%d%m%Y*")),
			# added '=' before because single digit day was not displaying leading zeros.
			}

	#DMS Data Extract
	dms_csv_value =['student_application_id',
		'student_id',
		'full_name','current_designation',
		'date_of_birth',
		'gender',
		'location',
		'address_line_1',
		'address_line_2',
		'address_line_3',
		'city',
		'state',
		'pin_code',
		'country',
		'phone',
		'mobile',
		'email_id',
		'current_organization',
		'current_location__location_name',
		'current_employment_status',
		'programName',
		'admit_year',
		]

	dms_csv_header={'student_application_id':'AP_NO',
			'student_id':'ID_NO',
			'full_name':'STUD_NAME',
			'current_designation':'DESIG',
			'date_of_birth':'DOB',
			'gender':'SEX',
			'location':'LOCATIION',
			'address_line_1':'POST_ADD1',
			'address_line_2':'POST_ADD2',
			'address_line_3':'POST_ADD3',
			'city':'POST_CITY',
			'state':'POST_STATE',
			'pin_code':'POST_PIN',
			'country':'COUNTRY',
			'phone':'PHONE_OFF',
			'mobile':'MOBILE_NO',
			'email_id':'EMAIL_ADD',
			'current_organization':'EMP_ORG',
			'current_location__location_name':'EXAM_CENT',
			'current_employment_status':'EMPL_STAT',
			'programName':'DEGREE',
			'admit_year':'SEM_ADM',

			}

	def dms_field_serializer_map(self):
		return {
			'date_of_birth': (lambda x: x.strftime("%d-%m-%Y")),
			'gender': (lambda x:self.get_choice_display(x,GENDER_CHOICES)),
			'current_employment_status': (lambda x:self.get_choice_display(x,EMPLOYMENTSTATUS_CHOICES)),
			'state': (lambda x:self.get_choice_display(x,STATE_CHOICES)),
			'country': (lambda x: dict(countries).get(x,"")),
			}

	#Portal User Data Extract	
	portal_csv_value =['student_id',
		'user_name',
		'full_name',
		'date_of_birth',
		'gender','address',
		'city',
		'pin_code',
		'state','country',
		'mobile',
		'email_id',
		'role',
		]

	portal_csv_header={'student_id':'id',
		'user_name':'username',
		'full_name':'full_name',
		'date_of_birth':'dob',
		'gender':'gender',
		'address':'address',
		'city':'city',
		'pin_code':'pincode',
		'state':'state',
		'country':'country',
		'mobile':'phone',
		'email_id':'email',
		'role':'role',
		}

	def portal_field_serializer_map(self):
		return {
			'date_of_birth': (lambda x: x.strftime("%d-%m-%Y")),
			'state': (lambda x:self.get_choice_display(x,STATE_CHOICES)),
			'gender': (lambda x:self.get_choice_display(x,GENDER_CHOICES)),
			'country': (lambda x: dict(countries).get(x,"")),
			}

	def queryset(self):
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
			location=F('current_location__location_name'),
			programType=F('program__program_type'),			
			programName=F('program__program_name'),
			current_status=F('application_status'),
			student_id = F('candidateselection_requests_created_5550__student_id'),
			verified_student_name = F('candidateselection_requests_created_5550__verified_student_name'),
			eloa_pg_email = Concat('login_email__email', Value(' | '), 'program__program_code'),
			internal_pg=Case(
				When(candidateselection_requests_created_5550__admitted_to_program__isnull=False, 
					then=F('candidateselection_requests_created_5550__admitted_to_program')),
				When(candidateselection_requests_created_5550__new_sel_prog__isnull=False, 
					then=F('candidateselection_requests_created_5550__new_sel_prog')),				
				default=F('program')
					),
			last_name_csv=Value("-",output_field=CharField()), #added '=' before beacuse . was invisible in csv
			bits_rej_reason = F('candidateselection_requests_created_5550__bits_rejection_reason'),
			bits_comment = F('candidateselection_requests_created_5550__selection_rejection_comments'),
			last_updated = Case(
				When(application_status__in=[settings.APP_STATUS[0][0],
					settings.APP_STATUS[4][0],settings.APP_STATUS[14][0]], 
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
					settings.APP_STATUS[3][0],settings.APP_STATUS[12][0], settings.APP_STATUS[17][0]],
					then=F('last_updated_on_datetime'),
					),
				When(Q(application_status=settings.APP_STATUS[13][0],
						applicationpayment_requests_created_3__fee_type='2'), #datetime for application fees paid.
					then=Min('applicationpayment_requests_created_3__payment_date')
					),
				When(application_status=settings.APP_STATUS[11][0], # datetime for admission fees paid.
					then=Max('applicationpayment_requests_created_3__payment_date')
					),
				When(application_status__in=[settings.APP_STATUS[18][0],settings.APP_STATUS[19][0]],
					then=F('pre_selected_rejected_on_datetime'),
					),
				default=None,
				output_field=DateTimeField()
				),
		).order_by('-last_updated')
		return query

	def get(self, request, *args, **kwargs):
		logger.info("{0} invoked funct.".format(request.user.email))
		
		from_date=request.GET.get("fromDate", None)
		to_date=request.GET.get("toDate", None)
		search=request.GET.get("user",'')

		if to_date:
			t = to_date.split('-')
			to_date = dt( int(t[2]), int(t[1]), int(t[0]), 23, 59, 59 )

		if from_date:
			t = from_date.split('-')
			from_date = dt( int(t[2]), int(t[1]), int(t[0]), 00, 00, 00 )

		self.query = self.queryset()

		self.query = self.query.filter(
				reduce(operator.and_, (
					Q(login_email__email__icontains = item)|
					Q(full_name__icontains = item)|
					Q(admit_batch__icontains = item)|
					Q(location__icontains = item)|
					Q(programName__icontains = item)|
					Q(program__program_code__icontains = item)|
					Q(student_application_id__icontains = item)|
					Q(current_status__icontains = item)|
					Q(created_on_datetime__icontains = item)|
					Q(candidateselection_requests_created_5550__student_id__icontains = item)
					for item in search.split())) 
				) if search else self.query
				
		if from_date and to_date :
			self.query = self.query.filter( created_on_datetime__range = [from_date,to_date])
		elif from_date :
			self.query = self.query.filter( created_on_datetime__gte = from_date)
		elif to_date :
			self.query = self.query.filter( created_on_datetime__lte = to_date)

		pg1 = request.GET.get('prog',None)
		self.query = self.query.filter(program=pg1) if pg1 else self.query

		status = request.GET.get('stat',None)
		self.query = self.query.filter(application_status=status) if status else self.query

		pg_type = request.GET.get('pg_type',None)
		self.query = self.query.filter(program__program_type=pg_type) if pg_type else self.query

		admit_batch = request.GET.get('admit_batch',None)
		self.query = self.query.filter(admit_batch=admit_batch) if admit_batch else self.query

		if 'AppCSV' in request.GET:
			query = self.query.values(*self.csv_value)
			head,ser_map,f_order = self.csv_header,self.field_serializer_map(),self.csv_value	
			filename = 'applicant_data'
		elif 'EduCSV' in request.GET:
			qual = StudentCandidateQualification.objects.filter(
				application__in=self.query.values_list('pk',flat=True)
				).annotate(exp_application=F('application'))
			query = qual.values(*self.edu_csv_value)
			head,ser_map,f_order = self.edu_csv_header,self.edu_field_serializer_map(),self.edu_csv_value
			filename = 'education_data'

		elif 'WExpCSV' in request.GET:
			qual = StudentCandidateWorkExperience.objects.filter(
				application__in=self.query.values_list('pk',flat=True)
				).annotate( Duration =  Datediff('end_date','start_date', interval='days')
				)
			query = qual.values(*self.wexp_csv_value)	
			head,ser_map,f_order = self.wexp_csv_header,self.wexp_field_serializer_map(),self.wexp_csv_value
			filename = 'work_experience_data'

		elif 'MHrCSV' in request.GET:
			query = self.query.filter(application_status__in=[
				settings.APP_STATUS[9][0],
				settings.APP_STATUS[11][0],
				],
				program__mentor_id_req=True,
				program__hr_cont_req=True)
			query=query.values(*self.mhr_csv_value)
			head,ser_map,f_order = self.mhr_csv_header,self.mhr_field_serializer_map(),self.mhr_csv_value
			filename = 'mentor_hr_data'

		#Taxila User Data Extract
		elif 'TaxUsrCSV' in request.GET:
			query = self.query.exclude(Q(student_id__isnull=True)|Q(student_id=''))
			query = query.annotate(
				user_name = Concat('student_id',Value('@wilp.bits-pilani.ac.in')),
				email_csv = Concat('student_id',Value('@wilp.bits-pilani.ac.in')),
				auth=Value('Shibboleth',output_field=CharField()),
				institution=Value('BITS-PILANI',output_field=CharField()),
				)
			query=query.values(*self.tax_usr_csv_value)
			head,ser_map,f_order = self.tax_usr_csv_header,dict(),self.tax_usr_csv_value
			filename = 'taxila_user_data_extract'

		#Taxila Course Data
		elif 'TaxCourCSV' in request.GET:
			query = self.query.exclude(Q(student_id__isnull=True)|Q(student_id=''))
			query = query.annotate(
			course1= Concat('internal_pg',Value('|'),'admit_year',
				output_field=CharField()),
			course2=Concat('internal_pg',Value('|'),'admit_year',
				output_field=CharField()),
			course3=Concat('internal_pg',Value('|'),'admit_year',
				output_field=CharField()),
			course4=Concat('internal_pg',Value('|'),'admit_year',
				output_field=CharField()),
			role1=Value('student',output_field=CharField()),
			role2=Value('student',output_field=CharField()),
			role3=Value('student',output_field=CharField()),
			role4=Value('student',output_field=CharField()),
			user_name = Concat('student_id',Value('@wilp.bits-pilani.ac.in')),
			email_csv = Concat('student_id',Value('@wilp.bits-pilani.ac.in')),
			)
			query = query.values(*self.tax_cour_csv_value)
			head,ser_map,f_order = self.tax_cour_csv_header,self.tax_cour_field_serializer_map(),self.tax_cour_csv_value
			filename = 'taxila_course_data'

		#Mail User Data Extract
		elif 'MailUsrCSV' in request.GET:
			query = self.query.exclude(Q(student_id__isnull=True)|Q(student_id=''))
			query = query.annotate(
				user_name = Concat('student_id',Value('@wilp.bits-pilani.ac.in')),
				)
			query = query.values(*self.mail_usr_csv_value)
			head,ser_map,f_order = self.mail_usr_csv_header,self.mail_usr_field_serializer_map(),self.mail_usr_csv_value
			filename = 'mail_user_data_extract'

		#DMS Data Extract
		elif 'DmsDataCSV' in request.GET:
			query = self.query.exclude(Q(student_id__isnull=True)|Q(student_id=''))
			query = query.values(*self.dms_csv_value)
			head,ser_map,f_order = self.dms_csv_header,self.dms_field_serializer_map(),self.dms_csv_value
			filename = 'dms_data_extract'

		#Portal User Data Extract
		elif 'PUsrCSV' in request.GET:
			query = self.query.exclude(Q(student_id__isnull=True)|Q(student_id=''))
			query = query.annotate(
				address = Concat('address_line_1', Value(' '), 'address_line_2',Value(' '), 'address_line_3'),
				role=Value('student',output_field=CharField()),
				user_name = Concat('student_id',Value('@wilp.bits-pilani.ac.in')),
				)
			query = query.values(*self.portal_csv_value)
			head,ser_map,f_order = self.portal_csv_header,self.portal_field_serializer_map(),self.portal_csv_value
			filename = 'portal_user_data_extract'

		return render_to_csv_response(query,append_datestamp=True,
			field_header_map=head,
			field_serializer_map=ser_map ,
			field_order=f_order,filename=filename,)

class BaseCSVArchiveView(View):
	

	csv_value = ['student_application_id','student_id',
		'full_name',
		'verified_student_name',
		'login_email','program__program_name','date_of_birth','gender','nationality',
		'fathers_name','mothers_name','current_location','address_line_1','address_line_2',
		'address_line_3','city','pin_code','state','country','phone','mobile','email_id',
		'current_employment_status','current_organization',
		'current_org_employee_number','current_designation',
		'work_location','current_org_industry',
		'current_org_employment_date','fee_payment_owner',
		'total_work_experience_in_months','employer_mentor_flag',
		'employer_consent_flag','math_proficiency_level',
		'prior_student_flag','bits_student_id','parallel_studies_flag',
		'bonafide_flag','created_on_datetime',
		'admit_year','application_status',]

	csv_header={'student_application_id':'Application ID',
		'student_id':'Student ID',
		'full_name':'Name',
		'verified_student_name':'Verified Student Name',
		'login_email':'Login Id',
		'program__program_name':'Program',
		'date_of_birth':'Date Of Birth',
		'gender':'Gender','nationality':'Nationality',
		'fathers_name':'Fathers Name',
		'mothers_name':'Mothers Name',
		'current_location':'Current Location',
		'address_line_1':'Address Line 1',
		'address_line_2':'Address Line 2',
		'address_line_3':'Address Line 3',
		'city':'City','pin_code':'Pin Code','state':'State','country':'Country',
		'phone':'Phone','mobile':'Mobile',
		'email_id':'Email Id',
		'current_employment_status':'Current Employment Status',
		'current_organization':'Current Organization',
		'current_org_employee_number':'Current Org Employee Number',
		'current_designation':'Current Designation',
		'work_location':'Work Location',
		'current_org_industry':'Current Org Industry',
		'current_org_employment_date':'Current Org Employment Date',
		'fee_payment_owner':'Fee Payment Owner',
		'total_work_experience_in_months':'Total Work Experience',
		'employer_mentor_flag':'Employer Mentor Flag',
		'employer_consent_flag':'Employer Consent Flag',
		'math_proficiency_level':'Math Proficiency Level',
		'prior_student_flag':'Prior Student Flag',
		'bits_student_id':'Bits Student Id',
		'parallel_studies_flag':'Parallel Studies Flag',
		'bonafide_flag':'Bonafide Flag',
		'created_on_datetime':'Applied On',
		'admit_year':'Admit Batch',
		'application_status':'Current Status',
		}

	def field_serializer_map(self):
		return {
			'created_on_datetime': (lambda x: timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p")),
			'date_of_birth': (lambda x: x.strftime("%d-%m-%Y")),
			'state': (lambda x:self.get_choice_display(x,STATE_CHOICES)),
			'gender': (lambda x:self.get_choice_display(x,GENDER_CHOICES)),
			'nationality': (lambda x:self.get_choice_display(x,NATIONALITY_CHOICES)),
			'current_employment_status': (lambda x:self.get_choice_display(x,EMPLOYMENTSTATUS_CHOICES)),
			'fee_payment_owner':(lambda x:self.get_choice_display(x,FEEPAYMENT_CHOICES)),
			'math_proficiency_level':(lambda x:self.get_choice_display(x,LEVEL_CHOICES)),
			'prior_student_flag':(lambda x:self.get_choice_display(x,PRIOR_CHOICES)),
			'parallel_studies_flag':(lambda x:self.get_choice_display(x,PARALLEL_CHOICES)),
			'last_updated': (lambda x: timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p") if x else ''),
			'country': (lambda x: dict(countries).get(x,"")),

		}

	edu_csv_value =['application__student_application_id',
		'application__candidateselectionarchived_1__student_id',
		'application__application_status',
		'application__login_email',
		'application__full_name','application__gender',
		'application__current_location',
		'application__program__program_code',
		'application__program__program_name',
		'application__total_work_experience_in_months',
		'application__admit_year',
		'degree__qualification_category',
		'school_college',
		'completion_year',
		'degree__degree_short_name',
		'discipline',
		'duration',
		'percentage_marks_cgpa',
		'division',
		
		]

	edu_csv_header={'application__student_application_id':'Application ID',
		'application__candidateselectionarchived_1__student_id':'Student ID',
		'application__application_status':'Current Status',
		'application__login_email':'Login Id',
		'application__full_name':'Name',
		'application__gender':'Gender',
		'application__current_location':'Current Location',
		'application__program__program_code':'Program Code',
		'application__program__program_name':'Program',
		'application__total_work_experience_in_months':'Total Work Experience',
		'application__admit_year':'Admit Batch',
		'degree__qualification_category':'Category',#doubt	
		'school_college':'Board/University',
		'completion_year':'Year of Passing',
		'degree__degree_short_name':'Degree',	
		'discipline':'Discipline Name',
		'duration':'Duration',
		'percentage_marks_cgpa':'Percentage Marks CGPA',
		'division':'Division',
		
		}

	def edu_field_serializer_map(self):
		return {
			'application__gender': (lambda x:self.get_choice_display(x,GENDER_CHOICES)),
			'duration':(lambda x:self.get_choice_display(x,DURATION_CHOICES)),
			'division' : (lambda x:self.get_choice_display(x,DIVISION_CHOICES)),
			}

	wexp_csv_value =['application__student_application_id',
		'application__candidateselectionarchived_1__student_id',
		'application__application_status',
		'application__login_email',
		'application__full_name',
		'application__gender',
		'application__current_location',
		'application__program__program_code',
		'application__program__program_name',
		'application__total_work_experience_in_months',
		'application__admit_year',
		'organization',
		'start_date',
		'end_date',
		'designations',
		'Duration',
		]

	wexp_csv_header={'application__student_application_id':'Application ID',
		'application__candidateselectionarchived_1__student_id':'Student ID',
		'application__application_status':'Current Status',
		'application__login_email':'Login Id',
		'application__full_name':'Name',
		'application__gender':'Gender',
		'application__current_location':'Current Location',
		'application__program__program_code':'Program Code',
		'application__program__program_name':'Program',
		'application__total_work_experience_in_months':'Total Work Experience',
		'application__admit_year':'Admit Batch',
		'organization':'Organization',
		'start_date':'Start Date',
		'end_date':'End Date',
		'designations':'Designation',
		'Duration':'Duration',
		}

	def wexp_field_serializer_map(self):
		return {'application__gender': (lambda x:self.get_choice_display(x,GENDER_CHOICES)),
			'current_employment_status': (lambda x:self.get_choice_display(x,EMPLOYMENTSTATUS_CHOICES)),
			}

	mhr_csv_value =['student_application_id',
		'login_email',
		'full_name','application_status',
		'program__program_code',
		'program__program_name',
		'candidateselectionarchived_1__new_application_id',
		'candidateselectionarchived_1__m_name',
		'candidateselectionarchived_1__m_des',
		'candidateselectionarchived_1__m_mob_no',
		'candidateselectionarchived_1__m_email',
		'candidateselectionarchived_1__hr_cont_name',
		'candidateselectionarchived_1__hr_cont_des',
		'candidateselectionarchived_1__hr_cont_mob_no',
		'candidateselectionarchived_1__hr_cont_email',
		'created_on_datetime',
		]

	mhr_csv_header={'student_application_id':'Application ID',
			'login_email':'Login Id',
			'full_name':'Name',
			'application_status':'Current Status',
			'program__program_code':'Program Code',
			'program__program_name':'Program',
			'candidateselectionarchived_1__new_application_id':'New Application ID',
			'candidateselectionarchived_1__m_name':'Mentor Name',
			'candidateselectionarchived_1__m_des':'Mentor Designation',
			'candidateselectionarchived_1__m_mob_no':'Mentor Mobile Number',
			'candidateselectionarchived_1__m_email':'Mentor Email',
			'candidateselectionarchived_1__hr_cont_name':'HR Contact Name',
			'candidateselectionarchived_1__hr_cont_des':'HR Contact Designation',
			'candidateselectionarchived_1__hr_cont_mob_no':'HR Contact Mobile Number',
			'candidateselectionarchived_1__hr_cont_email':'HR Contact Email',
			'created_on_datetime':'Applied On',
			}

	def mhr_field_serializer_map(self):
		return {
			'created_on_datetime': (
				lambda x: (x or '') and timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p")
			),
		}


	def get_choice_display(self, value, choices):
		for k,v in choices: 
			if k==value:return v
		return "Not Found"

	def queryset(self):
		query = StudentCandidateApplicationArchived.objects.annotate(
			programName=F('program__program_name'),
			student_id = F('candidateselectionarchived_1__student_id'),
			verified_student_name = F('candidateselectionarchived_1__verified_student_name'),
			)
		return query

	def get(self, request, *args, **kwargs):

		self.query = self.queryset()
		from_date=request.GET.get("fromDate",None)
		to_date=request.GET.get("toDate",None)
		search=request.GET.get("user",'')
		pg_type = request.GET.get('pgType',None)
		pg1 = request.GET.get('prog',None)
		status = request.GET.get('stat',None)
		admit_batch = request.GET.get('admit_batch',None)
		if to_date:
			t = to_date.split('-')
			to_date = dt( int(t[2]), int(t[1]), int(t[0]), 23, 59, 59 )
		if from_date:
			t = from_date.split('-')
			from_date = dt( int(t[2]), int(t[1]), int(t[0]), 00, 00, 00 )

		if from_date and to_date :
			self.query = self.query.filter( created_on_datetime__range = [from_date,to_date])
		elif from_date :
			self.query = self.query.filter( created_on_datetime__gte = from_date)
		elif to_date :
			self.query = self.query.filter( created_on_datetime__lte = to_date)

		self.query = self.query.filter(program__program_type=pg_type) if pg_type else self.query
		self.query = self.query.filter(program=pg1) if pg1 else self.query
		self.query = self.query.filter(application_status=status) if status else self.query
		self.query = self.query.filter(admit_batch=admit_batch) if admit_batch else self.query

		self.query = self.query.filter(
			reduce(operator.and_, (
				Q(run__icontains = x )|
				Q(full_name__icontains = x )|
				Q(created_on_datetime__icontains = x )|
				Q(last_updated_on_datetime__icontains = x )|
				Q(current_location__icontains = x )|
				Q(programName__icontains = x)|
				Q(program__program_code__icontains = x)|
				Q(login_email__icontains = x )|
				Q(application_status__icontains = x )|
				Q(admit_batch__icontains = x )|
				Q(application_status__icontains = x )|
				Q(student_application_id__icontains = x )|
				Q(student_id__icontains = x)
				for x in search.split()
				)
			)) if search else self.query#.none()


		if 'AppCSV' in request.GET:
			query = self.query.values(*self.csv_value)
			head,ser_map,f_order = self.csv_header,self.field_serializer_map(),self.csv_value
			filename = 'applicant_archive_data'

		elif 'EduCSV' in request.GET:
			qual = StudentCandidateQualificationArchived.objects.filter(
				application__in=self.query.values_list('pk',flat=True)
				)
			query = qual.values(*self.edu_csv_value)
			head,ser_map,f_order = self.edu_csv_header,self.edu_field_serializer_map(),self.edu_csv_value
			filename = 'education_archive_data'

		elif 'WExpCSV' in request.GET:
			qual = StudentCandidateWorkExperienceArchived.objects.filter(
				application__in=self.query.values_list('pk',flat=True)
				).annotate( Duration =  Datediff('end_date','start_date', interval='days')
				)
			query = qual.values(*self.wexp_csv_value)	
			head,ser_map,f_order = self.wexp_csv_header,self.wexp_field_serializer_map(),self.wexp_csv_value
			filename = 'work_experience_archive_data'

		elif 'MHrCSV' in request.GET:
			self.query = self.query.filter(application_status__in=[
				settings.APP_STATUS[9][0],
				settings.APP_STATUS[11][0],
				],
				program__mentor_id_req=True,
				program__hr_cont_req=True)

			query=self.query.values(*self.mhr_csv_value)
			head,ser_map,f_order = self.mhr_csv_header,self.mhr_field_serializer_map(),self.mhr_csv_value
			filename = 'mentor_hr_archive_data'

		return render_to_csv_response(query,append_datestamp=True,
			field_header_map=head,
			field_serializer_map=ser_map ,
			field_order=f_order,filename=filename,)
