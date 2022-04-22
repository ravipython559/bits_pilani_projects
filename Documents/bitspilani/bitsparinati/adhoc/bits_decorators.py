from registrations.models import OtherFeePayment, CandidateSelection
from django.shortcuts import render, redirect, HttpResponseRedirect
from django.core import signing
from django.http import Http404
from django.db.models import Q

def is_transaction_done(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		try:
			ofp = OtherFeePayment.objects.get(pk=kwargs['pk'])
			if ofp.transaction_id:
				return render(request, 'adhoc/adhoc_bad_request.html', {'otf':ofp},)
		except Exception as e:
			return render(
				request, 'adhoc/500.html', 
				{
					'payment_error':"""
					{0} (This error occurs mostly due to interruption in payment process)
					""".format(str(e)),
					'ofp':ofp,
				},
			) 
		return view_func(request, *args, **kwargs)
	return _wrapped_view_func

def is_adhoc_payment(view_func):
	def _wrapped_view_func(request, *args, **kwargs):

		otf = OtherFeePayment.objects.filter(email=request.user.email,)
		if not otf.exists():
			return render(request, 'adhoc/no_adhoc_payment.html',)

		if not otf.filter(Q(transaction_id='')|Q(transaction_id__isnull=True)).exists():
			return render(request, 'adhoc/adhoc_bad_request.html', {'otf':otf},)

		return view_func(request, *args, **kwargs)

	return _wrapped_view_func

def is_adhoc_payment_un_registered(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		try:
			sign = signing.loads(request.COOKIES['adhoc_secret'])
			otf = OtherFeePayment.objects.get(
				email=sign['adhoc_email'], 
				program=sign['program'],
				fee_type=sign['fee_type'],
			)
			if otf.transaction_id:
				return render(request, 'adhoc/adhoc_bad_request.html', {'otf':otf},)
		except OtherFeePayment.DoesNotExist:
			return render(request, 'adhoc/no_adhoc_payment.html',)
		try:
			return view_func(request, *args, **kwargs)
		except Exception as e:
			return render(request, 'adhoc/500.html', {
				'payment_error':"""
				{0} (This error occurs mostly due to interruption in payment process)
				""".format(str(e))},) 
	return _wrapped_view_func

def redirect_token_user(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		try:
			otf = OtherFeePayment.objects.get(email=request.user.email,)
		except:
			pass

		try:
			sign = signing.loads(request.COOKIES['adhoc_secret'])
			otf = OtherFeePayment.objects.get(email=sign['adhoc_email'],)
		except:
			pass 
			
		return view_func(request, *args, **kwargs)
			
	return _wrapped_view_func

