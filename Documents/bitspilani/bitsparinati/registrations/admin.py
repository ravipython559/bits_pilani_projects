from django.contrib import admin
from daterange_filter.filter import DateRangeFilter
from django.core.urlresolvers import reverse
from django.contrib.admin.views.main import ChangeList
from django.shortcuts import (get_object_or_404,render,
	redirect,render_to_response,HttpResponseRedirect)
from .models import *
from .forms import *
from .extra_forms import *
from django.conf.urls import url
from django.db.models.functions import *
from django.db.models import *
from django.template.response import TemplateResponse
from import_export import resources
from import_export.admin import ImportExportModelAdmin, ImportExportActionModelAdmin,base_formats
from django.contrib.auth.models import User
from import_export.admin import ImportMixin,ImportExportMixin
from import_export import resources, fields as i_e_fields, widgets as widg
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from uuid import uuid4
from django.contrib.auth.hashers import make_password
from django.utils.translation import ugettext_lazy as _
from django.utils.html import escape
import operator

# Register your models here.

def user_unicode(self):
	return  u'%s' % (self.email)

User.__unicode__ = user_unicode
User._meta.get_field('email').__dict__['_unique'] = True
admin.site.unregister(User)
#admin.site.register(User)

class UserAdmin(admin.ModelAdmin):
	search_fields = ('email',)
admin.site.register(User,UserAdmin)

class AdminDegree(admin.ModelAdmin):
	list_per_page = 15
	list_display =('degree_short_name','degree_long_name','qualification_category',)
admin.site.register(Degree, AdminDegree)

class AdminBitsRejectionReason(admin.ModelAdmin):
	list_per_page = 15
	list_display =('reason',)
admin.site.register(BitsRejectionReason, AdminBitsRejectionReason)

class AdminApplicantRejectionReason(admin.ModelAdmin):
	list_per_page = 15
	list_display =('reason',)
admin.site.register(ApplicantRejectionReason, AdminApplicantRejectionReason)

class AdminApplicantionDocumentReason(admin.ModelAdmin):
	list_per_page = 15
	list_display =('reason',)
admin.site.register(ApplicantionDocumentReason, AdminApplicantionDocumentReason)

class AdminDiscpline(admin.ModelAdmin):
	list_per_page = 15
	list_display =('discipline_name','discipline_long_name',)
admin.site.register(Discpline, AdminDiscpline)

class AdminDocumentType(admin.ModelAdmin):
	list_per_page = 15
	list_display =('document_name','mandatory_document','n_v_flag')
admin.site.register(DocumentType, AdminDocumentType)

class AdminIndustry(admin.ModelAdmin):
	list_per_page = 15
	list_display =('industry_name',)
admin.site.register(Industry, AdminIndustry)

class AdminLocation(admin.ModelAdmin):
	list_per_page = 15
	list_display =('location_name','is_exam_location',)
admin.site.register(Location, AdminLocation)

class AdminProgramFeesAdmission(admin.ModelAdmin):
	form = ProgramFeesAdmissionForm

	list_per_page = 15
	fields=('admit_year','program','latest_fee_amount_flag',
		'fee_amount','fee_type','fee_expiry','stud_id_gen_st_num',
		'admit_sem_des', 'admit_sem_cohort', 
		'is_paytm_enable',
		)
	list_display =('admit_year','program',
		'latest_fee_amount_flag','sequence_number','admit_sem_des',
		'fee_amount','fee_type','fee_expiry','stud_id_gen_st_num')
	search_fields = ['program__program_name', 'program__program_code', 'fee_type', 'admit_sem_des',]


	def get_search_results(self, request, queryset, search_term):
		queryset, use_distinct = super(AdminProgramFeesAdmission, self).get_search_results(request, queryset, search_term)
		search_fields = self.get_search_fields(request)
		if search_fields and search_term:
	
			fee_choices = lambda : [When(fee_type=Value(k),then=Value(v)) for (k,v) in FEE_TYPE_CHOICES ]

			local_queryset = self.model.objects.annotate(annotated_fee_type = Case(*fee_choices(), 
				default = Value(''), 
				output_field = CharField())
			)

			local_queryset = local_queryset.filter(reduce(operator.and_, 
				[Q(annotated_fee_type__icontains=x) for x in search_term.upper().strip().split()]))
			queryset |= self.model.objects.filter(pk__in=local_queryset.values_list('pk', flat=True))

		return queryset, use_distinct
	
