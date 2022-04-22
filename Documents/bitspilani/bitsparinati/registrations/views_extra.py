from django.shortcuts import render, redirect
from django.db import IntegrityError, transaction
from django.core.urlresolvers import reverse
from djqscsv import render_to_csv_response
from django_mysql.models import GroupConcat
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.db.models import Max, Value,Count,F,Q,CharField,Case,When,Sum,DateTimeField
from django.db.models.functions import Concat
from datetime import datetime as dt
from datetime import date, timedelta
from registrations.models import *
from .forms import *
from import_export.tmp_storages import MediaStorage as MS
from .bits_decorator import *
from django.views.decorators.cache import never_cache
from dateutil.parser import parse
from django.conf import settings
from django.http import JsonResponse,HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST, require_GET
from celery.result import AsyncResult
from django.core.serializers.json import DjangoJSONEncoder
from table.views import FeedDataView
from django.utils import timezone
from .tables import *
from import_export.tmp_storages import  *
from django.contrib.auth.decorators import login_required
from registrations.dynamic_dmr_report import *
from registrations.dynamic_views import BaseDeffDocsUpload, BaseDeferredReviewData
from registrations.tables_ajax import *
from bits_admin.dynamic_views import (BaseDefDocsAppData, BaseElectiveSelectionsAppData, 
	BaseDefDocsSubData,BaseEMIReportAppData, BasePreSelAppData, BaseEMIReportEduvAppData,BaseEMIReportEzcredAppData, BaseEMIReportPropelldAppData,BaseApplicationAdminArchiveView)
from bits_admin.tables_ajax import (DefDocView, BaseElectiveSelectionsAppAjaxData, 
	BaseEMIReportAppAjaxData, DefDocSubView, PreSelAppView, BaseEMIReportEduvAppAjaxData,BaseEMIReportEzcredAppAjaxData,BaseEMIReportPropelldAppAjaxData)
from bits_admin.tables import def_doc_paging, doc_sub_paging, emi_report_paging , pre_sel_paging , eduv_report_paging,ezcred_report_paging,propelld_report_paging
from bits_admin.forms import program_filter_form
from django.utils.decorators import method_decorator
from registrations.utils import offer_letter as ol
import json
import datetime
import logging
import tablib
import operator
logger = logging.getLogger("main")


@method_decorator([login_required, reviewer_or_payment_reviewer_permission_report],name='dispatch')
class DMR(BaseDMR):
	template_name = 'reviewer/dmr_report.html'

@method_decorator([login_required, reviewer_or_payment_reviewer_permission_report],name='dispatch')
class DMRNonSpecific(BaseDMRNonSpecific):
	template_name = 'reviewer/dmr_non_specific.html'
	form_class = DMRNonSpecificForm

	def get_context_data(self, **kwargs):
		context = super(DMRNonSpecific, self).get_context_data(**kwargs)
		context['form'] = self.form_class(initial=self.request.GET)
		return context


@method_decorator([login_required,reviewer_or_payment_reviewer_permission_report],name='dispatch')
class WaiverReportDataView(BaseWaiverReportDataView):
	token = waiver_report_table().token

@method_decorator([login_required, reviewer_or_payment_reviewer_permission_report],name='dispatch')
class WaiverReport(BaseWaiverReport):
	template_name = 'reviewer/fee_waiver_report.html'
	form_class = ELOA_AdmitBatchForm

@method_decorator([login_required,reviewer_or_payment_reviewer_permission_report],name='dispatch')
class MilestoneView(BaseMilestoneView):
	token = milestone_report_table().token

@method_decorator([login_required,reviewer_or_payment_reviewer_permission_report],name='dispatch')
class ApplicationMilestoneReport(BaseApplicationMilestoneReport):
	template_name = 'reviewer/milestone_report.html'

@method_decorator([login_required,reviewer_or_payment_reviewer_permission_report],name='dispatch')
class ProgChangeReportAjax(BaseProgChangeReport):
	token = prog_change_report_paging().token

@method_decorator([login_required,reviewer_or_payment_reviewer_permission_report],name='dispatch')
class ProgramChangeReport(BaseProgramChangeReport):
	template_name = 'reviewer/prog_change_report.html'

