import logging
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render
from registrations.models import *
from bits_admin.tables_ajax import *
from bits_admin.dynamic_views import *
from super_reviewer.dynamic_views import *
from bits_admin.csv_views import *
from .bits_decorator import *
from registrations.dynamic_dmr_report import *
from registrations.tables_ajax import *
from registrations.tables import pgm_adm_report_paging
from business_dev.tables import *
logger = logging.getLogger("main")
# Create your views here.


@method_decorator([login_required, business_user_permission],name='dispatch')
class MyDataView(ApplicantAjaxDataView):
	token = FP_table().token


@method_decorator([login_required, business_user_permission],name='dispatch')
class ViewData(ApplicantDataView):
	template_name = 'business_dev/home.html'

	def get_context_data(self, to_date=None, from_date=None, pg_type=None, program=None, status=None, admit_batch=None, **kwargs):
		context = super(ViewData, self).get_context_data(to_date=to_date,
			from_date=from_date, pg_type=pg_type, program=program, status=status, admit_batch=admit_batch, **kwargs)
		SCATable = FP_table(program=context['program'], 
			status=context['status'], from_date=context['from_date'],
			to_date=context['to_date'], pg_type=context['pg_type'], admit_batch=context['admit_batch'])
		context['table'] = SCATable(context['queryResult'])
		return context


@method_decorator([login_required, business_user_permission],name='dispatch')
class DateRefresh(DateRefreshView):
	template_name = 'business_dev/home.html'

	def get_context_data(self, to_date=None, from_date=None, pg_type=None, program=None, status=None, admit_batch=None, **kwargs):
		context = super(DateRefresh, self).get_context_data(to_date=to_date,
			from_date=from_date,pg_type=pg_type,program=program,status=status, admit_batch=admit_batch, **kwargs)

		SCATable = FP_table(program=context['program'], 
			status=context['status'], from_date=context['from_date'],
			to_date=context['to_date'], pg_type=context['pg_type'], admit_batch=context['admit_batch'])
		context['table'] = SCATable(context['queryResult'])
		return context


@method_decorator([login_required, business_user_permission],name='dispatch')
class CSVView(BaseCSVView):pass


@method_decorator([login_required, business_user_permission,],name='dispatch')
class DMR(BaseDMR):
	template_name = 'business_dev/reports/dmr_report.html'


@method_decorator([login_required, business_user_permission,],name='dispatch')
class DMRNonSpecific(BaseDMRNonSpecific):
	template_name = 'business_dev/reports/dmr_non_specific.html'
	form_class = DMRNonSpecificForm

	def get_context_data(self, **kwargs):
		context = super(DMRNonSpecific, self).get_context_data(**kwargs)
		context['form'] = self.form_class(initial=self.request.GET)
		return context

@method_decorator([login_required, business_user_permission,],name='dispatch')
class WaiverReportDataView(BaseWaiverReportDataView):
	token = WR_table().token


@method_decorator([login_required, business_user_permission,],name='dispatch')
class WaiverReport(BaseWaiverReport):
	template_name = 'business_dev/reports/fee_waiver_report.html'

	def get_context_data(self, **kwargs):
		context = super(WaiverReport, self).get_context_data(**kwargs)
		SCATable = WR_table(self.request.GET.get('admit_batch')  or 0)
		context['table'] = SCATable(context['query'])
		return context


@method_decorator([login_required, business_user_permission],name='dispatch')
class MilestoneView(BaseMilestoneView):
	token = M_table().token


@method_decorator([login_required, business_user_permission,],name='dispatch')
class ApplicationMilestoneReport(BaseApplicationMilestoneReport):
	template_name = 'business_dev/reports/milestone_report.html'

	def get_context_data(self, **kwargs):
		context = super(ApplicationMilestoneReport, self).get_context_data(**kwargs)
		SCATable = M_table(self.request.GET.get('admit_batch')  or 0,self.request.GET.get('program') or 0,self.request.GET.get('pg_type') or 0)
		context['table'] = SCATable(context['query'])
		return context


