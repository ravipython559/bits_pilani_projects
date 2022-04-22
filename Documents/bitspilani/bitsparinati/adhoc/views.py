import json
import requests
from registrations.models import *
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.db.models import Max
from django.template.loader import render_to_string
from .models import *
from django.utils import timezone
from dateutil.parser import parse as DATE_PARSE
from .bits_decorators import *
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import render
from django.views.generic import TemplateView, View
from . import zest_settings as ZEST
from .zest_utils import zest_emi_in_progress, zest_emi_in_none, update_approved_emi, login_approval_update
from .zest_api import ZestCreateLoan
from django.http import JsonResponse
from table.views import FeedDataView
from .tables import *
from django.core.urlresolvers import reverse_lazy
from django.core.serializers.json import DjangoJSONEncoder
from django.core import serializers
from django.db.models import Value
from django.db.models.functions import Concat
from registrations.utils.encoding_pdf import BasePDFTemplateView

import phonenumbers
from .forms import *
from .tpsl import *
import logging
import uuid
import decimal
import re
import json

class AdhocAjax(TemplateView):
	template_name = 'adhoc/inclusions/adhoc_form.html'

	def get_context_data(self, *args, **kwargs):
		context = super(AdhocAjax, self).get_context_data(*args, **kwargs)
		try:
			email = self.request.user.email
			is_auth_user = True
		except :
			email = self.request.GET['email']
			is_auth_user = False


		ofp = OtherFeePayment.objects.filter(email=email)

		context['form'] = ajax_AdhocStartUpForm(ofp, is_auth_user)(
			initial={
				'email':email,
				'program': self.request.GET.get('program'),
				'fee_type': self.request.GET.get('fee_type'),
			}
		)
		return context 

	def get(self, request, *args, **kwargs):
		if request.is_ajax():

			response = super(AdhocAjax, self).get(request,*args, **kwargs)

			return JsonResponse({'form': response.rendered_content,})


class AdhocTokenLogin(FormView):
	template_name = 'adhoc/home.html' 
	form_class = AdhocStartUpForm

	def get_initial(self):
		try:
			return {'email':self.request.user.email}
		except :
			return super(AdhocTokenLogin, self).get_initial()

	def get_success_url(self):
		return reverse_lazy(
			'adhoc:pay-adhoc-fee-view-token-user',
			kwargs={'pk':self.ofp.pk}
		)

	def form_valid(self, form):

		self.ofp = OtherFeePayment.objects.get(
			email=form.cleaned_data['email'],
			program=form.cleaned_data['program'],
			fee_type=form.cleaned_data['fee_type'],
		)

		return super(AdhocTokenLogin, self).form_valid(form)
	
@method_decorator([login_required, never_cache, is_adhoc_payment], name='dispatch')
class HomeRegisteredViews(AdhocTokenLogin):
	form_class = AdhocStartUpForm
	template_name = 'adhoc/home.html'

	def get_success_url(self):
		return reverse_lazy('adhoc:pay-adhoc-fee-view', kwargs={'pk':self.ofp.pk})

def direct_adhoc_payment(request):
	if request.user.is_authenticated():
		return redirect(reverse('adhoc:registered-home'))
	response = redirect(reverse('registrationForm:applicantData'))
	response.set_cookie('is_adhoc_user', True)
	return response 

class BaseZestCreateEMI(ZestMixin, AdhocMixin, BaseAdhocView):
	errors_list = None
	adhoc_error_model = AdhocMetaEmi
	form_class = AdhocZestForm
	template_name = 'adhoc/pay_adhoc_fee.html'
	error_template_name = 'adhoc/500.html'

@method_decorator([never_cache, is_transaction_done], name='dispatch')	
class ZestCreateEMI(BaseZestCreateEMI):
	pass

@method_decorator([never_cache, is_transaction_done], name='dispatch')	
class UnRegisteredZestCreateEMI(BaseZestCreateEMI):
	pass 
	
class BaseAdhocFeeView(AdhocMixin, BaseAdhocView):
	form_class = AdhocForm
	template_name = 'adhoc/pay_adhoc_fee.html'
	error_template_name = 'adhoc/500.html'

@method_decorator([never_cache, is_transaction_done], name='dispatch')
class AdhocFeeView(BaseAdhocFeeView):pass

@method_decorator([never_cache, is_transaction_done], name='dispatch')
class UnRegisteredAdhocFeeView(BaseAdhocFeeView):pass

@method_decorator([require_POST, csrf_exempt, never_cache], name='dispatch')
class AdhocPaymentReturn(AdhocMixin, BaseAdhocReturn):
	template_name = 'adhoc/adhoc_receipt.html'
	error_template_name = 'adhoc/500.html'

class BaseAdhocReportAppData(TemplateView):
	zet_model = AdhocZestEmiTransaction
	template_name = 'adhoc/emi_report.html'

	def get(self, request, *args, **kwargs):
		zests = self.zet_model.objects.filter(
			Q(status__in=ZS.inprogress_status)|
			Q(status__isnull=True)
		)
		for zest in zests.iterator():login_approval_update(zest)

		return super(BaseAdhocReportAppData, self).get(
			request, 
			table=adhoc_zest_paging(self.ajax_url)(), *args, **kwargs
		)

class BaseAjaxAdhocReport(FeedDataView):
	pass

class AdhocReceiptPdf(BasePDFTemplateView):
	template_name = "adhoc/adhoc_fee_receipt_pdf.html"
	pdf_kwargs = {'encoding' : 'utf-8',}

	def get_context_data(self, pk, **kwargs):
		context = super(AdhocReceiptPdf, self).get_context_data(pagesize="A4", title="Fee Receipt PDF", **kwargs)
		context['ofp'] = OtherFeePayment.objects.get(pk=pk)
		return context

class BaseAdhocReportEduvAppData(TemplateView):
	template_name = 'adhoc/eduvanz/emi_report_eduv.html'

	def get(self, request, *args, **kwargs):
		return super(BaseAdhocReportEduvAppData, self).get(
			request, 
			table=adhoc_eduv_paging(self.ajax_url)(), *args, **kwargs
		)

class BaseAjaxAdhocReportEduv(FeedDataView):
	pass

class BaseAdhocReportPropelldAppData(TemplateView):
	template_name = 'adhoc/propelld/emi_report_propelld.html'

	def get(self, request, *args, **kwargs):
		return super(BaseAdhocReportPropelldAppData, self).get(
			request, 
			table=adhoc_propelld_paging(self.ajax_url)(), *args, **kwargs
		)

class BaseAjaxAdhocReportPropelld(FeedDataView):
	pass
	