@method_decorator([login_required,reviewer_or_payment_reviewer_permission_report],name='dispatch')
class ProgramLocationReportAjax(BaseProgramLocationReportAjax):
	token = prog_loc_report().token

@method_decorator([login_required,reviewer_or_payment_reviewer_permission_report],name='dispatch')
class ProgramLocationReport(BaseProgramLocationReport):
	template_name = 'reviewer/prog_loc_report.html'

@method_decorator([login_required,reviewer_or_payment_reviewer_permission_report],name='dispatch')
class AEView(BaseAEView):
	token = ApplcantExceptionTable().token

@method_decorator([login_required,reviewer_or_payment_reviewer_permission_report],name='dispatch')
class ApplicationExceptionView(BaseApplicationExceptionView) :
	template_name = 'reviewer/application_exception_table.html'
	
@login_required
@reviewer_permission
@require_POST
def bulk_regenerate(request):

	def inner_program_data(cs, pg, ap_exp):
		try:
			template_name = (
					ap_exp.offer_letter or 
					ap_exp.transfer_program.offer_letter_template or 
					cs.application.program.offer_letter_template
			)
			return (get_program_data(cs, pg), template_name)

		except (
			ApplicantExceptions.DoesNotExist, 
			ProgramLocationDetails.DoesNotExist,
			PROGRAM_FEES_ADMISSION.DoesNotExist
			) as e: 
			return None

	
	pg_id = request.POST.get('reg-prog',None)
	cs = CandidateSelection.objects.filter(
		application__program__pk = int(pg_id),
		application__application_status__in =[settings.APP_STATUS[9][0],
		settings.APP_STATUS[11][0]],
		) 
	for x in cs:
		template_name = x.application.program.offer_letter_template
		try:
			pfa, pld = get_program_data(x,x.application.program)
			ap_exp = ApplicantExceptions.objects.get(
				applicant_email=x.application.login_email.email,
				program=x.application.program
			)

			template_name = ap_exp.offer_letter or template_name

			if ap_exp.transfer_program:
				(pfa, pld), template_name = inner_program_data(x, ap_exp.transfer_program, ap_exp) or ((pfa, pld,), template_name)

		except (
			ApplicantExceptions.DoesNotExist, 
			ProgramLocationDetails.DoesNotExist,
			PROGRAM_FEES_ADMISSION.DoesNotExist
			) as e: pass

		else:
			x.fee_payment_deadline_dt = pld.fee_payment_deadline_date
			x.orientation_dt = pld.orientation_date
			x.lecture_start_dt = pld.lecture_start_date
			x.orientation_venue = pld.orientation_venue
			x.lecture_venue = pld.lecture_venue
			x.admin_contact_person = pld.admin_contact_person
			x.acad_contact_person = pld.acad_contact_person
			x.admin_contact_phone = pld.admin_contact_phone
			x.acad_contact_phone = pld.acad_contact_phone
			x.adm_fees = pfa.fee_amount
			x.offer_letter_generated_flag = True
			x.offer_letter_regenerated_dt = timezone.now()
			x.offer_letter_template = template_name
			x.offer_letter = ol.render_offer_letter_content(x)
			x.save()

	return redirect(reverse('registrationForm:review-applicant-data'))

def get_program_data(cs,prog):

	pld = ProgramLocationDetails.objects.get(
			program=prog,
			location=cs.application.current_location
		)
	pfa = PROGRAM_FEES_ADMISSION.objects.get(program=prog,
			fee_type='1',
			latest_fee_amount_flag=True
		)

	return pfa, pld 

