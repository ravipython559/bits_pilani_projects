from django.shortcuts import render, redirect
from payment_reviewer.forms import *
from .bits_decorator import *
from .tables_payment import *
from import_export.tmp_storages import  *
import tablib
import operator
from django.conf import settings
from django.db.models import *
from django.db.models.functions import Concat
from table.views import FeedDataView
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db import IntegrityError, transaction
from djqscsv import render_to_csv_response
from datetime import datetime as dt
from tempfile import NamedTemporaryFile as NTFile
from django.utils import timezone
from dateutil.parser import parse
from dateutil.tz import gettz
import logging
logger = logging.getLogger("main")

class ReconcileError(Exception):pass 

def get_choice_display(value,choices):
	for k,v in choices:
		if k==value:return v
	return "Not Found"

# upload manual and gateway payment

@staff_member_required
def upload_manual_payments(request,alert_status = None):
	result = None
	if request.method == 'POST':
		form = ManualUploadForm(request.POST,request.FILES)
		if form.is_valid():
			csv_file_name = form.cleaned_data['file'].name
			csv_file = form.cleaned_data['file'].read()
			dataset = tablib.Dataset().load(csv_file)
			resource = ManualPaymentDataUploadResource()
			result = resource.import_data(dataset, dry_run=True)

			if not result.has_errors():
				storage = MediaStorage()
				storage.save(data = csv_file)
				return redirect(
					reverse('bits_admin_payment:preview-manual-payments',
						kwargs={'file_name':storage.name,
							'csv_file_name':csv_file_name,
							}
						)
				)
	else:
		form =  ManualUploadForm()

	messages = {'confirm':'Payment data successfully imported',
		'cancel':'Import cancelled.Data deleted from application center',
		'approve':'''payments updated in application center.application 
		status updated.student ids generated for admission fee payments''',
		}

	return render(request,
		'adm_payment/upload_manual_payments.html',
		{
		'form':form,
		'result':result,
		'messages':messages.get(alert_status,None),
		})

@staff_member_required
def upload_gateway_payments(request, alert_status = None):
	result = None

	if request.method == 'POST':
		form = GatewayUploadForm(request.POST,request.FILES)
		if form.is_valid():
			def filtering_email(row):
				src_itc = row[-2].strip()
				if not src_itc:return ''
				data = src_itc.replace('{','').replace('}',',').split(',')
				ctx = dict(tuple( tuple(x.split(":"))  for x in data if x))
				return ctx.get('email','').strip()

			def filtering_application(row):
				src_itc = row[-1].strip()
				if not src_itc:return ''
				data = src_itc.replace('{','').replace('}',',').split(',')
				ctx = dict(tuple( tuple(x.split(":"))  for x in data if x))
				return ctx.get('itc','').strip()

			def filtering_mobile(row):
				src_itc = row[-3].strip() 
				if not src_itc:return ''
				data = src_itc.replace('{','').replace('}',',').split(',')
				ctx = dict(tuple( tuple(x.split(":"))  for x in data if x))
				mobile = ctx.get('mob','').strip()
				mobile = mobile if mobile.startswith('+') else '+{0}'.format(mobile.strip())
				return mobile

			def filtering_cust_name(row):
				src_itc = row[-4].strip()
				if not src_itc:return ''
				data = src_itc.replace('{','').replace('}',',').split(',')
				ctx = dict(tuple( tuple(x.split(":"))  for x in data if x))
				return ctx.get('custname','').strip()

			csv_file_name = form.cleaned_data['file'].name
			csv_file = form.cleaned_data['file'].read()
			uploaded_file = NTFile(delete=False)
			with open(uploaded_file.name, 'w') as f:f.write(csv_file)
			with open(uploaded_file.name) as f:csv_list = f.readlines()

			no_of_payment = int(csv_list[5].replace(',','').strip().split(':')[-1])
			payment_report_on = parse('{}'.format(
				csv_list[0].replace(',','').strip().split(':')[-1].strip(),
				),
				tzinfos={"IST": gettz("Asia/Kolkata")},
				dayfirst=True)
			

			csv_custom_headers = {'SR No.':'SR No.',
				'Bank Id':'Bank ID',
				'Bank Name':'Bank Name',
				'TPSL Transaction id':'TPSL Transaction ID',
				'Sm Tramsaction Id':'SM Transaction ID',
				'Bank Transaction id':'Bank Transaction ID', 
				'Charges':'Charges',
				'Total Amount': 'Total Amount',
				'Taxes':'Taxes',
				'Net Amount':'Net Amount',
				'Transaction date':'Transaction Date temp',
				'Transaction time':'Transaction time temp',
				'Payment Date':'Payment Date temp',
				'SRC ITC':'Src_itc',}

			csv_filter_list = [tuple( x.strip().split(',') ) for x in csv_list[17:-2]]
			csv_filter_header = tuple(csv_custom_headers.get(x) for x in csv_list[16].strip().split(','))

			dataset = tablib.Dataset()
			dataset.headers = csv_filter_header
			dataset.extend(csv_filter_list)
			dataset.append_col(filtering_application, header='Application ID')
			dataset.append_col(filtering_email, header='Email')
			dataset.append_col(filtering_mobile, header='Mobile')
			dataset.append_col(filtering_cust_name, header='User Name')
			dataset.append_col(lambda r: payment_report_on, header='Payment File Date')
			dataset.append_col(lambda r: '{0} {1}'.format(r[10],r[11]),
				header='Transaction Date')
			# del dataset['Src_itc']
			resource = PaymentGatewayDataUploadResource()
			result = resource.import_data(dataset, dry_run=True)
			if not result.has_errors():
				storage = MediaStorage()
				storage.save(data = dataset.csv)
				return redirect(
					reverse('bits_admin_payment:preview-gateway-payments',
						kwargs={'file_name':storage.name,
						'csv_file_name':csv_file_name,
						}
					)
				)

	else:
		form = GatewayUploadForm()

	messages = {'confirm':'payment data successfully imported',
		'cancel':'import cancelled.Data deleted from application center',
		'approve':'''payments updated in application center.application 
		status updated.student ids generated for admission fee payments''',
		}

	return render(request,
		'adm_payment/upload_gateway_payments.html',
		{
		'form':form,
		'result':result,
		'messages':messages.get(alert_status,None),
		})