admin.site.register(PROGRAM_FEES_ADMISSION, AdminProgramFeesAdmission)

class AdminElectiveCourseList(ImportMixin,admin.ModelAdmin):
	form = AdminElectiveCourseListForm
	formats=(base_formats.CSV,)
	resource_class = ElectiveCourseListResource
	list_per_page = 25
	list_display =('program','course_id',
				   'course_name','course_units',
				   'course_id_slot','is_active',
		)
	search_fields = ['program__program_code','program__program_name','course_id','course_name','course_id_slot__course_id',]

admin.site.register(ElectiveCourseList,AdminElectiveCourseList)

class AdminProgram(admin.ModelAdmin):
	form = ProgramForm
	list_per_page = 25
	list_display =('program_code','program_name',
		'form_title',
		'program_type','active_for_applicaton_flag',
		'document_submission_flag',
		'show_on_page_flag','serial_number_on_page',
		'show_to_fee_wvr_appl_flag',
		'application_pdf_template',
		'offer_letter_template',
		'collaborating_organization',
		'org_logo_image','document_upload_page_path_choice',
		'min_work_exp_in_months',
		'hr_cont_req',
		'mentor_id_req',
		'zest',
		'propelld',
	)
	search_fields = ['program_name','program_code','program_type']
	def document_upload_page_path_choice(self, profile):
		path = profile.document_upload_page_path
		return '-' if not path else path
			
admin.site.register(Program, AdminProgram)
 
class AdminInstruction(admin.ModelAdmin):
	list_display=('text',)

	def has_add_permission(self, request):
		return False
	def has_delete_permission(self, request,obj=None):
		return False

	def get_actions(self, request):
		actions = super(AdminInstruction, self).get_actions(request)
		del actions['delete_selected']
		return actions

	def response_change(self, request, obj):
		if not '_continue' in request.POST:
			return redirect(reverse('registrationForm:bits-login-admin'))
		else:
			return super(AdminInstruction, self).response_change(request, obj)

admin.site.register(Instruction, AdminInstruction)

class StudentCandidateAdmin(admin.ModelAdmin):
	list_per_page = 15
	actions = ['download_csv']
	list_display = ('applicationId','fullname','created_on_datetime',
		'current_location','program_name',
		'user_email','current_status')
	search_fields = ('full_name','current_location__location_name',
		'program__program_name','login_email__email','application_status',)
	list_filter = (('created_on_datetime', DateRangeFilter),)

	def has_add_permission(self, request):
		return False

	def get_actions(self, request):
		actions = super(StudentCandidateAdmin, self).get_actions(request)
		del actions['delete_selected']
		return actions

	def __init__(self,*args,**kwargs):
		super(StudentCandidateAdmin, self).__init__(*args, **kwargs)
		self.list_display_links =[]

	def user_email(self, profile):
		return profile.login_email.email

	def fullname(self,profile):
		return self.full_name

	def program_name(self,profile):
		return profile.program.program_name

	def current_status(self,profile):
		return profile.application_status

	def applicationId(self,profile):
		return "<a href='%s'>%s</a>"%(reverse('bits_admin:admin-application-views',
			kwargs={'id': profile.id}),profile.student_application_id)

	applicationId.allow_tags = True
	applicationId.short_description = "applicationId"
	applicationId.admin_order_field = 'student_application_id'
	current_status.admin_order_field = 'application_status'
	program_name.admin_order_field = 'program__program_name'
	fullname.admin_order_field = 'full_name'
	user_email.admin_order_field = 'login_email__email'

	def download_csv(self, request, queryset):
		import csv
		from django.http import HttpResponse
		import StringIO
		f = StringIO.StringIO()
		writer = csv.writer(f)
		writer.writerow(['applicationId', 'fullname', 'created_on_datetime',
		 'current_location', 'program_name','user_email','current_status'])
		for s in queryset:
			writer.writerow([s.applicationId(), s.full_name,
				s.created_on_datetime, s.current_location,
				s.program_name(),s.user_email(),s.current_status()])
		f.seek(0)
		response = HttpResponse(f, content_type='text/csv')
		response['Content-Disposition'] = 'attachment; filename=stat-info.csv'
		return response

	download_csv.short_description = "Download CSV file for selected stats."