@method_decorator([login_required, business_user_permission],name='dispatch')
class ApplicantDetail(BaseApplicantDetail):
	template_name = 'business_dev/application_view.html'


@method_decorator([login_required, business_user_permission],name='dispatch')
class ArchiveHomeDataView(BaseArchiveHomeDataView):
	template_name = 'business_dev/bits_archived/archivedView.html'

	def get_context_data(self, to_date=None, from_date=None, pg_type=None, program=None, status=None,admit_batch=None, **kwargs):
		context = super(ArchiveHomeDataView, self).get_context_data( to_date=to_date, 
			from_date=from_date, pg_type=pg_type, 
			program=program, status=status,admit_batch=admit_batch,**kwargs)
		SCATable = AFP_table(to_date=to_date, from_date=from_date, pg_type=pg_type, program=program, status=status,admit_batch=admit_batch,)
		context['table'] = SCATable(context['queryResult'])
		return context


@method_decorator([login_required, business_user_permission],name='dispatch')
class ArchiveDataView(BaseArchiveDataView):
	token = AFP_table().token


@method_decorator([login_required, business_user_permission],name='dispatch')
class FilterArchivalApplicant(BaseFilterArchivalApplicant):
	template_name = 'business_dev/bits_archived/archivedView.html'
	def get_context_data(self, to_date=None, from_date=None, pg_type=None, program=None, status=None, admit_batch=None, **kwargs):
		context = super(FilterArchivalApplicant, self).get_context_data( to_date=to_date, 
			from_date=from_date, pg_type=pg_type, program=program, status=status,admit_batch=admit_batch,**kwargs)
		SCATable = AFP_table(to_date=context['to_date'], from_date=context['from_date'], 
			pg_type=context['pg_type'], program=context['program'], status=context['status'], admit_batch=context['admit_batch'],)
		context['table'] = SCATable(context['queryResult'])
		return context


@method_decorator([login_required, business_user_permission],name='dispatch')
class ApplicationAdminArchiveView(BaseApplicationAdminArchiveView):
	template_name = 'business_dev/bits_archived/applicant_archive.html'


@method_decorator([login_required, business_user_permission],name='dispatch')
class CSVArchiveView(BaseCSVArchiveView):pass


@method_decorator([login_required, business_user_permission,],name='dispatch')
class ProgChangeReportAjax(BaseProgChangeReport):
	token = PCRP_table().token


@method_decorator([login_required, business_user_permission,],name='dispatch')
class ProgramChangeReport(BaseProgramChangeReport):
	template_name = 'business_dev/prog_change_report.html'

	def get_context_data(self, **kwargs):
		context = super(ProgramChangeReport, self).get_context_data(**kwargs)
		SCATable = PCRP_table(self.request.GET.get('admit_batch')  or 0)
		context['table'] = SCATable(context['query'])
		return context


@method_decorator([login_required,business_user_permission,],name='dispatch')
class ProgramLocationReport(BaseProgramLocationReport):
	template_name = 'business_dev/reports/prog_loc_report.html'


@method_decorator([login_required,reviewer_or_payment_reviewer_permission_report],name='dispatch')
class AEView(BaseAEView):
	token = ApplcantExceptionTable().token


@method_decorator([login_required,reviewer_or_payment_reviewer_permission_report],name='dispatch')
class ApplicationExceptionView(BaseApplicationExceptionView) :
	template_name = 'business_dev/reports/application_exception_table.html'


@method_decorator([login_required, business_user_permission],name='dispatch')
class DefDocsAppAjaxData(DefDocView):
	token = def_doc_paging(ajax_url = 'business_user:def-doc-ajax',action_url = 'business_user:business_application_details').token

@method_decorator([login_required, business_user_permission],name='dispatch')
class DefDocsSubAjaxData(DefDocSubView):
	token = doc_sub_paging(ajax_url = 'business_user:def-doc-sub-ajax',action_url = 'business_user:business_application_details').token

@method_decorator([login_required, business_user_permission],name='dispatch')
class DefDocsAppData(BaseDefDocsAppData):
	template_name = 'business_dev/reports/def_doc_app_view.html'
	ajax_url = 'business_user:def-doc-ajax'
	action_url = 'business_user:business_application_details'