# end upload manual and gateway payment

# preview upload manual and gateway payment

@staff_member_required
def preview_manual_payments(request,file_name = None,csv_file_name = None):
	if 'confirm' in request.POST:
		form = HiddenForm(request.POST)
		if form.is_valid():
			storage = MediaStorage(name = form.cleaned_data['file_name'])
			dataset = tablib.Dataset().load(storage.read())
			man_up = [ (x['Application ID'],x['Payment ID']) for x in dataset.dict ]
			resource = ManualPaymentDataUploadResource()
			result = resource.import_data(dataset, dry_run=False)
			man_up_filter = reduce(
				operator.or_,
				( 
					Q(application__student_application_id=x[0].strip(),
					payment_id=x[1].strip()) for x in man_up 
				)
			)

			ManualPaymentDataUpload.objects.filter(
				man_up_filter
				).update(
					upload_filename = csv_file_name,
					status = '1',
					uploaded_by = request.user.email,
					)
			return redirect( reverse('bits_admin_payment:hist-manual-payments',
				kwargs={'alert_status': 'confirm'}) )

	elif 'cancel' in request.POST:
		form = HiddenForm(request.POST)
		if form.is_valid():
			storage = MediaStorage(name = form.cleaned_data['file_name'])
			storage.remove()
			return redirect( reverse('bits_admin_payment:upload-manual-payments',
				kwargs={'alert_status': 'cancel'}) )
	else:
		form = HiddenForm({'file_name':file_name})
		storage = MediaStorage(name = file_name )
		dataset = tablib.Dataset().load(storage.read())
		resource = ManualPaymentDataUploadResource()
		result = resource.import_data(dataset, dry_run=True)
		
	return render(request,
		'adm_payment/preview_manual_payments.html',
		{'form' : form,'result':result,})