# admin.site.register(StudentCandidateApplication, StudentCandidateAdmin)


class ApplicationPaymentAdmin(admin.ModelAdmin):
	"""Application Payment Custom Admin class."""

	def get_urls(self):
		"""Add Custom url to Admin Urls list."""
		urls = super(ApplicationPaymentAdmin, self).get_urls()
		my_urls = [url(r'^update/$', self.admin_site.admin_view(
			self.payment_import),
			name='admin_update_paymentdata')]
		return my_urls + urls

	def get_success_data(self, request, form):
		success = True
		context = dict(
			self.admin_site.each_context(request), form=form, success=success)
		return TemplateResponse(request, "payment_imported.html", context)
	def get_unsuccess_data(self, request, form):
		success = True
		context = dict(
			self.admin_site.each_context(request), form=form, success=success)
		return TemplateResponse(request, "error_payment_imported.html", context)

	def payment_data_return_context(self, request, form):
		"""Submit Payment Upload form."""
		result = form.save()
		success_result = None
		if not result:
			self.get_success_data(request, form)
			success_result = "success"
		else:
			self.get_unsuccess_data(request, form)
			success_result = "fail"
		return success_result

	def payment_import(self, request):
		"""Custom View to upload the Payment data CSV format."""
		if request.method == "POST":
			form = PaymentDataInput(request.POST, request.FILES)

			if form.is_valid():
				result = self.payment_data_return_context(request, form)
				if result == "success":
					return HttpResponseRedirect(
						reverse('registrationForm:bits-login-admin'))
				else:
					context = {"form": form}
					return TemplateResponse(
						request, "error_payment_imported.html", context)
			else:
				context = {"form": form}
				return TemplateResponse(request, "payment_imported.html", context)
		else:
			form = PaymentDataInput()
			context = {"form": form}
			return TemplateResponse(request, "payment_imported.html", context)
admin.site.register(ApplicationPayment, ApplicationPaymentAdmin)


class AdminCollaboratingOrganization(admin.ModelAdmin):
	list_per_page = 15
	list_display =('org_name',)
admin.site.register(CollaboratingOrganization, AdminCollaboratingOrganization)


class ExceptionListOrgApplicantsAdmin(ImportExportMixin, admin.ModelAdmin):
	list_per_page = 15
	list_max_show_all = 2000
	formats=(base_formats.CSV,base_formats.XLS,base_formats.XLSX,)
	resource_class = ExceptionListOrgApplicantsResource
	form = ELOAForms
	search_fields = ['employee_name', 'employee_email',
	'org__org_name','program__program_name','program__program_code']
	list_display = ['employee_email','exception_type',
	'org','program','employee_id','employee_name']

admin.site.register(ExceptionListOrgApplicants, ExceptionListOrgApplicantsAdmin)

