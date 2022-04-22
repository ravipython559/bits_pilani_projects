from django.shortcuts import render
from django.conf import settings
from django.utils import timezone
from django.views.generic.edit import UpdateView, CreateView
from django.views.generic import TemplateView
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse_lazy
from django.forms.models import *
from .forms import *
from .bits_decorator import *

# Create your views here.
@method_decorator([login_required, is_certificate_redirect],name='dispatch')
class ApplicationForm(CreateView):
	model = StudentCandidateApplication
	template_name = 'certificate/application_form.html'
	program_code = None


	def get_form_class(self):
		self.form_class = studentApplication(pg_code=self.program_code, 
			login_email=self.request.user.email)
		return self.form_class

	def second_form(self):
		EducationFormset = modelformset_factory(
			StudentCandidateQualification,
			form=StudentEducation(pg_code=self.program_code), 
			extra=0,min_num=1, 
			can_delete=True, exclude=('application',),
		)
		return EducationFormset

	def get(self, request, pg_code=None, *args, **kwargs):
		self.program_code = pg_code
		return super(ApplicationForm, self).get(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super(ApplicationForm, self).get_context_data(**kwargs)
		
		if 'form' not in context:
			context['form'] = self.get_form()
		if 'educationFormset' not in context:
			context['educationFormset'] = self.second_form()( prefix='edu', 
				queryset=StudentCandidateWorkExperience.objects.none() )
		context['pg_code'] = self.program_code
		pgm = Program.objects.get(program_code=str(context['pg_code']))
		context['title']= str(pgm.form_title)
		context['is_pg_active']= pgm.active_for_applicaton_flag
		return context

	def send_mail(self, sca = None):
		subject = 'Application Form %s has been received'%(sca.student_application_id)
		user_detail={'progName': sca.program.program_name,
			'location': sca.current_location.location_name,
			'appID': sca.student_application_id,
			'userID':sca.login_email.email,
			'regEmailID':sca.email_id}
		msg_plain = render_to_string('reg_email.txt', user_detail)
		msg_html = render_to_string('reg_email.html', user_detail)
		email = send_mail(subject,msg_plain,'<'+settings.FROM_EMAIL+'>',
			[sca.email_id],html_message=msg_html, fail_silently=True)

	def post(self, request, pg_code=None, *args, **kwargs):

		self.program_code = pg_code
		pfa = PROGRAM_FEES_ADMISSION.objects.get(
			program__program_code=self.program_code, latest_fee_amount_flag=True,
			fee_type='2')
		
		form = self.get_form()
		second_form = self.second_form()(self.request.POST, prefix="edu")
		if form.is_valid() and second_form.is_valid():
			app = form.save(commit=False)
			app.application_status = settings.APP_STATUS[12][0]
			app.admit_year = pfa.admit_year
			app.admit_sem_cohort = pfa.admit_sem_cohort
			app.admit_batch = '{0}-{1}'.format(pfa.admit_year, pfa.admit_sem_cohort)
			app.login_email = request.user
			app.current_org_employment_date = timezone.datetime(day=1,month=1,year=1990)
			app.exam_location = str(app.current_location)
			app.save()
			sca = StudentCandidateApplication.objects.get(login_email=request.user)
			sca.student_application_id = "A{0}{1:04d}".format(app.program.program_code, app.id)
			ApplicantExceptions.objects.filter(applicant_email = sca.login_email.email,
				program = sca.program,
				transfer_program__isnull = False ).update(application = sca)
			eduFormset = second_form.save(commit=False)
			for x in eduFormset:
				x.application = sca
				x.save()

			sca.save()
			self.send_mail(sca=sca)
			return HttpResponseRedirect(self.get_success_url())
		else:
			return self.form_invalid(form, second_form, **kwargs)

	def form_invalid(self, form, second_form, **kwargs):
		ctx = self.get_context_data(form=form, educationFormset=second_form, **kwargs)
		return self.render_to_response(ctx)

	def get_success_url(self):
		return reverse_lazy('certificate:progress')

@method_decorator([login_required, is_certificate_redirect_to_edit ],name='dispatch')
class ApplicationEditForm(UpdateView):
	model = StudentCandidateApplication
	template_name = 'certificate/application_edit_form.html'
	application_id = None

	def get_object(self, queryset=None):
		return StudentCandidateApplication.objects.get(login_email=self.request.user)

	def get_form_class(self):
		self.form_class = studentApplication(pg_code=self.get_object().program.program_code, 
			login_email=self.get_object().login_email.email)
		return self.form_class

	def second_form(self):
		EducationFormset = inlineformset_factory(
			StudentCandidateApplication, 
			StudentCandidateQualification,
			form=StudentEducation(pg_code=self.get_object().program.program_code), 
			extra=0,min_num=1, can_delete=True,
			)
		return EducationFormset

	def get_context_data(self, *args, **kwargs):
		context = super(ApplicationEditForm, self).get_context_data(*args, **kwargs)
		
		if 'form' not in context:
			context['form'] = self.get_form()
		if 'educationFormset' not in context:
			context['educationFormset'] = self.second_form()(instance=self.object, prefix="edu")
		context['pg_code'] = self.object.program.program_code
		context['is_pg_active']= self.object.program.active_for_applicaton_flag
		context['title']= str(Program.objects.get(program_code=str(context['pg_code'])).form_title)
		return context

	def send_mail(self, sca = None):
		subject = 'Application Form %s has been received'%(sca.student_application_id)
		user_detail={'progName': sca.program.program_name,
			'location': sca.current_location.location_name,
			'appID': sca.student_application_id,
			'userID':sca.login_email.email,
			'regEmailID':sca.email_id}
		msg_plain = render_to_string('reg_email.txt', user_detail)
		msg_html = render_to_string('reg_email.html', user_detail)
		email = send_mail(subject,msg_plain,'<'+settings.FROM_EMAIL+'>',
			[sca.email_id],html_message=msg_html, fail_silently=True)

	def post(self, request, *args, **kwargs):

		self.object = self.get_object()
		form = self.get_form()
		second_form = self.second_form()(self.request.POST,
			instance=self.object, prefix="edu")
		if form.is_valid() and second_form.is_valid():
			

			app = form.save(commit=False)
			pfa = PROGRAM_FEES_ADMISSION.objects.get(
				program=app.program, latest_fee_amount_flag=True,
				fee_type='2')
			app.exam_location = str(app.current_location)
			app.admit_year = pfa.admit_year
			app.admit_sem_cohort = pfa.admit_sem_cohort
			app.admit_batch = '{0}-{1}'.format(pfa.admit_year, pfa.admit_sem_cohort)
			app.save()
			ApplicantExceptions.objects.filter(applicant_email = self.object.login_email.email,
				program = self.object.program,
				transfer_program__isnull = False ).update(application = self.object)
			if self.object.application_status == settings.APP_STATUS[16][0] :
				self.object.application_status = settings.APP_STATUS[14][0]
			self.object.student_application_id = "A{0}{1:04d}".format(app.program.program_code, app.id)
			self.object.save()
			second_form.save()
			self.send_mail(sca=self.object)
			return HttpResponseRedirect(self.get_success_url())
		else:
			return self.form_invalid(form, second_form,*args, **kwargs)

	def form_invalid(self, form, second_form, *args, **kwargs):
		ctx = self.get_context_data(form=form, educationFormset=second_form, *args, **kwargs)
		return self.render_to_response(ctx)

	def get_success_url(self):
		return reverse_lazy('certificate:progress')


class ViewData(TemplateView):
	template_name = "progress.html"
	
	def get_context_data(self,*args, **kwargs):
		context = super(ViewData, self).get_context_data(*args, **kwargs)
		p_code = str(self.sca.student_application_id)[1:5]
		program_object = Program.objects.filter(program_code=p_code)
		document_submission_flag = program_object[0].document_submission_flag
		context['queryResult'] = self.sca
		context['show_greeting_msg'] = self.sca.application_status==settings.APP_STATUS[12][0]
		context['document_submission_flag'] = document_submission_flag
		return context

	def get(self, request, *args, **kwargs):
		self.sca = StudentCandidateApplication.objects.get(login_email=request.user)
		return super(ViewData, self).get(request, *args, **kwargs)

@method_decorator([login_required, ],name='dispatch')
class ApplicationFormView(TemplateView):
	template_name = "certificate/application_form_view.html"
	def get_context_data(self,*args, **kwargs):
		sca = StudentCandidateApplication.objects.get(login_email=self.request.user)
		context = super(ApplicationFormView, self).get_context_data(*args, **kwargs)
		context['sca'] = sca
		context['edu1'] = StudentCandidateWorkExperience.objects.filter(application=sca)
		context['qual1'] = StudentCandidateQualification.objects.filter(application=sca)
		context['uploadFiles'] = ApplicationDocument.objects.filter(application=sca)

		#logic to check teaching mode,programming_flag
		teaching_mode_check = FormFieldPopulationSpecific.objects.filter(program = sca.program,show_on_form=True,
				field_name__in=['teaching_mode','programming_flag','alternate_email_id',]
			).values_list('field_name', flat=True)

		context['teaching_mode_check'] = teaching_mode_check

		return context 

@method_decorator([login_required, is_certificate_redirect_to_admin_rev_edit],name='dispatch')
class ApplicationAdminView(UpdateView):
	template_name = "certificate/application_form_view.html"
	form_class = DobForm
	model = StudentCandidateApplication

	def get_initial(self):
		return {'date_of_birth':self.object.date_of_birth}

	def get_context_data(self,alert_status=None, *args, **kwargs):
		context = super(ApplicationAdminView, self).get_context_data(*args, **kwargs)
		context['sca'] = self.object 
		context['qual1'] = StudentCandidateQualification.objects.filter(application=self.object)
		context['uploadFiles'] = ApplicationDocument.objects.filter(application=self.object)
		context['alert_status'] = alert_status
		return context

	def get_success_url(self):
		return reverse_lazy('certificate:student-rev-or-adm-application-view',
			kwargs={'pk':self.object.pk})