@staff_member_required
def preview_gateway_payments(request,file_name = None,csv_file_name = None):
	if 'confirm' in request.POST:
		form = HiddenForm(request.POST)
		if form.is_valid():
			storage = MediaStorage(name = form.cleaned_data['file_name'])
			dataset = tablib.Dataset().load(storage.read())
			man_up = [ (x['Application ID'],x['TPSL Transaction ID']) for x in dataset.dict ]
			resource = PaymentGatewayDataUploadResource()
			result = resource.import_data(dataset, dry_run=False)
			man_up_filter = reduce(
				operator.or_,
				( 
					Q(src_itc_application__student_application_id=x[0].strip(),
					tpsl_transaction_id=x[1].strip()) for x in man_up 
				)
			)

			PaymentGatewayRecord.objects.filter(
				man_up_filter
				).update(
					payment_file_name = csv_file_name,
					status = '1',
					missing_in_application_center = True,
					uploaded_by = request.user.email,
					)
			return redirect( reverse('bits_admin_payment:hist-gateway-payments',
				kwargs={'alert_status': 'confirm'}) )

	elif 'cancel' in request.POST:
		form = HiddenForm(request.POST)
		if form.is_valid():
			storage = MediaStorage(name = form.cleaned_data['file_name'])
			storage.remove()
			return redirect( reverse('bits_admin_payment:upload-gateway-payments',
				kwargs={'alert_status': 'cancel'}) )
	else:
		form = HiddenForm({'file_name':file_name})
		storage = MediaStorage(name = file_name )
		dataset = tablib.Dataset().load(storage.read())

		header_list = ['Bank ID','SM Transaction ID','Bank Transaction ID',
		'Charges','Taxes','Email','Mobile']

		for x in header_list:del dataset[x]

		resource = DisplayPaymentGatewayDataResource()
		result = resource.import_data(dataset, dry_run=True)
		
	return render(request,
		'adm_payment/preview_gateway_payments.html',
		{'form' : form,'result':result,})

# end preview upload manual and gateway payment

# Ajax call for historical upload manual and gateway payment

@method_decorator([staff_member_required,],name='dispatch')
class HMPView(FeedDataView):

	token = manual_payment_paging().token

	def get_queryset(self):
		query = super(HMPView, self).get_queryset()
		status = self.kwargs.get('st',None)
		from_date = self.kwargs.get('fm_dt',None)
		to_date = self.kwargs.get('to_dt',None)

		from_date = from_date if not from_date == '00-00-0000' else None
		to_date = to_date if not to_date == '00-00-0000' else None

		if from_date and to_date :
			query=query.filter(payment_date__range = [
				dt.strptime(from_date,"%Y-%m-%d %H:%M:%S"),
				dt.strptime(to_date,"%Y-%m-%d %H:%M:%S")
				] )
		elif from_date :
			query=query.filter(payment_date__gte = dt.strptime(from_date,"%Y-%m-%d %H:%M:%S") )
		elif to_date :
			query=query.filter(payment_date__lte = dt.strptime(to_date,"%Y-%m-%d %H:%M:%S") )

		query = query.filter( status = status ) if status and not status == 'n' else query

		query = query.annotate(
			app_id = F('application__student_application_id'),
			sca_pk = F('application__pk'),
			pay_type = Case(
				When(payment_type=Value('1'),then=Value(dict(ManualPaymentDataUpload.PAYMENT_TYPE)['1'])),
				When(payment_type=Value('2'),then=Value(dict(ManualPaymentDataUpload.PAYMENT_TYPE)['2'])),
				When(payment_type=Value('3'),then=Value(dict(ManualPaymentDataUpload.PAYMENT_TYPE)['3'])),
				When(payment_type=Value('4'),then=Value(dict(ManualPaymentDataUpload.PAYMENT_TYPE)['4'])),
				output_field=CharField(),
				),
			man_status=Case(
				When(status=Value('1'),then=Value(dict(ManualPaymentDataUpload.STATUS_MAN)['1'])),
				When(status=Value('2'),then=Value(dict(ManualPaymentDataUpload.STATUS_MAN)['2'])),
				When(status=Value('3'),then=Value(dict(ManualPaymentDataUpload.STATUS_MAN)['3'])),
				When(status=Value('4'),then=Value(dict(ManualPaymentDataUpload.STATUS_MAN)['4'])),
				When(status=Value('5'),then=Value(dict(ManualPaymentDataUpload.STATUS_MAN)['5'])),
				output_field=CharField(),
				)
			)

		return query