class AdminReviewer(admin.ModelAdmin):
	form = ReviewerRegistrationsForm #edit
	add_form = ReviewerRegistrationsForm #add
	list_display = ('user','last_login','role_of_user')
	def role_of_user(self, profile):
		user_role = profile.user_role
		return 'Reviewer' if not user_role else ' '.join(map(lambda x : x.capitalize(),user_role.split('-')))

	def last_login(self, obj):
		return obj.user.last_login

	def save_model(self, request, obj, form, change):
		email = form.cleaned_data['email']
		password = form.cleaned_data['password1']
		user_role = form.cleaned_data['user_role']

		if not change:
			username=uuid4().hex[:-4]
			user = User.objects.create_user(username=username,
				email=email, password=password)
			user.save()
			reviewer =Reviewer.objects.create(user = user,
				reviewer = True, user_role = user_role)
			reviewer.save()
		else:

			user=User.objects.get(email=obj.user.email)
			user.email=email
			user.password=make_password(password)
			user.save()
			obj.save()
			
	def get_form(self, request, obj=None, **kwargs):
		
		if obj:
			form = EditReviewerRegistrationsForm
			form.base_fields['email'].initial = obj.user.email
			form.base_fields['user_role'].initial = obj.user_role
		else:
			form = super(AdminReviewer, self).get_form(request, obj, **kwargs)
			form.base_fields['email'].initial = ''
			form.base_fields['user_role'].initial = None

		return form
admin.site.register(Reviewer, AdminReviewer)

class AdminProgramDomainMapping(ImportMixin, admin.ModelAdmin):
	form = ProgramDomainMappingForm
	formats=(base_formats.CSV,base_formats.XLS,base_formats.XLSX,)
	resource_class = ProgramDomainMappingResource
	list_per_page = 15
	list_max_show_all = 2000
	list_display =('program','domain',
		'email')
	search_fields = ['program__program_name','program__program_code', 'email']
	def domain(self, profile):
		email_domain = profile.email_domain
		return ' ' if not email_domain else email_domain
		
admin.site.register(ProgramDomainMapping, AdminProgramDomainMapping)

class AdminProgramDocumentMap(admin.ModelAdmin):
	list_per_page = 15
	list_max_show_all = 2000
	list_display = ('program', 'document_type', 'mandatory_flag','deffered_submission_flag')
	search_fields = ['program__program_name', 'program__program_code', 'document_type__document_name']
	form = ProgramDocumentMapForm
admin.site.register(ProgramDocumentMap, AdminProgramDocumentMap)

class AdminFormFieldPopulationSpecific(admin.ModelAdmin):
	list_per_page = 15
	list_display =('program','field_name',
		'show_on_form','default_value','is_editable')
	form = FormFieldPopulationSpecificForm
	def changeform_view(self, request, object_id=None, form_url='', extra_context=None):

		extra_context={'title':'Form Field Customizations (Specific Programs Only)',}
		return super(AdminFormFieldPopulationSpecific, self).changeform_view(request, object_id, form_url, extra_context=extra_context)
admin.site.register(FormFieldPopulationSpecific, AdminFormFieldPopulationSpecific)

class AdminProgramQualificationCategorymappings(admin.ModelAdmin):
	list_per_page = 15
	list_display = ('program','qualification_category')
	search_fields = ['program__program_name', 'program__program_code', 'qualification_category__category_name']
admin.site.register(ProgramQualificationRequirements, AdminProgramQualificationCategorymappings)

class AdminQualificationCategory(admin.ModelAdmin):
	list_per_page = 15
admin.site.register(QualificationCategory, AdminQualificationCategory)

class AdminCousreList(admin.ModelAdmin):
	list_per_page = 15
	list_display =('program','admit_year','course_id','course_name','course_unit','active_flag','is_elective')
	search_fields = ['program__program_code','program__program_name','course_id','course_name']
admin.site.register(FirstSemCourseList, AdminCousreList)

class AdminBatchMailConfig(admin.ModelAdmin):
	list_per_page = 15
	list_display =('mail_type','mail_batch',)
	readonly_fields=('mail_type',)

	def mail_batch(self, profile):
		return "{0} - {1}".format(profile.initial_day,profile.cutoff_date)

	def has_add_permission(self, request):
		return False

	def has_delete_permission(self, request,obj=None):
		return False

	def get_actions(self, request):
		actions = super(AdminBatchMailConfig, self).get_actions(request)
		del actions['delete_selected']
		return actions

admin.site.register(BatchMailConfig, AdminBatchMailConfig)

