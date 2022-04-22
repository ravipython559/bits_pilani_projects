from django.shortcuts import render, redirect, HttpResponseRedirect
from django.views.generic import TemplateView, View, FormView
from django.core.urlresolvers import reverse_lazy
from semester_api import zest_settings as ZEST
from semester_api.zest_utils import emi_in_progress, emi_in_none, update_approved_emi,emi_in_cancellation
from semester_api.models import SemMetaZest, SemZestEmiTransaction, SemPaytmTransactions
from django.http import HttpResponsePermanentRedirect
from semester_api.zest_api import ZestCreateLoan,sem_ZestCallBack
from django.http import JsonResponse
from table.views import FeedDataView
from semester_api.tables import SemZestEmiTable
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.db.models import Q, Max
from bits_rest import zest_statuses as ZS 
import operator
import hashlib
from djqscsv import render_to_csv_response
from django.utils import timezone
from .zest_api import ZestDeleteLoan
from bits_rest.viewsets.paytm import Checksum
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.conf import settings
import uuid
import urllib
from datetime import date, timedelta

# Create your views here.
@method_decorator([csrf_exempt, never_cache,],name='dispatch')
class ZestCreateEMI(View):
	errors_list = None
	zest_error_model = SemMetaZest
	def authenticate_user(self, request, *args, **kwargs):
		is_valid = True
		self.student_id = request.POST.get('student_id')
		self.email = request.POST.get('email')
		self.pincode = request.POST.get('pincode')
		self.b_amount = request.POST.get('basket_amount')
		self.mobile = request.POST.get('mobile')
		key = request.POST.get('key')
		return is_valid

	def cor_json_request(self, response):
		response["Access-Control-Allow-Origin"] = "*"
		response["Access-Control-Allow-Methods"] = "POST"
		response["Access-Control-Max-Age"] = "1000"
		response["Access-Control-Allow-Headers"] = "*"
		return response 


	def post(self, request, *args, **kwargs):

		if self.authenticate_user(request, *args, **kwargs):

			try:
				update_approved_emi(self.student_id)
			except Exception as e:
				pass

			if emi_in_progress(self.student_id) or emi_in_none(self.student_id):
				zest_link = SemZestEmiTransaction.objects.filter(student_id=self.student_id).exclude(status__in=ZS.cancelled_status).exclude(status='Declined').last()
				if zest_link:
					if zest_link.zest_emi_link:
						response = JsonResponse({'return_url':zest_link.zest_emi_link})
						return self.cor_json_request(response)
					else:
						response = JsonResponse({'return_url':ZEST.ZEST_PORTAL_LINK})
						return self.cor_json_request(response)
				else:
						response = JsonResponse({'return_url':ZEST.ZEST_PORTAL_LINK})
						return self.cor_json_request(response)
			try:
				emi = ZestCreateLoan(self.student_id, self.email, self.b_amount, self.pincode, self.mobile)
				response = JsonResponse({'return_url':emi()})
				return self.cor_json_request(response)
			except Exception as e:
				error = None
				if emi.error_request.status_code == 400:
					error = emi.error_request.json()
				errors_list = {'request_error':str(e), 'zest_error':error, 'occured': 'while creation'}
						
				self.zest_error_model.objects.create(student_id=self.student_id, errors=errors_list)

		response = JsonResponse({'error': "validation failed"}, status=400)
		return self.cor_json_request(response)


@method_decorator([csrf_exempt, never_cache,],name='dispatch')
class ZestStatusEMI(View):
	def post(self, request, *args, **kwargs):
		zest = SemZestEmiTransaction.objects.filter(Q(status__in=ZS.inprogress_status)|Q(status__isnull=True)).order_by('-requested_on')
		created_datetime=date.today()-timedelta(days=30)
		a = zest.filter(requested_on__gt=created_datetime)
		student_ids = a.values_list('student_id', flat=True).distinct()
		for student_id in student_ids.iterator():
			update_approved_emi(student_id)
		return redirect(reverse_lazy('semester_api:emi-report'))