@method_decorator([staff_member_required,],name='dispatch')
class HGPView(FeedDataView):

	token = gateway_payment_paging().token

	def get_queryset(self):
		query = super(HGPView, self).get_queryset()
		status = self.kwargs.get('st',None)
		from_date = self.kwargs.get('fm_dt',None)
		to_date = self.kwargs.get('to_dt',None)

		from_date = from_date if not from_date == '00-00-0000' else None
		to_date = to_date if not to_date == '00-00-0000' else None

		if from_date and to_date :
			query=query.filter(transaction_date__range = [
				dt.strptime(from_date,"%Y-%m-%d %H:%M:%S"),
				dt.strptime(to_date,"%Y-%m-%d %H:%M:%S")
				] )
		elif from_date :
			query=query.filter(transaction_date__gte = dt.strptime(from_date,"%Y-%m-%d %H:%M:%S") )
		elif to_date :
			query=query.filter(transaction_date__lte = dt.strptime(to_date,"%Y-%m-%d %H:%M:%S") )

		query = query.filter( status = status ) if status and not status == 'n' else query

		query = query.annotate(
			app_id = F('src_itc_application__student_application_id'),
			sca_pk = F('src_itc_application__pk'),
			gp_status = Case(
				When(status=Value('1'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['1'])),
				When(status=Value('2'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['2'])),
				When(status=Value('3'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['3'])),
				When(status=Value('4'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['4'])),
				When(status=Value('5'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['5'])),
				When(status=Value('6'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['6'])),
				output_field=CharField(),
				),
			)

		return query

# end Ajax call for historical upload manual and gateway payment

# historical upload manual and gateway payment
@staff_member_required
def hist_manual_payments(request,alert_status = None):
	query = ManualPaymentDataUpload.objects.all()

	to_date = request.GET.get("to_date",None)
	from_date = request.GET.get("from_date",None)

	data = {}

	status = request.GET.get('status',None)
	query = query.filter(status=status) if status else query
	data['status'] = status


	if to_date :
		data['to_date'] = to_date
		t=to_date.split('-')
		to_date = dt( int(t[2]), int(t[1]), int(t[0]), 23, 59, 59 )
	

	if from_date :
		data['from_date'] = from_date
		t=from_date.split('-')
		from_date = dt( int(t[2]), int(t[1]), int(t[0]), 00, 00, 00 )
	

	if from_date and to_date :
		query=query.filter(payment_date__range=[from_date,to_date])
	elif from_date :
		query = query.filter(payment_date__gte=from_date)
	elif to_date:
		query = query.filter(payment_date__lte=to_date)

	query = query.annotate(
		app_id = F('application__student_application_id'),
		sca_pk = F('application__pk'),
		pay_type = Case(
				When(payment_type=Value('1'),then=Value(dict(ManualPaymentDataUpload.PAYMENT_TYPE)['1'])),
				When(payment_type=Value('2'),then=Value(dict(ManualPaymentDataUpload.PAYMENT_TYPE)['2'])),
				When(payment_type=Value('3'),then=Value(dict(ManualPaymentDataUpload.PAYMENT_TYPE)['3'])),
				When(payment_type=Value('4'),then=Value(dict(ManualPaymentDataUpload.PAYMENT_TYPE)['4'])),
				output_field=CharField(),
				),
		man_status=Case(
				When(status=Value('1'),then=Value(dict(ManualPaymentDataUpload.STATUS_MAN)['1'])),
				When(status=Value('2'),then=Value(dict(ManualPaymentDataUpload.STATUS_MAN)['2'])),
				When(status=Value('3'),then=Value(dict(ManualPaymentDataUpload.STATUS_MAN)['3'])),
				When(status=Value('4'),then=Value(dict(ManualPaymentDataUpload.STATUS_MAN)['4'])),
				When(status=Value('5'),then=Value(dict(ManualPaymentDataUpload.STATUS_MAN)['5'])),
				output_field=CharField(),
				))
	
	ManualPaymentTable = manual_payment_paging(status = status,
		from_date = from_date,to_date = to_date )

	table = ManualPaymentTable(query)

	messages = {
		'reject':'reject message',
		'approve':'approve message',
		'confirm':'Payment data successfully imported',
		'cancel':'Import cancelled.Data deleted from application center',
		'approve':'''Payments updated in application center.application 
			status updated.student ids generated for admission fee payments''',
		}


	return render(request,'adm_payment/hist_manual_payments.html',
		{'table':table,
		'form':ManualDateandStatusForm(data),
		'messages':messages.get(alert_status,None),
		})