@admin.register(ApplicantExceptions)
class AdminApplicantExceptions(ImportExportMixin, admin.ModelAdmin):
	formats=(base_formats.CSV,)
	resource_class = ApplicantExceptionsResource
	exclude = ('application',)
	list_per_page = 15
	list_display =('applicant_email','program','work_ex_waiver','employment_waiver',
		'mentor_waiver','offer_letter','hr_contact_waiver','org','transfer_program','created_on_datetime')
	search_fields = ['applicant_email','program__program_name','program__program_code']
	
	def get_export_resource_class(self):
		return ApplicantExceptionsExportResource

@admin.register(ProgramLocationDetails)
class AdminProgramLocationDetails(ImportMixin, admin.ModelAdmin):
	form = ProgramLocationDetailsForm
	formats=(base_formats.CSV,base_formats.XLS,base_formats.XLSX,)
	resource_class = ProgramLocationDetailsResource
	des= escape("""The set of information below is intended for the offer letter issued to the student for the program upon acceptance of admission offer.
		 The information is dependent on the location from where the student has opted to attend courses for the program. 
		 If any of the information below is kept blank and the same is intended to be shown on the offer letter,
		  the offer letter will show the text - < to be announced later >""")
	fieldsets = (
		(None,{
		'fields':('program','location','fee_payment_deadline_date',
			'orientation_date','lecture_start_date')
		}),
		(None,{
		'fields':('orientation_venue',
			'lecture_venue','admin_contact_person','acad_contact_person',
			'admin_contact_phone','acad_contact_phone',),
		'description':des,
		}),
	)
	list_per_page = 15
	list_max_show_all = 2000
	list_display =('program','location','fee_payment_deadline_date',
		'orientation_date','lecture_start_date',
		'orientation_venue','lecture_venue',
		'admin_contact_person','acad_contact_person',
		'admin_contact_phone','acad_contact_phone')
	search_fields = ['program__program_name', 'program__program_code', 'location__location_name',
		'orientation_venue', 'lecture_venue', 'admin_contact_person', 'acad_contact_person',
	]

@admin.register(OtherFeePayment)
class AdminOtherFeePayment(ImportExportMixin, admin.ModelAdmin):
	formats=(base_formats.CSV,)
	resource_class = OFPImportResource
	exclude = ('uploaded_on',)
	list_per_page = 15
	fields = ('email', 'program','fee_type', 'fee_amount','Zest_Program_Map','Propelld_Program_Map','enable_zest_flag','enable_eduvenz_flag','enable_ABFL_flag','enable_propelld_flag',
			'propelld_course_id','paid_on','transaction_id','payment_bank', 'gateway_total_amount', 'gateway_net_amount', 'student_application_id','student_id', 'full_name', 'mobile')
	list_display =('email', 'fee_type', 'fee_amount','enable_eduvenz_flag','enable_ABFL_flag','enable_zest_flag','Zest_Program_Map',
					'Propelld_Program_Map','propelld_course_id','uploaded_on', 'paid_on','student_application_id','student_id')
	search_fields = ['email','fee_type','program__program_code',
		'student_application_id','student_id',]

	def get_export_resource_class(self):
		return OFPExportResource


class AdminZestProgramMap(admin.ModelAdmin):
	list_per_page = 15
	list_display = ('merchant_name','client_id', 'client_secret')

admin.site.register(ZestProgramMap, AdminZestProgramMap)


class ProgramFormNotesFieldsAdmin(admin.ModelAdmin):
	def formfield_for_foreignkey(self, db_field, request, **kwargs):
	    if db_field.name == "program":
	        kwargs["queryset"] = Program.objects.filter(program_type='specific')
	    return super(ProgramFormNotesFieldsAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
admin.site.register(ProgramFormNotesFields,ProgramFormNotesFieldsAdmin)

# class ApplicationDocumentAdmin(admin.ModelAdmin):
# 	list_display =('application',)
# 	search_fields = ['application__student_application_id',]
# admin.site.register(ApplicationDocument, ApplicationDocumentAdmin)

class AdminPropelldProgramMap(admin.ModelAdmin):
	list_per_page = 15
	list_display = ('propelld_name','client_id', 'client_secret')

admin.site.register(PropelldProgramMap, AdminPropelldProgramMap)