@login_required
@reviewer_permission
def rev_regen_offer(request,ap_id=None):
	cs = CandidateSelection.objects.get(application__pk=int(ap_id))
	template_name = cs.application.program.offer_letter_template
	try:
		pfa,pld=get_program_data(cs,cs.application.program)
		ap_exp = ApplicantExceptions.objects.get(applicant_email=cs.application.login_email.email,
			program = cs.application.program)
		template_name = ap_exp.offer_letter or template_name

		if ap_exp.transfer_program:
			pfa,pld=get_program_data(cs,ap_exp.transfer_program)
			template_name = (
					ap_exp.offer_letter or 
					ap_exp.transfer_program.offer_letter_template or 
					cs.application.program.offer_letter_template
			)
								
	except (
			ApplicantExceptions.DoesNotExist,
			PROGRAM_FEES_ADMISSION.DoesNotExist,
			ProgramLocationDetails.DoesNotExist,
			) as e:
			pfa,pld=get_program_data(cs,cs.application.program)

	cs.fee_payment_deadline_dt = pld.fee_payment_deadline_date
	cs.orientation_dt = pld.orientation_date
	cs.lecture_start_dt = pld.lecture_start_date
	cs.orientation_venue = pld.orientation_venue
	cs.lecture_venue = pld.lecture_venue
	cs.admin_contact_person = pld.admin_contact_person
	cs.acad_contact_person = pld.acad_contact_person
	cs.admin_contact_phone = pld.admin_contact_phone
	cs.acad_contact_phone = pld.acad_contact_phone
	cs.adm_fees = pfa.fee_amount
	cs.offer_letter_generated_flag = True
	cs.offer_letter_regenerated_dt = timezone.now()
	cs.offer_letter_template = template_name
	cs.offer_letter = ol.render_offer_letter_content(cs)
	cs.save()

	return redirect(reverse_lazy('reviewer:review_application_details',
		kwargs={'application_id':cs.application.id,
			'alert_status':1}))

@method_decorator([login_required,],name='dispatch')
class DeffDocsUpload(BaseDeffDocsUpload):
    template_name = 'registrations/deff_docs_upload.html'

@method_decorator([login_required, reviewer_permission],name='dispatch')
class ElectiveSelectionsAppData(BaseElectiveSelectionsAppData):
	success_url = reverse_lazy('reviewer:view-elective-selections')
	template_name = 'reviewer/elective_selections_app_view.html'

	def get_context_data(self, query=None, program=None, **kwargs):
		context = super(ElectiveSelectionsAppData, self).get_context_data(query=query, program=program,**kwargs)
		SCATable = elective_selections_paging(programs=program,)
		context['table'] = SCATable(query)
		return context 

@method_decorator([login_required, reviewer_permission], name='dispatch')
class ElectiveSelectionsAppAjaxData(BaseElectiveSelectionsAppAjaxData):
	token = elective_selections_paging().token

@method_decorator([login_required, reviewer_permission],name='dispatch')
class DefDocsAppAjaxData(DefDocView):
	token = def_doc_paging(ajax_url = 'reviewer:def-doc-ajax',action_url = 'registrationForm:review_application_details').token

@method_decorator([login_required, reviewer_permission], name='dispatch')
class DefDocsSubAjaxData(DefDocSubView):
	token = doc_sub_paging(ajax_url = 'reviewer:def-doc-sub-ajax',action_url = 'registrationForm:review_application_details').token

@method_decorator([login_required, reviewer_permission],name='dispatch')
class DefDocsAppData(BaseDefDocsAppData):
	template_name = 'reviewer/def_doc_app_view.html'
	ajax_url = 'reviewer:def-doc-ajax'
	action_url = 'registrationForm:review_application_details'

@method_decorator([login_required, reviewer_permission], name='dispatch')
class DefDocsSubData(BaseDefDocsSubData):
	ajax_url = 'reviewer:def-doc-sub-ajax'
	action_url = 'registrationForm:review_application_details'
	template_name = 'reviewer/def_doc_fields_view.html'

@method_decorator([login_required, reviewer_permission],name='dispatch')
class EMIReportAppData(BaseEMIReportAppData):
	ajax_url = 'reviewer:emi-report-ajax'
	action_url = 'registrationForm:review_application_details'
	template_name = 'reviewer/emi_report.html'

@method_decorator([login_required, reviewer_permission],name='dispatch')
class EMIReportAppAjaxData(BaseEMIReportAppAjaxData):
	token = emi_report_paging(ajax_url = 'reviewer:emi-report-ajax',action_url = 'registrationForm:review_application_details').token

@method_decorator([login_required, reviewer_permission], name='dispatch')
class DeferredApplicationDetails(BaseDeferredReviewData):
	template_name = 'registrations/deff_review_application_form_view.html'