@staff_member_required
def hist_gateway_payments(request, alert_status = None):
	query = PaymentGatewayRecord.objects.all()

	to_date = request.GET.get("to_date",None)
	from_date = request.GET.get("from_date",None)

	data = {}

	status = request.GET.get('status',None)
	query = query.filter(status=status) if status else query
	data['status'] = status


	if to_date :
		data['to_date'] = to_date
		t=to_date.split('-')
		to_date = dt( int(t[2]), int(t[1]), int(t[0]), 23, 59, 59 )
	

	if from_date :
		data['from_date'] = from_date
		t=from_date.split('-')
		from_date = dt( int(t[2]), int(t[1]), int(t[0]), 00, 00, 00 )
	

	if from_date and to_date :
		query=query.filter(transaction_date__range=[from_date,to_date])
	elif from_date :
		query = query.filter(transaction_date__gte=from_date)
	elif to_date:
		query = query.filter(transaction_date__lte=to_date)

	query = query.annotate(
		app_id = F('src_itc_application__student_application_id'),
		sca_pk = F('src_itc_application__pk'),
		gp_status = Case(
				When(status=Value('1'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['1'])),
				When(status=Value('2'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['2'])),
				When(status=Value('3'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['3'])),
				When(status=Value('4'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['4'])),
				When(status=Value('5'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['5'])),
				When(status=Value('6'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['6'])),
				output_field=CharField(),
				),
		)

	GatewayPaymentTable = gateway_payment_paging(status = status,
		from_date = from_date,to_date = to_date )

	table = GatewayPaymentTable(query)
	messages = {
		'reject':'reject message',
		'approve':'approve message',
		'confirm':'Payment data successfully imported',
		'cancel':'Import cancelled.Data deleted from application center',
		'approve':'''Payments updated in application center.application 
			status updated.student ids generated for admission fee payments''',
		}

	return render(request,'adm_payment/hist_gateway_payments.html',
		{'table':table,
		'form':GatewayDateandStatusForm(data),
		'messages':messages.get(alert_status,None),
		})

# end historical upload manual and gateway payment

# csv historical upload manual and gateway payment

@staff_member_required
@require_http_methods(["POST"])
def csv_hist_gateway_payments(request):

	logger.info("{0} invoked funct.".format(request.user.email))
	csv_fee_value = ['src_itc_application__student_application_id',
				 'src_itc_user_name',
				 'bank_name',
				 'tpsl_transaction_id',
				 'total_amount',
				 'net_amount',
				 'transaction_date',
				 'status',
				 'accepted_rejected_datetime',] #order

	csv_fee_header = {'src_itc_application__student_application_id':'Application ID',
				 'src_itc_user_name':'User Name', 
				 'bank_name':'Bank Name',
				 'tpsl_transaction_id':'TPSL Transaction ID',
				 'total_amount':'Total Amount',
				 'net_amount':'Net Amount', 
				 'transaction_date':'Transaction Date',
				 'status':'Status',
				 'accepted_rejected_datetime':'Accepted/Rejected on'}

	field_serializer_map_fee={
	'transaction_date': (lambda x: x and timezone.localtime(x).strftime("%d/%m/%Y")),
	'status': (lambda x:get_choice_display(x,PaymentGatewayRecord.STATUS_GATEWAY)),
	'accepted_rejected_datetime': (lambda x: (x or '') and timezone.localtime(x).strftime("%d/%m/%Y")),
	}

	from_date=request.POST.get("fromDate",None)
	to_date=request.POST.get("toDate",None)
	search=request.POST.get("user",'')

	if to_date:
		t = to_date.split('-')
		to_date = dt( int(t[2]), int(t[1]), int(t[0]), 23, 59, 59 )
	if from_date:
		t = from_date.split('-')
		from_date = dt( int(t[2]), int(t[1]), int(t[0]), 00, 00, 00 )

	query = PaymentGatewayRecord.objects.all().annotate(
		app_id = F('src_itc_application__student_application_id'),
		sca_pk = F('src_itc_application__pk'),
		gp_status = Case(
				When(status=Value('1'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['1'])),
				When(status=Value('2'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['2'])),
				When(status=Value('3'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['3'])),
				When(status=Value('4'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['4'])),
				When(status=Value('5'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['5'])),
				When(status=Value('6'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['6'])),
				output_field=CharField(),
				),
		)

	query=query.filter(
			reduce(operator.and_, (
				Q(src_itc_application__student_application_id__icontains = item)|
				Q(src_itc_user_name__icontains = item)|
				Q(bank_name__icontains = item)|
				Q(tpsl_transaction_id__icontains = item)|
				Q(gp_status__icontains = item)
				for item in search.split())) 
			) if search else query

	if from_date and to_date:
		query=query.filter(
			transaction_date__range=[from_date,to_date]
			)
	elif from_date:
		query=query.filter(
			transaction_date__gte=from_date
			)
	elif to_date:
		query=query.filter(
			transaction_date__lte = to_date
			)

	status = request.POST.get('stat',None)
	query = query.filter(status=status) if status else query

	query=query.values(*csv_fee_value)  

	return render_to_csv_response(query,append_datestamp=True,
		field_header_map=csv_fee_header,
		field_serializer_map=field_serializer_map_fee ,field_order=csv_fee_value,) 