class EMIReportAppData(TemplateView):
	zet_model = SemZestEmiTransaction
	template_name = 'semester_api/emi_report.html'


	def get(self, request, *args, **kwargs):

		if 'applicant_report' in request.GET:
			time_threshold = timezone.now() - timedelta(days=60)
			semzestemitransaction_object = SemZestEmiTransaction.objects.filter(requested_on__gte=time_threshold)

			active = semzestemitransaction_object.filter(status='Active')

			in_progress = semzestemitransaction_object.filter(
				Q(status__in=ZS.inprogress_status)|Q(status__isnull=True)
			)
			in_progress = in_progress.exclude(
				student_id__in=active.values_list('student_id', flat=True)
			) if active.exists() else in_progress

			cancelled = semzestemitransaction_object.filter(status__in=ZS.cancelled_status)
			cancelled = cancelled.exclude(
				student_id__in=in_progress.values_list('student_id', flat=True)
			) if in_progress.exists() else cancelled
			cancelled = cancelled.exclude(
				student_id__in=active.values_list('student_id', flat=True)
			) if active.exists() else cancelled

			query = reduce(operator.or_, (x for x in [active, in_progress, cancelled, semzestemitransaction_object] if x.exists()))

			students = query.values('student_id').annotate(max_date=Max('requested_on'))

			query = SemZestEmiTransaction.objects.filter(
				reduce(operator.or_,
					(
						Q(
							student_id=x['student_id'], 
							requested_on=x['max_date']
						) for x in students.iterator()
					)
				),
				requested_on__gte=time_threshold,
			)
			search = request.GET.get('hidden_search') or None
			query = query.filter(
				reduce(operator.and_, (
						Q(student_id__icontains=item)|
						Q(order_id__icontains=item)|
						Q(status__icontains=item)
						for item in search.strip().split()
					)
				) 
			) if search else query

			return render_to_csv_response(
				(
					query.values('student_id','requested_on','order_id','status','approved_or_rejected_on')
					if query.exists()
					else query.values('student_id','requested_on','order_id','status','approved_or_rejected_on').none()
				),
				field_header_map={
					'student_id':'Student ID',
					'requested_on':'Loan Applied On',
					'order_id':'Zest Order ID',
					'status':'Current Loan Status',
					'approved_or_rejected_on':'Approved On',
				},
				field_serializer_map={
					'requested_on': (lambda x: timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p")),
					'status': (lambda x:dict(ZS.ZEST_DISPLAY_STATUS_CHOICES).get(x, '-')),
					'approved_or_rejected_on': (lambda x: timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p")),
				}
			)
		else:
			return super(EMIReportAppData, self).get(request, table=SemZestEmiTable, *args, **kwargs)

class AjaxEMIReport(FeedDataView):
	token = SemZestEmiTable.token

	def get_queryset(self):
		time_threshold = timezone.now() - timedelta(days=60)
		semzestemitransaction_object = SemZestEmiTransaction.objects.filter(requested_on__gte=time_threshold)
		return semzestemitransaction_object

@method_decorator([csrf_exempt, never_cache,],name='dispatch')
class ZestEMIStatus(View):
	model = SemZestEmiTransaction

	def cor_json_request(self, response):
		response["Access-Control-Allow-Origin"] = "*"
		response["Access-Control-Allow-Methods"] = "GET"
		response["Access-Control-Max-Age"] = "1000"
		response["Access-Control-Allow-Headers"] = "*"
		return response

	def get(self, request, *args, **kwargs):
		student_id = request.GET.get('student_id')
		update_approved_emi(student_id)
		zest_inprogress = self.model.objects.filter(
			Q(status__in=ZS.inprogress_status)|Q(status__isnull=True),
			student_id=student_id,
		)

		zest_complete = self.model.objects.filter(
			status__in=[ZS.Approved, ZS.Active],
			student_id=student_id,
		)

		response = JsonResponse({
			'zest_inprogress':zest_inprogress.exists(),
			'zest_complete':zest_complete.exists(),
			'is_in_delete_status':emi_in_cancellation(student_id),
		})

		return self.cor_json_request(response)

@method_decorator([csrf_exempt, never_cache,],name='dispatch')
class ZestDeleteEMI(View):
	model = SemZestEmiTransaction

	def cor_json_request(self, response):
		response["Access-Control-Allow-Origin"] = "*"
		response["Access-Control-Allow-Methods"] = "POST"
		response["Access-Control-Max-Age"] = "1000"
		response["Access-Control-Allow-Headers"] = "*"
		return response 

	def post(self, request, *args, **kwargs):
		student_id = request.POST.get('student_id')

		if emi_in_cancellation(student_id):
			emi = ZestDeleteLoan(student_id)
			emi()
			response = JsonResponse({'msg': "Cancellation in process"})
		else:
			response = JsonResponse({'msg': "Cancellation not allowed at this stage"})
		return self.cor_json_request(response)


@method_decorator([csrf_exempt, never_cache,],name='dispatch')
class ZestCallbackView(View):
	sha512 = lambda self, o_id, sec_key, status: hashlib.sha512(
		'{o_id}|{sec_key}|{status}'.format(
			o_id=o_id, 
			sec_key=sec_key, 
			status=status
		)
	).hexdigest()

	def post(self, request, *args, **kwargs):
		o_id = request.POST.get('orderno')
		status = request.POST.get('status')
		key = request.POST.get('key')
		sec_key = ZEST.ZEST_TO_MERCHANT
		if self.sha512(o_id, sec_key, status)==key:
			try:
				zest = SemZestEmiTransaction.objects.get(order_id=o_id)
				update_approved_emi(zest.student_id)

				# callback_meta = zest.callback_meta or []
				# callback_meta.append(dict(self.request.POST.iterlists()))
				# zest.callback_meta = callback_meta

				# if status == ZS.Active:
				# 		zest.approved_or_rejected_on = timezone.localtime(timezone.now())
				# 		zest.is_terms_and_condition_accepted = True
				# 		zest.is_approved = True
				# 		zest.status = status
				# 		zest.save()

				# elif status=='Declined':
				# 	zest.approved_or_rejected_on = timezone.localtime(timezone.now())

				# zest.status = status
				# zest.save()

				return JsonResponse({'status':'success', 'msg':'success'})
			except Exception as e:
				SemMetaZest.objects.create(student_id=o_id, errors=e.message)
				return JsonResponse({'status':'failed', 'msg':'failed','error_message':e.message})
		else:
			status_msg = 'sha512 key matched: {}'.format('failed')
			SemMetaZest.objects.create(student_id=o_id, errors={'status':'failed', 'msg':status_msg})
			return JsonResponse({'status':'failed', 'msg':status_msg})
		return JsonResponse({'status':'failed', 'msg':'failed'})

@method_decorator([csrf_exempt, never_cache,],name='dispatch')
class PaytmCreateView(View):

	def cor_json_request(self, response):
		response["Access-Control-Allow-Origin"] = "*"
		response["Access-Control-Allow-Methods"] = "GET"
		response["Access-Control-Max-Age"] = "1000"
		response["Access-Control-Allow-Headers"] = "*"
		return response

	def post(self, request, *args, **kwargs):
		params = {}
		if request.POST.get("student_id") and request.POST.get("email") and request.POST.get("mobile") and request.POST.get("amount") and request.POST.get('redirect_url') and request.POST.get("order_id"):
			params['student_id'] = request.POST.get("student_id")
			params['email'] = request.POST.get("email")
			params['mobile'] = request.POST.get("mobile")
			params['amount'] = request.POST.get("amount")
			params['redirect_url'] = request.POST.get("redirect_url")
			params['order_id'] = request.POST.get("order_id")
			url = 'http%s://%s%s' % ('s' if request.is_secure() else '',
				request.get_host(),reverse_lazy('semester_api:paytm-integration'))
			url = "{0}?order_id={1}".format(url, params['order_id'])
			try:
				paytm_obj = SemPaytmTransactions.objects.get(order_id=params['order_id'])
				if paytm_obj:
					response= JsonResponse({'error': "validation failed", "message": "order_id {0} couldn't be duplicate".format(params['order_id'])}, status=400)
			except SemPaytmTransactions.DoesNotExist as e:
				SemPaytmTransactions.objects.create(order_id=params['order_id'], student_id=params['student_id'],
					email=params['email'], mobile=params['mobile'], request_amount=params['amount'],
					created_on=timezone.now(), status='ORDER_ID_CREATED', redirect_url= params['redirect_url'])
				response= JsonResponse({'status':'success', 'return_url':url, 'order_id':params['order_id']})
		else:
			response= JsonResponse({'error': "validation failed", "message": "student_id , email, mobile, amount, redirect_url, order_id fields are require mandatory"}, status=400)

		return self.cor_json_request(response)


@method_decorator([csrf_exempt, never_cache,],name='dispatch')
class paytmIntegration(TemplateView):
	template_name = 'semester_api/payment.html'
	order_id=None

	def get_context_data(self, **kwargs):
		context = super(paytmIntegration, self).get_context_data(**kwargs)
		paytm_data = SemPaytmTransactions.objects.get(order_id=self.order_id)
		data_dict = {
			"MID": settings.PAYTM_MERCHANT_ID,
			"ORDER_ID": paytm_data.order_id,
			"TXN_AMOUNT": paytm_data.request_amount,
			"CUST_ID": paytm_data.student_id,
			"INDUSTRY_TYPE_ID": settings.PAYTM_INDUSTRY_TYPE_ID,
			"WEBSITE": settings.PAYTM_WEBSITE,
			"CHANNEL_ID":"WEB",
			"MOBILE_NO" : paytm_data.mobile,
			"EMAIL" : paytm_data.email,
			"CALLBACK_URL": self.get_callback(),
		}
		param_dict = data_dict
		param_dict['CHECKSUMHASH'] = Checksum.generate_checksum(data_dict, settings.PAYTM_MERCHANT_KEY)
		context['paytmdict'] = param_dict
		context['PAYTM_PAYMENT_URL'] = settings.PAYTM_PAYMENT_URL
		paytm_data.status = 'PAYMENT_INITIATED'
		paytm_data.save()
		return context

	def get_callback(self):
		return 'http%s://%s%s' % ('s' if self.request.is_secure() else 's',
			self.request.get_host(), str(reverse_lazy('semester_api:paytm-callback'))
			)

	def get(self, request, *args, **kwargs):
		self.order_id= request.GET.get('order_id')
		return super(paytmIntegration, self).get(request, *args, **kwargs)


class CallBack(View):

	def post(self, request, *args, **kwargs):
		data_dict = { k:v for k,v in request.POST.items() }
		verify = Checksum.verify_checksum(
			data_dict, settings.PAYTM_MERCHANT_KEY,
			data_dict['CHECKSUMHASH']
		)
		if verify:
			self.update_models(data_dict)
			if data_dict.has_key('STATUS'):
				paytm_app = SemPaytmTransactions.objects.get(order_id=data_dict['ORDERID'])
				data_dict['STUDENT_ID'] = paytm_app.student_id
				data_dict_item = data_dict.items()
				encoded_url_params = urllib.urlencode(data_dict_item)
				if data_dict['STATUS'] == u'TXN_SUCCESS':
					url = paytm_app.redirect_url+"?"+encoded_url_params
					return HttpResponseRedirect(url)
				else:
					url = paytm_app.redirect_url+"?"+encoded_url_params
					return HttpResponseRedirect(url)
		else:
			return JsonResponse("checksum verify failed")

@method_decorator([csrf_exempt,], name='dispatch')
class paytmCallback(CallBack):
	def update_models(self, data_dict):
		with transaction.atomic():
			paytm_app = SemPaytmTransactions.objects.get(order_id=data_dict['ORDERID'])
			paytm_app.resp_json=data_dict
			if data_dict.has_key('TXNAMOUNT'):
				paytm_app.transaction_amount=data_dict['TXNAMOUNT']
			if data_dict.has_key('MID'):
				paytm_app.merchant_id=data_dict['MID']
			if data_dict.has_key('TXNDATE'):
				paytm_app.transaction_date=data_dict['TXNDATE']
			if data_dict.has_key('STATUS'):
				paytm_app.status=data_dict['STATUS']
			if data_dict.has_key('BANKNAME'):
				paytm_app.bank_name=data_dict['BANKNAME']
			if data_dict.has_key('PAYMENTMODE'):
				paytm_app.payment_mode=data_dict['PAYMENTMODE']
			if data_dict.has_key('BANKTXNID'):
				paytm_app.bank_transaction_id=data_dict['BANKTXNID']
			if data_dict.has_key('TXNID'):
				paytm_app.transaction_id=data_dict['TXNID']
			if data_dict.has_key('CURRENCY'):
				paytm_app.currency=data_dict['CURRENCY']
			if data_dict.has_key('RESPMSG'):
				paytm_app.response_message=data_dict['RESPMSG']
			if data_dict.has_key('GATEWAYNAME'):
				paytm_app.gateway_name=data_dict['GATEWAYNAME']
			paytm_app.save()

@method_decorator([csrf_exempt, never_cache,],name='dispatch')
class paytmStatus(View):
	def cor_json_request(self, response):
		response["Access-Control-Allow-Origin"] = "*"
		response["Access-Control-Allow-Methods"] = "GET"
		response["Access-Control-Max-Age"] = "1000"
		response["Access-Control-Allow-Headers"] = "*"
		return response

	def get(self, request, *args, **kwargs):
		if request.GET.get('order_id'):
			order_id = request.GET.get('order_id')
			try:
				paytm_obj = SemPaytmTransactions.objects.get(order_id=order_id)
				response= JsonResponse({'status': paytm_obj.status, 'order_id': paytm_obj.order_id})
			except SemPaytmTransactions.DoesNotExist as e:
				response= JsonResponse({'status':'failed', 'message':'order_id is not found'}, status=404)
		else:
			response= JsonResponse({'error': "validation failed", "message": "order_id param require mandatory"})
		return self.cor_json_request(response)
