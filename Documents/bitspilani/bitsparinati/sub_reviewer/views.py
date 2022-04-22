import logging
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render, redirect
from super_reviewer.dynamic_views import *
from registrations.models import *
from registrations.tables_ajax import *
from registrations.tables import *
from registrations.dynamic_views import (ReviewerApplicantData as BaseRAD)
from .bits_decorator import *
from django.shortcuts import render, redirect, HttpResponseRedirect
from django.views.generic.edit import UpdateView
from django.core.urlresolvers import reverse_lazy
from registrations.dynamic_dmr_report import *
from registrations.tables_ajax import (ReviewerDataView as BaseAjaxRDV)
from registrations.csv_views import (BaseRCSV as BRCSV)
from registrations.tables import ( filter_paging as FA, pgm_adm_report_paging)
from bits_admin.dynamic_views import BaseDefDocsAppData, BaseDefDocsSubData
from bits_admin.tables import def_doc_paging, doc_sub_paging
from bits_admin.tables_ajax import DefDocView, DefDocSubView
from .tables import *
from .forms import *

logger = logging.getLogger("main")
# Create your views here.


@method_decorator([login_required, sub_reviewer_permission,],name='dispatch')
class RCSV(BRCSV):
	app_status=[]

@method_decorator([login_required,sub_reviewer_permission],name='dispatch')
class MyDataView(BaseAjaxRDV):
	token = RA_table().token


@method_decorator([login_required,sub_reviewer_permission],name='dispatch')
class RAData(BaseRAD):
	template_name = 'sub_reviewer/home.html'
	def get_context_data(self, program=None, status=None, pg_type=None, **kwargs):
		context = super(RAData, self).get_context_data(program=program,
		 status=status, pg_type=pg_type, **kwargs)
		SCATable = RA_table(program=context['program'], status=context['status'], pg_type=context['pg_type'],)
		context['table'] = SCATable(context['query'])
		return context 


@method_decorator([login_required, sub_reviewer_permission,],name='dispatch')
class DMR(BaseDMR):
	template_name = 'sub_reviewer/reports/dmr_report.html'

@method_decorator([login_required, sub_reviewer_permission,],name='dispatch')
class DMRNonSpecific(BaseDMRNonSpecific):
	template_name = 'sub_reviewer/reports/dmr_non_specific.html'
	form_class = DMRNonSpecificForm

	def get_context_data(self, **kwargs):
		context = super(DMRNonSpecific, self).get_context_data(**kwargs)
		context['form'] = self.form_class(initial=self.request.GET)
		return context

@method_decorator([login_required, sub_reviewer_permission,],name='dispatch')
class WaiverReportDataView(BaseWaiverReportDataView):
	token = WR_table().token

@method_decorator([login_required, sub_reviewer_permission,],name='dispatch')
class WaiverReport(BaseWaiverReport):
	template_name = 'sub_reviewer/reports/fee_waiver_report.html'

	def get_context_data(self, **kwargs):
		context = super(WaiverReport, self).get_context_data(**kwargs)
		SCATable = WR_table(self.request.GET.get('admit_batch')  or 0)
		context['table'] = SCATable(context['query'])
		return context

@method_decorator([login_required, sub_reviewer_permission],name='dispatch')
class MilestoneView(BaseMilestoneView):
	token = M_table().token

@method_decorator([login_required, sub_reviewer_permission,],name='dispatch')
class ApplicationMilestoneReport(BaseApplicationMilestoneReport):
	template_name = 'sub_reviewer/reports/milestone_report.html'

	def get_context_data(self, **kwargs):
		context = super(ApplicationMilestoneReport, self).get_context_data(**kwargs)
		SCATable = M_table(self.request.GET.get('admit_batch')  or 0,self.request.GET.get('program') or 0,self.request.GET.get('pg_type') or 0)
		context['table'] = SCATable(context['query'])
		return context

@method_decorator([login_required, sub_reviewer_permission, sub_reviewer_update_permission],name='dispatch')
class ApplicantDetail(UpdateView):
	model = StudentCandidateApplication
	template_name = 'sub_reviewer/application_form_update.html'
	form_class = SubReviewerForm
	
	pk_url_kwarg = 'application_id'
	application_id=None

	def second_form(self):
		SubReviewerApplicationDocumentFormSet = inlineformset_factory(
			StudentCandidateApplication,
			ApplicationDocument,
			form=sub_rev_app_doc(email=self.request.user.email),
			extra=0,
			can_delete=False,
			can_order=False
			)
		return SubReviewerApplicationDocumentFormSet
	
	def get_context_data(self, **kwargs):
		context = super(ApplicantDetail, self).get_context_data(**kwargs)
		app = StudentCandidateApplication.objects.get(id=self.application_id)
		
		if 'app_form' not in context:
			context['app_form'] = self.get_form()
		#context['doc_form'] = self.get_form(form_class=SubReviewerApplicationDocumentFormSet)
		if 'doc_form' not in context:
			context['doc_form'] = self.second_form()(instance=self.get_object(), prefix="doc")

		# code to hide employment and mentor details
		sca_attributes = app.__dict__.keys()
		for x in sca_attributes:
			setattr(app, '%s_hide' %(x), False)

		rejected_attributes = FormFieldPopulationSpecific.objects.filter(
		program=app.program,
		show_on_form=False,
		).values_list('field_name', flat=True)

		for x in rejected_attributes:
			setattr(app, '%s_hide' %(x), True)
		
		context['form'] = app
		p_code = str(app.student_application_id)[1:5]
		program_object = Program.objects.filter(program_code=p_code)
		document_submission_flag = program_object[0].document_submission_flag

		context['document_submission_flag'] = document_submission_flag
		context['edu1'] = StudentCandidateWorkExperience.objects.filter(application=app)
		context['qual1'] = StudentCandidateQualification.objects.filter(application=app)
		context['uploadFiles'] = ApplicationDocument.objects.filter(application=app)
		context['is_specific'] = app.program.program_type == 'specific'
		context['teaching_mode_check'] = self.def_teaching_mode_check()
		return context

	def get(self, request, application_id=None, *args, **kwargs):
		self.application_id = application_id
		return super(ApplicantDetail, self).get(request, *args, **kwargs)

	def post(self, request, application_id=None, *args, **kwargs):
		self.application_id = application_id
		self.object = self.get_object()
		# return super(ApplicantDetail, self).post(request, *args, **kwargs)
		
		app_form = self.get_form()
		doc_form = self.second_form()(self.request.POST,
			instance=self.get_object(), prefix="doc")
		if app_form.is_valid() and doc_form.is_valid():
			app_form.save()
			doc_form.save()
			return HttpResponseRedirect(self.get_success_url())
		else:
			return self.form_invalid(app_form, doc_form, **kwargs)

	def form_invalid(self, app_form, doc_form, **kwargs):
		ctx = self.get_context_data(app_form=app_form, doc_form=doc_form, **kwargs)
		return self.render_to_response(ctx)

	def get_success_url(self):
		return reverse_lazy('sub_reviewer:sub-review-application-details',
			kwargs={'application_id':self.application_id})

	#code to hide teaching mode
	def def_teaching_mode_check(self):
		return FormFieldPopulationSpecific.objects.filter(
				program=self.get_object().program,
				show_on_form=True,
				field_name__in=['teaching_mode','programming_flag','alternate_email_id',],
			).values_list('field_name', flat=True)