@staff_member_required
@require_http_methods(["POST"])
def csv_hist_manual_payments(request):

	logger.info("{0} invoked funct.".format(request.user.email))
	csv_fee_value = ['application__student_application_id',
				 'payment_id',
				 'payment_type',
				 'payment_date',
				 'payment_amount',
				 'payment_mode',
				 'payment_reversal_flag',
				 'status',
				 'accepted_rejected_datetime',] #order

	csv_fee_header = {'application__student_application_id':'Application ID',
				 'payment_id':'Payment ID', 
				 'payment_type':'Payment Type',
				 'payment_date':'Payment Date',
				 'payment_amount':'Payment Amount',
				 'payment_mode':'Payment Mode', 
				 'payment_reversal_flag':'Reversal',
				 'status':'Status',
				 'accepted_rejected_datetime':'Accepted/Rejected on'}

	field_serializer_map_fee={
	'payment_date': (lambda x: x and timezone.localtime(x).strftime("%d/%m/%Y")),
	'status': (lambda x:get_choice_display(x,ManualPaymentDataUpload.STATUS_MAN)),
	'payment_type': (lambda x:get_choice_display(x,ManualPaymentDataUpload.PAYMENT_TYPE)),
	'accepted_rejected_datetime': (lambda x: (x or '') and timezone.localtime(x).strftime("%d/%m/%Y")),
	}

	from_date=request.POST.get("fromDate",None)
	to_date=request.POST.get("toDate",None)
	search=request.POST.get("user",'')

	if to_date:
		t = to_date.split('-')
		to_date = dt( int(t[2]), int(t[1]), int(t[0]), 23, 59, 59 )
	if from_date:
		t = from_date.split('-')
		from_date = dt( int(t[2]), int(t[1]), int(t[0]), 00, 00, 00 )

	query = ManualPaymentDataUpload.objects.all().annotate(
		app_id = F('application__student_application_id'),
		sca_pk = F('application__pk'),
		pay_type = Case(
				When(payment_type=Value('1'),then=Value(dict(ManualPaymentDataUpload.PAYMENT_TYPE)['1'])),
				When(payment_type=Value('2'),then=Value(dict(ManualPaymentDataUpload.PAYMENT_TYPE)['2'])),
				When(payment_type=Value('3'),then=Value(dict(ManualPaymentDataUpload.PAYMENT_TYPE)['3'])),
				When(payment_type=Value('4'),then=Value(dict(ManualPaymentDataUpload.PAYMENT_TYPE)['4'])),
				output_field=CharField(),
				),
		man_status=Case(
				When(status=Value('1'),then=Value(dict(ManualPaymentDataUpload.STATUS_MAN)['1'])),
				When(status=Value('2'),then=Value(dict(ManualPaymentDataUpload.STATUS_MAN)['2'])),
				When(status=Value('3'),then=Value(dict(ManualPaymentDataUpload.STATUS_MAN)['3'])),
				When(status=Value('4'),then=Value(dict(ManualPaymentDataUpload.STATUS_MAN)['4'])),
				When(status=Value('5'),then=Value(dict(ManualPaymentDataUpload.STATUS_MAN)['5'])),
				output_field=CharField(),
				))

	query=query.filter(
			reduce(operator.and_, (
				Q(application__student_application_id__icontains = item)|
				Q(payment_id__icontains = item)|
				Q(pay_type__icontains = item)|
				Q(payment_mode__icontains = item)|
				Q(man_status__icontains = item)
				for item in search.split())) 
			) if search else query

	if from_date and to_date:
		query=query.filter(
			payment_date__range=[from_date,to_date]
			)
	elif from_date:
		query=query.filter(
			payment_date__gte=from_date
			)
	elif to_date:
		query=query.filter(
			payment_date__lte = to_date
			)

	status = request.POST.get('stat',None)
	query = query.filter(status=status) if status else query

	query=query.values(*csv_fee_value)  

	return render_to_csv_response(query,append_datestamp=True,
		field_header_map=csv_fee_header,
		field_serializer_map=field_serializer_map_fee ,field_order=csv_fee_value,)