@method_decorator([login_required, business_user_permission],name='dispatch')
class DefDocsSubData(BaseDefDocsSubData):
	ajax_url = 'business_user:def-doc-sub-ajax'
	action_url = 'business_user:business_application_details'
	template_name = 'business_dev/reports/def_doc_fields_view.html'

@method_decorator([login_required, business_user_permission],name='dispatch')
class EMIReportAppData(BaseEMIReportAppData):
	ajax_url = 'business_user:emi-report-ajax'
	action_url = 'business_user:business_application_details'
	template_name = 'business_dev/reports/emi_report.html'

@method_decorator([login_required, business_user_permission],name='dispatch')
class EMIReportAppAjaxData(BaseEMIReportAppAjaxData):
	token = emi_report_paging(ajax_url = 'business_user:def-doc-sub-ajax',action_url = 'business_user:business_application_details').token

@method_decorator([login_required, business_user_permission,],name='dispatch')
class BD_DMRCertification(BaseDMRCertification):
	template_name = 'business_dev/reports/dmr_certification.html'

@method_decorator([login_required, business_user_permission,],name='dispatch')
class BD_DMRCluster(BaseDMRCluster):
	template_name = 'business_dev/reports/dmr_cluster.html'

@method_decorator([login_required, business_user_permission,],name='dispatch')
class BD_DMRSpecific(BaseDMRSpecific):
	template_name = 'business_dev/reports/dmr_specific.html'

@method_decorator([login_required, business_user_permission],name='dispatch')
class ProgramAdmissionsReport(BaseProgramAdmissionReport):
	template_name = 'business_dev/reports/pgm_adm_report.html'
	ajax_url = 'business_user:program-admissions-report-ajax'

@method_decorator([login_required, business_user_permission],name='dispatch')
class ProgramAdmissionsReportAjax(BasePgmAdmReportAjaxData):
	token = pgm_adm_report_paging(ajax_url='business_user:program-admissions-report-ajax',).token

@method_decorator([login_required, reviewer_or_payment_reviewer_permission_report],name='dispatch')
class EMIReportEduvAppData(BaseEMIReportEduvAppData):	
	template_name = 'business_dev/reports/emi_eduv_report.html'
	ajax_url = 'business_user:emi-report-eduv-ajax'
	action_url = 'business_user:review_application_details'


@method_decorator([login_required, reviewer_or_payment_reviewer_permission_report],name='dispatch')
class EMIReportEduvAppAjaxData(BaseEMIReportEduvAppAjaxData):
	token = eduv_report_paging(ajax_url='business_user:emi-report-eduv-ajax', action_url = 'business_user:review_application_details').token

@method_decorator([login_required, reviewer_or_payment_reviewer_permission_report],name='dispatch')
class EMIReportEzcredAppData(BaseEMIReportEzcredAppData):	
	template_name = 'business_dev/reports/emi_ezcred_report.html'
	ajax_url = 'business_user:emi-report-ezcred-ajax'
	action_url = 'business_user:business_application_details'

@method_decorator([login_required, reviewer_or_payment_reviewer_permission_report],name='dispatch')
class EMIReportEzcredAppAjaxData(BaseEMIReportEzcredAppAjaxData):
	token = ezcred_report_paging(ajax_url='business_user:emi-report-ezcred-ajax', action_url = 'business_user:business_application_details').token

@method_decorator([login_required, reviewer_or_payment_reviewer_permission_report],name='dispatch')
class EMIReportPropelldAppData(BaseEMIReportPropelldAppData):	
	template_name = 'business_dev/reports/emi_propelld_report.html'
	ajax_url = 'business_user:emi-report-propelld-ajax'
	action_url = 'business_user:business_application_details'

@method_decorator([login_required, reviewer_or_payment_reviewer_permission_report],name='dispatch')
class EMIReportPropelldAppAjaxData(BaseEMIReportPropelldAppAjaxData):
	token = propelld_report_paging(ajax_url='business_user:emi-report-propelld-ajax', action_url = 'business_user:business_application_details').token