@method_decorator([login_required, sub_reviewer_permission],name='dispatch')
class ApplicantDetailView(BaseApplicantDetail):
	template_name = 'sub_reviewer/application_view.html'


@method_decorator([login_required, sub_reviewer_permission,],name='dispatch')
class ProgChangeReportAjax(BaseProgChangeReport):
	token = PCRP_table().token

@method_decorator([login_required, sub_reviewer_permission,],name='dispatch')
class ProgramChangeReport(BaseProgramChangeReport):
	template_name = 'sub_reviewer/prog_change_report.html'

	def get_context_data(self, **kwargs):
		context = super(ProgramChangeReport, self).get_context_data(**kwargs)
		SCATable = PCRP_table(self.request.GET.get('admit_batch')  or 0)
		context['table'] = SCATable(context['query'])
		return context

@method_decorator([login_required,sub_reviewer_permission,],name='dispatch')
class ProgramLocationReport(BaseProgramLocationReport):
	template_name = 'sub_reviewer/reports/prog_loc_report.html'

@method_decorator([login_required,sub_reviewer_permission,],name='dispatch')
class AEView(BaseAEView):
	token = ApplcantExceptionTable().token

@method_decorator([login_required,sub_reviewer_permission,],name='dispatch')
class ApplicationExceptionView(BaseApplicationExceptionView) :
	template_name = 'sub_reviewer/reports/application_exception_table.html'

@method_decorator([login_required,sub_reviewer_permission,],name='dispatch')
class DefDocsAppAjaxData(DefDocView):
	token = def_doc_paging(ajax_url = 'sub_reviewer:def-doc-ajax',action_url = 'sub_reviewer:sub-review-application-details').token

@method_decorator([login_required,sub_reviewer_permission,],name='dispatch')
class DefDocsSubAjaxData(DefDocSubView):
	token = doc_sub_paging(ajax_url = 'sub_reviewer:def-doc-sub-ajax',action_url = 'sub_reviewer:sub-review-application-details').token

@method_decorator([login_required,sub_reviewer_permission,],name='dispatch')
class DefDocsAppData(BaseDefDocsAppData):
	template_name = 'sub_reviewer/def_doc_app_view.html'
	ajax_url = 'sub_reviewer:def-doc-ajax'
	action_url = 'sub_reviewer:sub-review-application-details'

@method_decorator([login_required,sub_reviewer_permission,],name='dispatch')
class DefDocsSubData(BaseDefDocsSubData):
	ajax_url = 'sub_reviewer:def-doc-sub-ajax'
	action_url = 'sub_reviewer:sub-review-application-details'
	template_name = 'sub_reviewer/def_doc_fields_view.html'

@method_decorator([login_required, sub_reviewer_permission,],name='dispatch')
class SubRev_DMRCertification(BaseDMRCertification):
	template_name = 'sub_reviewer/reports/dmr_certification.html'

@method_decorator([login_required, sub_reviewer_permission,],name='dispatch')
class SubRev_DMRCluster(BaseDMRCluster):
	template_name = 'sub_reviewer/reports/dmr_cluster.html'

@method_decorator([login_required, sub_reviewer_permission,],name='dispatch')
class SubRev_DMRSpecific(BaseDMRSpecific):
	template_name = 'sub_reviewer/reports/dmr_specific.html'

@method_decorator([login_required, sub_reviewer_permission,],name='dispatch')
class ProgramAdmissionsReport(BaseProgramAdmissionReport):
	template_name = 'sub_reviewer/reports/pgm_adm_report.html'
	ajax_url = 'sub_reviewer:program-admissions-report-ajax'

@method_decorator([login_required, sub_reviewer_permission,],name='dispatch')
class ProgramAdmissionsReportAjax(BasePgmAdmReportAjaxData):
	token = pgm_adm_report_paging(ajax_url='sub_reviewer:program-admissions-report-ajax',).token