@method_decorator([login_required, reviewer_permission], name='dispatch')
class PreSelAppData(BasePreSelAppData):
	template_name = 'reviewer/pre_sel_rej_view.html'
	ajax_url = 'reviewer:pre-sel-rej-app-ajax'
	action_url = 'registrationForm:review_application_details'

@method_decorator([login_required, reviewer_permission], name='dispatch')
class PreSelAppAjaxData(PreSelAppView):
	token = pre_sel_paging(ajax_url='reviewer:pre-sel-rej-app-ajax', action_url='registrationForm:review_application_details').token

@method_decorator([login_required, reviewer_or_payment_reviewer_permission_report],name='dispatch')
class Rev_DMRCertification(BaseDMRCertification):
	template_name = 'reviewer/dmr_certification.html'

@method_decorator([login_required, reviewer_or_payment_reviewer_permission_report],name='dispatch')
class Rev_DMRCluster(BaseDMRCluster):
	template_name = 'reviewer/dmr_cluster.html'

@method_decorator([login_required, reviewer_or_payment_reviewer_permission_report],name='dispatch')
class Rev_DMRSpecific(BaseDMRSpecific):
	template_name = 'reviewer/dmr_specific.html'

@method_decorator([login_required, reviewer_or_payment_reviewer_permission_report],name='dispatch')
class ProgramAdmissionsReport(BaseProgramAdmissionReport):
	template_name = 'reviewer/pgm_adm_report.html'
	ajax_url = 'reviewer:program-admissions-report-ajax'

@method_decorator([login_required, reviewer_or_payment_reviewer_permission_report],name='dispatch')
class ProgramAdmissionsReportAjax(BasePgmAdmReportAjaxData):
	token = pgm_adm_report_paging(ajax_url='reviewer:program-admissions-report-ajax',).token


@method_decorator([login_required, reviewer_or_payment_reviewer_permission_report],name='dispatch')
class EMIReportEduvAppData(BaseEMIReportEduvAppData):	
	template_name = 'reviewer/emi_eduv_report.html'
	ajax_url = 'reviewer:emi-report-eduv-ajax'
	action_url = 'registrationForm:review_application_details'


@method_decorator([login_required, reviewer_or_payment_reviewer_permission_report],name='dispatch')
class EMIReportEduvAppAjaxData(BaseEMIReportEduvAppAjaxData):
	token = eduv_report_paging(ajax_url='reviewer:emi-report-eduv-ajax', action_url = 'registrationForm:review_application_details').token

@method_decorator([login_required, reviewer_or_payment_reviewer_permission_report],name='dispatch')
class ApplicationAdminArchiveView(BaseApplicationAdminArchiveView):
	template_name = 'reviewer/bits_archived/applicant_archive.html'

@method_decorator([login_required, reviewer_or_payment_reviewer_permission_report],name='dispatch')
class EMIReportEzcredAppData(BaseEMIReportEzcredAppData):	
	template_name = 'reviewer/emi_ezcred_report.html'
	ajax_url = 'reviewer:emi-report-ezcred-ajax'
	action_url = 'registrationForm:review_application_details'

@method_decorator([login_required, reviewer_or_payment_reviewer_permission_report],name='dispatch')
class EMIReportEzcredAppAjaxData(BaseEMIReportEzcredAppAjaxData):
	token = ezcred_report_paging(ajax_url='reviewer:emi-report-ezcred-ajax', action_url = 'registrationForm:review_application_details').token

@method_decorator([login_required, staff_member_required],name='dispatch')
class EMIReportPropelldAppData(BaseEMIReportPropelldAppData):	
	template_name = 'bits_admin/emi_propelld_report.html'
	ajax_url = 'bits_admin_payment:emi-report-propelld-ajax'
	action_url = 'bits_admin:admin-application-views'

@method_decorator([login_required, staff_member_required],name='dispatch')
class EMIReportPropelldAppAjaxData(BaseEMIReportPropelldAppAjaxData):
	token = propelld_report_paging(ajax_url='bits_admin_payment:emi-report-propelld-ajax', action_url = 'bits_admin:admin-application-views').token	