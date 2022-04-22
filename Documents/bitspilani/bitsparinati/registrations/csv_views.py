from django.contrib.auth.decorators import login_required
from django.views.generic import View, TemplateView
from django.utils.decorators import method_decorator
from django.shortcuts import render
from registrations.models import *
from django.db.models.functions import *
from djqscsv import render_to_csv_response
from django.db.models import *
from django.conf import settings
from django.utils import timezone
import operator
from bits_admin.db_tools import Datediff
import logging
from datetime import datetime
import pytz
from django_countries import countries
from dateutil.parser import parse
logger = logging.getLogger("main")

class BaseRCSV(View):

	def get_choice_display(self, value, choices):
		for k,v in choices: 
			if k==value:return v
		return "Not Found"

	csv_value =['student_application_id','student_id',
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
		'admit_year','current_status',]

	csv_header={'student_application_id':'Application ID','student_id':'Student ID',
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
		}

	def field_serializer_map(self):

		return {
				'created_on_datetime': (lambda x: timezone.localtime(x).strftime("%d -%m-%Y %I:%M %p")),
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

	edu_csv_value =['student_application_id','student_id','current_status',
		'login_email__email',
		'full_name','gender','current_location__location_name',
		'program__program_code',
		'program__program_name',
		'total_work_experience_in_months','admit_year',
		'Category',
		'studentcandidatequalification_requests_created_12__school_college',
		'studentcandidatequalification_requests_created_12__completion_year',
		'studentcandidatequalification_requests_created_12__degree__degree_short_name',
		'studentcandidatequalification_requests_created_12__discipline__discipline_name',
		'studentcandidatequalification_requests_created_12__duration',
		'studentcandidatequalification_requests_created_12__percentage_marks_cgpa',
		'studentcandidatequalification_requests_created_12__division',
		
		]

	edu_csv_value =['application__student_application_id',
		'application__candidateselection_requests_created_5550__student_id',
		'application__application_status',
		'application__login_email__email',
		'application__full_name','application__gender',
		'application__current_location__location_name',
		'application__program__program_code',
		'application__program__program_name',
		'application__total_work_experience_in_months',
		'application__admit_year',
		'degree__qualification_category__category_name',
		'school_college',
		'completion_year',
		'degree__degree_short_name',
		'discipline__discipline_name',
		'duration',
		'percentage_marks_cgpa',
		'division',
		
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
		'application__total_work_experience_in_months':'Total Work Experience',
		'application__admit_year':'Admit Batch',
		'degree__qualification_category__category_name':'Category',	
		'school_college':'Board/University',
		'completion_year':'Year of Passing',
		'degree__degree_short_name':'Degree',	
		'discipline__discipline_name':'Discipline Name',
		'duration':'Duration',
		'percentage_marks_cgpa':'Percentage Marks CGPA',
		'division':'Division',
		
		}

	def edu_field_serializer_map(self):
		return {
			'gender': (lambda x:self.get_choice_display(x,GENDER_CHOICES)),
			'current_employment_status': (lambda x:self.get_choice_display(x,EMPLOYMENTSTATUS_CHOICES)),
			'duration':(lambda x:self.get_choice_display(x,DURATION_CHOICES)),
			'division' : (lambda x:self.get_choice_display(x,DIVISION_CHOICES)),
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
		return {
			'gender': (lambda x:self.get_choice_display(x,GENDER_CHOICES)),
			'current_employment_status': (lambda x:self.get_choice_display(x,EMPLOYMENTSTATUS_CHOICES)),
		}

	def queryset(self):
		query = StudentCandidateApplication.objects.prefetch_related(
			Prefetch('applicationpayment_requests_created_3',
			 queryset=ApplicationPayment.objects.filter(fee_type=1,
			 	application__application_status=settings.APP_STATUS[11][0]),
			 to_attr='adm'),
			).filter(
			application_status__in=[ x[0] for x in settings.APP_STATUS[:12]] + [settings.APP_STATUS[17][0]] + [ x[0] for x in self.app_status]
			)
		query = query.annotate(
			su_comment=F('candidateselection_requests_created_5550__su_rev_com'),
			rev_comment=F('candidateselection_requests_created_5550__es_com'),
			app_id = Case(
				When(candidateselection_requests_created_5550__new_application_id=None, 
					then=Concat('student_application_id',Value(' '))),
				default=Concat('candidateselection_requests_created_5550__new_application_id',Value(' ')),
				output_field=CharField(),
				),
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
				When(application_status=settings.APP_STATUS[11][0], # datetime for admission fees paid.
					then=Max('applicationpayment_requests_created_3__payment_date')
					),
				When(application_status__in=[settings.APP_STATUS[18][0],settings.APP_STATUS[19][0]],
					then=F('pre_selected_rejected_on_datetime'),
					),
				default=None,
				output_field=DateTimeField()
				),
			location=F('current_location__location_name'),
			programName=F('program__program_name'),
			programCode=F('program__program_code'),
			current_status=F('application_status'),
			verified_student_name = F('candidateselection_requests_created_5550__verified_student_name'),
			)
		return query



	def get(self, request, *args, **kwargs):
		logger.info("{0} invoked funct.".format(request.user.email))

		search=request.GET.get("user",None)
		pg1 = request.GET.get('prog',None)
		status = request.GET.get('stat',None)
		pg_type = request.GET.get('pg_type',None)
		adm_bat = request.GET.get('adm_bat',None)
		

		self.query = self.queryset()

		self.query = self.query.filter(program=pg1) if pg1 else self.query
		self.query = self.query.filter(application_status=status) if status else self.query
		self.query = self.query.filter(program__program_type=pg_type) if pg_type else self.query
		self.query = self.query.filter(admit_batch = adm_bat) if adm_bat else self.query
		
		self.query = self.query.filter(
			reduce(operator.and_, (
				Q(full_name__icontains = item)|
				Q(programName__icontains = item)|
				Q(student_application_id__icontains = item)|
				Q(current_status__icontains = item)|
				Q(student_id__icontains = item)|
				Q(created_on_datetime__icontains = item)|
				Q(id__icontains = item)|
				Q(app_id__icontains = item)|
				Q(admit_batch__icontains = item)
				for item in search.split()))
			) if search else self.query 

		

		if 'AppCSV' in request.GET:
			query=self.query.values(*self.csv_value)
			head,ser_map,f_order = self.csv_header,self.field_serializer_map(),self.csv_value 
			filename = 'applicant_data' 

		elif 'EduCSV' in request.GET:
			qual = StudentCandidateQualification.objects.filter(
				application__in=self.query.values_list('pk',flat=True)
				)
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

		return render_to_csv_response(query,append_datestamp=True,
			field_header_map=head,
			field_serializer_map=ser_map ,field_order=f_order,filename=filename,)