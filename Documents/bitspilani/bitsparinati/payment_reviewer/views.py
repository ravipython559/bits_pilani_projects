from django.shortcuts import render, redirect
from .forms import *
from bits_admin.forms import ToAndFromDate
from .bits_decorator import *
from .tables import *
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
from django.db import IntegrityError, transaction
from djqscsv import render_to_csv_response
from datetime import datetime as dt
from django.utils import timezone
from tempfile import NamedTemporaryFile as NTFile
from dateutil.parser import parse
from dateutil.tz import gettz
from bits_rest.bits_extra import student_id_generator
from registrations.tables import pgm_adm_report_paging
from registrations.tables_ajax import BasePgmAdmReportAjaxData
from registrations.dynamic_dmr_report import BaseProgramAdmissionReport
from django_mysql.locks import Lock
import logging
logger = logging.getLogger("main")

class ReconcileError(Exception):pass 

def get_choice_display(value,choices):
	for k,v in choices:
		if k==value:return v
	return "Not Found"

def display_status(status):
	for x in settings.APP_STATUS:
		if x[0] == status:
			return x[1]

@login_required
@only_payment_reviewer_permission
def payment_reviewer_home(request):
	return render(request,'payment_reviewer/payment_reviewer_home.html',)

# upload manual and gateway payment

@login_required
@add_and_view_permission
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
					reverse('payment_reviewer:preview-manual-payments',
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
		'payment_reviewer/upload_manual_payments.html',
		{
		'form':form,
		'result':result,
		'messages':messages.get(alert_status,None),
		})

@login_required
@add_and_view_permission
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

			resource = PaymentGatewayDataUploadResource()
			result = resource.import_data(dataset, dry_run=True)
			if not result.has_errors():
				storage = MediaStorage()
				storage.save(data = dataset.csv)
				return redirect(
					reverse('payment_reviewer:preview-gateway-payments',
						kwargs={'file_name':storage.name,
						'csv_file_name':csv_file_name,
						}
					)
				)

	else:
		form = GatewayUploadForm()

	messages = {'confirm':'Payment data successfully imported',
		'cancel':'Import cancelled. Data deleted from application center',
		'approve':'''Payments updated in application center. Application 
		status updated. Student IDs generated for Admission Fee payments''',
		}

	return render(request,
		'payment_reviewer/upload_gateway_payments.html',
		{
		'form':form,
		'result':result,
		'messages':messages.get(alert_status,None),
		})

# end upload manual and gateway payment

# preview upload manual and gateway payment

@login_required
@add_and_view_permission
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
			return redirect( reverse('payment_reviewer:hist-manual-payments',
				kwargs={'alert_status': 'confirm'}) )

	elif 'cancel' in request.POST:
		form = HiddenForm(request.POST)
		if form.is_valid():
			storage = MediaStorage(name = form.cleaned_data['file_name'])
			storage.remove()
			return redirect( reverse('payment_reviewer:upload-manual-payments',
				kwargs={'alert_status': 'cancel'}) )
	else:
		form = HiddenForm({'file_name':file_name})
		storage = MediaStorage(name = file_name )
		dataset = tablib.Dataset().load(storage.read())
		resource = ManualPaymentDataUploadResource()
		result = resource.import_data(dataset, dry_run=True)
		
	return render(request,
		'payment_reviewer/preview_manual_payments.html',
		{'form' : form,'result':result,})

@login_required
@add_and_view_permission
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
			return redirect( reverse('payment_reviewer:hist-gateway-payments',
				kwargs={'alert_status': 'confirm'}) )

	elif 'cancel' in request.POST:
		form = HiddenForm(request.POST)
		if form.is_valid():
			storage = MediaStorage(name = form.cleaned_data['file_name'])
			storage.remove()
			return redirect( reverse('payment_reviewer:upload-gateway-payments',
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
		'payment_reviewer/preview_gateway_payments.html',
		{'form' : form,'result':result,})

# end preview upload manual and gateway payment

# Ajax call for historical upload manual and gateway payment

@method_decorator([login_required,add_and_view_permission],name='dispatch')
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

@method_decorator([login_required,add_and_view_permission],name='dispatch')
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
@login_required
@add_and_view_permission
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
		'confirm':'Payment data successfully imported',
		'cancel':'Import cancelled.Data deleted from application center',
		'approve':'''Payments updated in application center. Application \
			status updated. Student IDs generated for Admission Fee payments''',
		'mismatch':'''One of more payments have amount mismatches \
			with the program fees. These payments have not been copied into payments table. You \
			can view the transactions with status = FEE MISMATCH in the history data viewpage.''',
		}

	return render(request,'payment_reviewer/hist_manual_payments.html',
		{'table':table,
		'form':ManualDateandStatusForm(data),
		'messages':messages.get(alert_status,None),
		})

@login_required
@add_and_view_permission
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
		'confirm':'Payment gateway data successfully imported',
		'cancel':'Import cancelled.Data deleted from application center',
		'approve':'''Payments updated in application center. Application \
			status updated. Student IDs generated for Admission Fee payments''',
		'mismatch':'''One of more payments have amount mismatches \
			with the program fees. These payments have not been copied into payments table. You \
			can view the transactions with status = FEE MISMATCH in the history data viewpage.''',
		}

	return render(request,'payment_reviewer/hist_gateway_payments.html',
		{'table':table,
		'form':GatewayDateandStatusForm(data),
		'messages':messages.get(alert_status,None),
		})

# end historical upload manual and gateway payment

# csv historical upload manual and gateway payment

@login_required
@require_http_methods(["POST"])
@add_and_view_permission
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

@login_required
@require_http_methods(["POST"])
@add_and_view_permission
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

# end csv historical upload manual and gateway payment 


# reconcile manual and gateway ajax view

@method_decorator([login_required,reconsile_permission],name='dispatch')
class RMPView(FeedDataView):

	token = review_manual_payment_upload().token
	
	def get_queryset(self):
	
		query = super(RMPView, self).get_queryset().filter(
			status__in = ['1','2']).annotate(
			app_id=F('application__student_application_id'),
			sca_pk = F('application__pk'),
			man_status=Case(
				When(status=Value('1'),then=Value(dict(ManualPaymentDataUpload.STATUS_MAN)['1'])),
				When(status=Value('2'),then=Value(dict(ManualPaymentDataUpload.STATUS_MAN)['2'])),
				When(status=Value('3'),then=Value(dict(ManualPaymentDataUpload.STATUS_MAN)['3'])),
				When(status=Value('4'),then=Value(dict(ManualPaymentDataUpload.STATUS_MAN)['4'])),
				When(status=Value('5'),then=Value(dict(ManualPaymentDataUpload.STATUS_MAN)['5'])),
				output_field=CharField(),
				),
			pay_type = Case(
				When(payment_type=Value('1'),then=Value(dict(ManualPaymentDataUpload.PAYMENT_TYPE)['1'])),
				When(payment_type=Value('2'),then=Value(dict(ManualPaymentDataUpload.PAYMENT_TYPE)['2'])),
				When(payment_type=Value('3'),then=Value(dict(ManualPaymentDataUpload.PAYMENT_TYPE)['3'])),
				When(payment_type=Value('4'),then=Value(dict(ManualPaymentDataUpload.PAYMENT_TYPE)['4'])),
				output_field=CharField(),
				),
			)
		filename = self.kwargs.get('file_name',None)
		checked_list = map(int,self.request.GET.getlist('checked_data[]'))
		un_checked_list = map(int,self.request.GET.getlist('un_checked_data[]'))
		storage = MediaStorage( name = filename )
		dataset = tablib.Dataset().load(storage.read())
		reconcile_id = set(filter(lambda x: x not in un_checked_list,map(int, dataset['id'] + checked_list )))
		data = tablib.Dataset()
		data.headers = ('id','flag')
		map(data.append, [ (x,1) for x in reconcile_id ])
		storage.remove()
		storage = MediaStorage( name = filename )
		storage.save(data = data.csv)
		q1 = query.annotate(
			acc_rej = Case(
				When(pk__in = data['id'], 
					then = Value(True)
					),
				default=Value(False),
				output_field=BooleanField(),

				),)
		q2 = query.annotate(
			acc_rej=Value(False, output_field=BooleanField()),
			)
		query = q1 if data['id'] else q2

		return query

@method_decorator([login_required,reconsile_permission],name='dispatch')
class RGPView(FeedDataView):
	token = review_gateway_payment_upload().token
	
	def get_queryset(self):
	
		query = super(RGPView, self).get_queryset().filter(
		status__in = ['1','3']).annotate(
		app_id=F('src_itc_application__student_application_id'),
		sca_pk = F('src_itc_application__pk'),
		gateway_status=Case(
				When(status=Value('1'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['1'])),
				When(status=Value('2'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['2'])),
				When(status=Value('3'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['3'])),
				When(status=Value('4'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['4'])),
				When(status=Value('5'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['5'])),
				When(status=Value('6'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['6'])),
				output_field=CharField(),
				),
		)

		filename = self.kwargs.get('file_name',None)
		checked_list = map(int,self.request.GET.getlist('checked_data[]'))
		un_checked_list = map(int,self.request.GET.getlist('un_checked_data[]'))
		storage = MediaStorage( name = filename )
		dataset = tablib.Dataset().load(storage.read())
		reconcile_id = set(filter(lambda x: x not in un_checked_list,map(int, dataset['id'] + checked_list )))
		data = tablib.Dataset()
		data.headers = ('id','flag')
		map(data.append, [ (x,1) for x in reconcile_id ])
		storage.remove()
		storage = MediaStorage( name = filename )
		storage.save(data = data.csv)
		q1 = query.annotate(
			acc_rej = Case(
				When(pk__in = data['id'], 
					then = Value(True)
					),
				default=Value(False),
				output_field=BooleanField(),

				),)
		q2 = query.annotate(
			acc_rej = Value(False, output_field=BooleanField()),
			)
		query = q1 if data['id'] else q2

		return query

# end reconcile manual and gateway ajax view

#  reconcile manual and gateway view
@login_required
@reconsile_permission
def reconcile_manual_payments(request):
	query = ManualPaymentDataUpload.objects.filter(
		status__in = ['1','2']).annotate(
			acc_rej=Value(False, output_field=BooleanField()),
			app_id=F('application__student_application_id'),
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
				),
		)

	if request.method == 'POST':

		form = HiddenForm(request.POST)

		if form.is_valid():
			any_mis_match = False
			storage = MediaStorage(name = form.cleaned_data['file_name'])
			dataset = tablib.Dataset().load(storage.read())
			chkboxes = filter(lambda x: x.startswith('{0}_check_name_'.format('bits')),request.POST.keys())
			checked = [ x.split('{0}_check_name_'.format('bits'))[-1] for x in chkboxes ]
			hidden = filter(lambda x: x.startswith('{0}_hidden_name_'.format('bits')),request.POST.keys())
			unchecked = [ int(request.POST.get(x)) for x in hidden if request.POST.get(x) not in checked ]
			reconcile_id = set(filter(lambda x: x not in unchecked,map(int, dataset['id'] + checked )))
			query = query.filter(pk__in = reconcile_id) if 'approve' in request.POST else query
			query = query.filter(pk__in = reconcile_id) if 'reject' in request.POST else query
			filter_query = map(lambda x:(FEE_TYPE_CHOICES[1][0],x,),
				query.filter(payment_type__in = ['1','4'], )) #admission,feetype=1
			filter_query += map(lambda x:(FEE_TYPE_CHOICES[2][0],x,),
				query.filter(payment_type__in = ['2','3'], ))  #application,feetype=2

			try:
				with transaction.atomic():

					if 'approve' in request.POST or 'approve_all' in request.POST:

						for fee_type,adm in filter_query:
							
							pfa = adm.application.program.program_fees_admission_requests_created_4.get(
								fee_type = fee_type,
								latest_fee_amount_flag = True,
								#admit_year = adm.application.admit_year,
								)

							cond_adm_app = adm.payment_amount == pfa.fee_amount and adm.payment_type in ['1','2']
							cond_rev = abs(adm.payment_amount) == pfa.fee_amount and adm.payment_type in ['4','3']

							if not adm.application.application_status == settings.APP_STATUS[12][0] and not adm.application.application_status == settings.APP_STATUS[9][0]:
								try:
									ApplicationPayment.objects.get(
										application = adm.application,
										fee_type = adm.payment_type,
										)
									adm.status = '5'
									adm.accepted_rejected_by = request.user.email
									adm.accepted_rejected_datetime = timezone.now()
									adm.save()
									continue

								except ApplicationPayment.DoesNotExist: pass

							if cond_rev or cond_adm_app:
								ApplicationPayment.objects.update_or_create(
									application = adm.application,
									fee_type = adm.payment_type,
									defaults = {'payment_id': adm.payment_id,
										'payment_date':adm.payment_date,
										'payment_amount':adm.payment_amount,
										'payment_bank':'NOT APPLICABLE',
										'transaction_id':adm.payment_id,
										'manual_upload_flag':True,
										'insertion_datetime':timezone.now(),
										'insertion_approved_by':request.user.email,
										},
									)
								adm.status = '3' #Approved
								adm.accepted_rejected_datetime = timezone.now()
								adm.accepted_rejected_by = request.user.email
								
								sca = adm.application
								if adm.payment_type == '1':#Admission Fee
									if not sca.application_status == settings.APP_STATUS[9][0]:
										raise ReconcileError('Admission Fee :applicant {0} status is other than {1} it is {2}'.format(
											sca.student_application_id,
											settings.APP_STATUS[9][0],
											sca.application_status)
										)

									sca.application_status = settings.APP_STATUS[11][0] #Admission Fee Paid
									sca.save()
									cs = CandidateSelection.objects.get(application = sca)

									try:

										ae = ApplicantExceptions.objects.get(applicant_email = cs.application.login_email.email,
											program = cs.application.program )
										ae = ae.transfer_program if ae.transfer_program else None
									except ApplicantExceptions.DoesNotExist:
										ae = None

									with Lock('bits_student_id_lock'):
										student_id = student_id_generator(login_email=sca.login_email.email)
										if cs.student_id:student_id=cs.student_id
										cs.student_id = student_id
										cs.admitted_to_program = ae
										cs.save()

								elif adm.payment_type == '2':#Application Fee
									if not sca.application_status in [settings.APP_STATUS[12][0], settings.APP_STATUS[18][0] ]:
										raise ReconcileError('Application Fee: applicant {0} status is other than {1} it is {2}'.format(
											sca.student_application_id,
											settings.APP_STATUS[12][0],
											sca.application_status)
										)

									sca.application_status = settings.APP_STATUS[13][0] #Application Fees Paid
									sca.save()

								elif adm.payment_type == '3':#REVERSAL-APPLICATION FEE
									ap = ApplicationPayment.objects.filter( 
										application = adm.application,
										fee_type__in = ['2','3'],
										 ).aggregate(total_amount=Sum(F('payment_amount')))
									if not ap['total_amount'] and adm.application.application_status == settings.APP_STATUS[13][0]:
										sca.application_status = settings.APP_STATUS[12][0] #Submitted
										sca.save()

								elif adm.payment_type == '4':#REVERSAL-ADMISSION FEE
									ap = ApplicationPayment.objects.filter( 
										application = adm.application,
										fee_type__in = ['1','4'],
										 ).aggregate(total_amount=Sum(F('payment_amount')))
									if not ap['total_amount'] and adm.application.application_status == settings.APP_STATUS[11][0]:
										sca.application_status = settings.APP_STATUS[9][0] #Accepted by Applicant
										sca.save()

								adm.save()	
							else:								
								adm.status = '2' #Fee Mismatch
								adm.accepted_rejected_datetime = None
								adm.accepted_rejected_by = None
								any_mis_match = True
								adm.save()

						alert_status = 'mismatch' if any_mis_match else 'approve' 

					elif 'reject' in request.POST:
						adm = ManualPaymentDataUpload.objects.filter(pk__in=[ x[1].pk for x in filter_query ])
						adm.update(status = '4',#Rejected
							accepted_rejected_datetime = timezone.now(),
							accepted_rejected_by = request.user.email
							)
						alert_status = 'reject'

			except Exception as e:
				storage.remove()
				storage = MediaStorage( name = form.cleaned_data['file_name'] )
				data = tablib.Dataset()
				data.headers = ('id','flag')
				map(data.append, [ (x,1) for x in reconcile_id ])
				storage.save(data = data.csv)
				ManualPaymentTable = review_manual_payment_upload( file_name = storage.name )
				table = ManualPaymentTable(query)
				return render(request,
					'payment_reviewer/reconcile_manual_payments.html',
					{
						'table' : table, 
						'form':form,
						'pfa_error':str(e),
					}
				)
			storage.remove()

			return redirect( reverse('payment_reviewer:hist-manual-payments',
				kwargs={'alert_status':alert_status}) )


	else:
		data = tablib.Dataset()
		data.headers = ('id','flag')
		storage = MediaStorage()
		storage.save(data = data.csv)
		ManualPaymentTable = review_manual_payment_upload( file_name = storage.name )
		table = ManualPaymentTable(query)
		form = HiddenForm({'file_name':storage.name})

	return render(request,
		'payment_reviewer/reconcile_manual_payments.html',
		{'table' : table, 'form':form})

@login_required
@reconsile_permission
def reconcile_gateway_payments(request):
	query = PaymentGatewayRecord.objects.filter(
		status__in = ['1','3']).annotate(
		acc_rej=Value(False, output_field=BooleanField()),
		app_id=F('src_itc_application__student_application_id'),
		sca_pk = F('src_itc_application__pk'),
		gateway_status=Case(
				When(status=Value('1'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['1'])),
				When(status=Value('2'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['2'])),
				When(status=Value('3'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['3'])),
				When(status=Value('4'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['4'])),
				When(status=Value('5'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['5'])),
				When(status=Value('6'),then=Value(dict(PaymentGatewayRecord.STATUS_GATEWAY)['6'])),
				output_field=CharField(),
				),
		)
	if request.method == 'POST':
		form = HiddenForm(request.POST)
		if form.is_valid():
			any_mis_match = False
			is_double_payment = False
			storage = MediaStorage(name = form.cleaned_data['file_name'])
			dataset = tablib.Dataset().load(storage.read())
			chkboxes = filter(lambda x: x.startswith('{0}_check_name_'.format('bits')),request.POST.keys())
			checked = [ x.split('{0}_check_name_'.format('bits'))[-1] for x in chkboxes ]
			hidden = filter(lambda x: x.startswith('{0}_hidden_name_'.format('bits')),request.POST.keys())
			unchecked = [ int(request.POST.get(x)) for x in hidden if request.POST.get(x) not in checked ]
			reconcile_id = set(filter(lambda x: x not in unchecked,map(int, dataset['id'] + checked )))
			query = query.filter(pk__in = reconcile_id) if 'approve' in request.POST else query
			query = query.filter(pk__in = reconcile_id) if 'reject' in request.POST else query
			try:
				with transaction.atomic():
					if 'approve' in request.POST or 'approve_all' in request.POST:
						for x in query:
							try:
								pfa = x.src_itc_application.program.program_fees_admission_requests_created_4.exclude                                                                    (
                                                                        fee_type__in=['5','6','7','8']
                                                                    ).get(
									latest_fee_amount_flag = True,
									admit_year = x.src_itc_application.admit_year,
									fee_amount = x.net_amount,
								)
								

							except PROGRAM_FEES_ADMISSION.DoesNotExist:
								any_mis_match = True
								x.status = '3'
								x.accepted_rejected_datetime = None
								x.accepted_rejected_by = None
								x.save()
							
							else:
								ap = ApplicationPayment.objects.filter(
										application = x.src_itc_application,
										fee_type = pfa.fee_type,
										transaction_id=x.tpsl_transaction_id,
										payment_bank=str(x.bank_id),
										payment_id=x.sm_transaction_id,
										payment_amount="{:.2f}".format(x.total_amount),
										payment_date=x.transaction_date,
									)


								if ap.exists():
									x.status = '2'
									x.missing_in_application_center = False
									x.accepted_rejected_datetime = timezone.now()
									x.accepted_rejected_by = request.user.email
									x.save()
									ap = ap.get(fee_type = pfa.fee_type,)
									ap.matched_with_payment_gateway=True
									ap.missing_from_gateway_file=False
									ap.manual_upload_flag=False
									ap.inserted_from_gateway_file=False
									ap.insertion_datetime=None
									ap.insertion_approved_by=None
									ap.save()

								else:

									try:
										ApplicationPayment.objects.get(
											application = x.src_itc_application,
											fee_type = pfa.fee_type,
											)
										x.status = '6'
										x.accepted_rejected_by = request.user.email
										x.accepted_rejected_datetime = timezone.now()
										x.save()
										continue

									except ApplicationPayment.DoesNotExist: pass

									app_payment=ApplicationPayment(
											application = x.src_itc_application,
											fee_type = pfa.fee_type,
											transaction_id=x.tpsl_transaction_id,
											payment_bank=x.bank_id,
											payment_id= x.sm_transaction_id,
											payment_amount=x.total_amount,
											payment_date=x.transaction_date,
											matched_with_payment_gateway=True,
											missing_from_gateway_file=False,
											manual_upload_flag=False,
											inserted_from_gateway_file=True,
											insertion_datetime=timezone.now(),
											insertion_approved_by=request.user.email,
											
										)
									x.status = '4'
									x.missing_in_application_center = False
									x.accepted_rejected_datetime = timezone.now()
									x.accepted_rejected_by = request.user.email
									
									sca = x.src_itc_application
									if pfa.fee_type == '1':#admission fees
										if not sca.application_status == settings.APP_STATUS[9][0]:
											app_pay = ApplicationPayment.objects.get(
													application = x.src_itc_application,
													fee_type = pfa.fee_type,
												)
											raise ReconcileError('''
													admission fees: applicant {0} reconcilation failed for transcation {1} 
													since transcation already exist which is {2}
												'''.format(
													sca.student_application_id,
													x.tpsl_transaction_id,
													app_pay.transaction_id,
												)
											)

										sca.application_status = settings.APP_STATUS[11][0] #Admission Fee Paid
										app_payment.save()
										x.save()
										sca.save()
										with Lock('bits_student_id_lock'):
											cs = CandidateSelection.objects.get(application = sca)
											student_id = student_id_generator(login_email=sca.login_email.email)
											if cs.student_id:student_id=cs.student_id
											cs.student_id = student_id
											cs.save()

									elif pfa.fee_type == '2':#application fees
										if not sca.application_status in [settings.APP_STATUS[12][0], settings.APP_STATUS[18][0] ]:
											app_pay = ApplicationPayment.objects.get(
													application = x.src_itc_application,
													fee_type = pfa.fee_type,
												)
											raise ReconcileError('''
														application fees: applicant {0} reconcilation failed for transcation {1} 
														since transcation already exist which is {2}
													'''.format(
														sca.student_application_id,
														x.tpsl_transaction_id,
														app_pay.transaction_id,
														)
													)

										sca.application_status = settings.APP_STATUS[13][0] #Application Fees Paid
										app_payment.save()
										x.save()
										sca.save()
						alert_status = 'mismatch' if any_mis_match else 'approve'

					elif 'reject' in request.POST:
						pgr = PaymentGatewayRecord.objects.filter(pk__in=[ x.pk for x in query ])
						pgr.update(status = '5',#Rejected
							accepted_rejected_datetime = timezone.now(),
							accepted_rejected_by = request.user.email)
						alert_status = 'reject'

			except Exception as e:
				storage.remove()
				storage = MediaStorage( name = form.cleaned_data['file_name'] )
				data = tablib.Dataset()
				data.headers = ('id','flag')
				map(data.append, [ (x,1) for x in reconcile_id ])
				storage.save(data = data.csv)
				GatewayPaymentTable = review_gateway_payment_upload( file_name = storage.name )
				table = GatewayPaymentTable(query)
				return render(request,
					'payment_reviewer/reconcile_gateway_payments.html',
					{
						'table' : table, 
						'form':form,
						'pfa_error':str(e),
					})

			storage.remove()
			return redirect( reverse('payment_reviewer:hist-gateway-payments',
				kwargs={'alert_status':alert_status}) )

	else :
		data = tablib.Dataset()
		data.headers = ('id','flag')
		storage = MediaStorage()
		storage.save(data = data.csv)
		GatewayPaymentTable = review_gateway_payment_upload( file_name = storage.name )
		table = GatewayPaymentTable(query)
		form = HiddenForm({'file_name':storage.name})

	return render(request,'payment_reviewer/reconcile_gateway_payments.html',
		{'table' : table, 'form':form})

# end reconcile manual and gateway view

# payment data view start 
class PaymentAppDataView(FeedDataView):

	token = usr_payment_filter_paging().token
	def get_queryset(self):
		query = super(PaymentAppDataView, self).get_queryset()
		from_date = self.kwargs.get('fm_dt',None)
		to_date = self.kwargs.get('to_dt',None)
		bank = self.kwargs.get('bank',None)

		from_date = from_date if not from_date == '00-00-0000' else None
		to_date = to_date if not to_date == '00-00-0000' else None
		bank_name = bank if not bank =='n' else None
		query = query.annotate(
			app_id = Case(
					When(candidateselection_requests_created_5550__new_application_id=None, 
						then=Concat('student_application_id',Value(' '))),
					default=Concat('candidateselection_requests_created_5550__new_application_id',Value(' ')),
					output_field=CharField(),
					),
			full_prog = Concat('program__program_name',Value(' - '),
				'program__program_code',Value(' ('),
				'program__program_type',Value(')')),
			payment_date = F('applicationpayment_requests_created_3__payment_date'),
			payment_amount = F('applicationpayment_requests_created_3__payment_amount'),
			transaction_id = F('applicationpayment_requests_created_3__transaction_id'),
			payment_bank = F('applicationpayment_requests_created_3__payment_bank'),
			)

		if from_date and to_date :
			query=query.exclude( 
				payment_date__isnull = True 
				).filter( 
				payment_date__range = [dt.strptime(from_date,"%Y-%m-%d %H:%M:%S"),
				dt.strptime(to_date,"%Y-%m-%d %H:%M:%S")] 
				)
		elif from_date :
			query=query.exclude( 
				payment_date__isnull = True 
				).filter(
				payment_date__gte = dt.strptime(from_date,"%Y-%m-%d %H:%M:%S") 
				)
		elif to_date :
			query=query.exclude( 
				payment_date__isnull = True 
				).filter( 
				payment_date__lte = dt.strptime(to_date,"%Y-%m-%d %H:%M:%S") 
				)

		if bank_name:
			if 'TPSL' != bank_name:
				query = query.filter(payment_bank=bank_name)
			else:
				query = query.filter(payment_bank__regex=r'^[0-9]+$')
		return query
		
	def get_queryset_length(self, queryset):
		return len(queryset)

def paymentDataView(request):
	logger.info("{0} invoked funct.".format(request.user.email))

	query = StudentCandidateApplication.objects.annotate(
		app_id = Case(
				When(candidateselection_requests_created_5550__new_application_id=None, 
					then=Concat('student_application_id',Value(' '))),
				default=Concat('candidateselection_requests_created_5550__new_application_id',Value(' ')),
				output_field=CharField(),
				),
		full_prog = Concat('program__program_name',Value(' - '),
				'program__program_code',Value(' ('),
				'program__program_type',Value(')')),
		payment_date = F('applicationpayment_requests_created_3__payment_date'),
		payment_amount = F('applicationpayment_requests_created_3__payment_amount'),
		transaction_id = F('applicationpayment_requests_created_3__transaction_id'),
		payment_bank = F('applicationpayment_requests_created_3__payment_bank'),
		)

	for x in query:x.applicationpayment_requests_created_3.count()


	SCATable = usr_payment_filter_paging( 
		count = query.count() 
		)

	table = SCATable(query)

	return render(request, 'payment_reviewer/payment_data_view.html', {"queryResult": query ,
		"form1": ToAndFromDate(),'table': table},
		)

@require_http_methods(["POST"])
def date_refresh_payment(request):

	to_date = request.POST.get( "to_date", None )
	from_date = request.POST.get("from_date", None )
	bank_name = request.POST.get("bank_type", None )
	data = {}

	if to_date :
		data['to_date'] = to_date
		t = to_date.split('-')
		to_date = dt( int(t[2]), int(t[1]), int(t[0]), 23, 59, 59 )
	
	if from_date :
		data['from_date'] = from_date
		t = from_date.split('-')
		from_date = dt( int(t[2]), int(t[1]), int(t[0]), 00, 00, 00 )

	if bank_name:
		data['bank_type'] = bank_name
	
	query = StudentCandidateApplication.objects.annotate(
		app_id = Case(
				When(candidateselection_requests_created_5550__new_application_id=None, 
					then=Concat('student_application_id',Value(' '))),
				default=Concat('candidateselection_requests_created_5550__new_application_id',Value(' ')),
				output_field=CharField(),
				),
		finalName = F('full_name'),
		full_prog = Concat('program__program_name',Value(' - '),
				'program__program_code',Value(' ('),
				'program__program_type',Value(')')),
		payment_date = F('applicationpayment_requests_created_3__payment_date'),
		payment_amount = F('applicationpayment_requests_created_3__payment_amount'),
		transaction_id = F('applicationpayment_requests_created_3__transaction_id'),
		payment_bank = F('applicationpayment_requests_created_3__payment_bank'),
		)

	if from_date and to_date :
		query=query.exclude( 
			payment_date__isnull = True 
			).filter( 
			payment_date__range=[from_date,to_date] 
			)
	elif from_date :
		query=query.exclude( 
			payment_date__isnull = True 
			).filter( 
			payment_date__gte=from_date 
			)
	elif to_date :
		query=query.exclude( 
			payment_date__isnull = True 
			).filter( payment_date__lte=to_date )

	if bank_name:
		if 'TPSL' != bank_name:
			query = query.filter(payment_bank=bank_name)
		else:
			query = query.filter(payment_bank__regex=r'^[0-9]+$')

	for x in query:x.applicationpayment_requests_created_3.count()

	SCATable = usr_payment_filter_paging( from_date = from_date,
	 to_date = to_date,
	 count = query.count(), bank = bank_name )
	table = SCATable(query)
	
	return render(request, 'payment_reviewer/payment_data_view.html', {
		'queryResult' : query ,
		'form1' : ToAndFromDate(data),
		'table' : table,
		},)

@require_http_methods(["POST"])
def csv_payment_view(request) :
	logger.info("{0} invoked funct.".format(request.user.email))
	csv_fee_value = ['app_id',
				 'full_name','full_prog',
				 'created_on_datetime',
				 'applicationpayment_requests_created_3__payment_date',
				 'applicationpayment_requests_created_3__payment_amount',
				 'applicationpayment_requests_created_3__transaction_id',
				 'payment_bank',
				 'application_status',] #order

	csv_fee_header = {'app_id':'Application Number',
				 'full_name':'Name', 
				 'full_prog':'Program Applied For',
				 'created_on_datetime':'Applied on Date',
				 'applicationpayment_requests_created_3__payment_date':'Payment Date',
				 'applicationpayment_requests_created_3__payment_amount':'Payment Amount', 
				 'applicationpayment_requests_created_3__transaction_id':'Transaction ID',
				 'payment_bank':'Payment Bank',
				 'application_status':'Current Status'}

	field_serializer_map_fee={
	'created_on_datetime': (lambda x: (x or '') and timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p")),
	'applicationpayment_requests_created_3__payment_date':(lambda x: (x or '') and timezone.localtime(x).strftime("%d-%m-%Y %I:%M %p")),
	'application_status':(lambda x: display_status(x)),
	}
	from_date=request.POST.get("fromDate",None)
	to_date=request.POST.get("toDate",None)
	search=request.POST.get("search",'')
	bank_name = request.POST.get("bank",None)

	if to_date:
		t = to_date.split('-')
		to_date = dt( int(t[2]), int(t[1]), int(t[0]), 23, 59, 59 )
	if from_date:
		t = from_date.split('-')
		from_date = dt( int(t[2]), int(t[1]), int(t[0]), 00, 00, 00 )
	
	query = StudentCandidateApplication.objects.annotate(
		app_id = Case(
					When(candidateselection_requests_created_5550__new_application_id__isnull = True, 
						then=Concat('student_application_id',Value(' '))),
					default=Concat('candidateselection_requests_created_5550__new_application_id',Value(' ')),
					output_field=CharField(),
					),
		full_prog = Concat('program__program_name',Value(' - '),
				'program__program_code',Value(' ('),
				'program__program_type',Value(')')),
		payment_date=F('applicationpayment_requests_created_3__payment_date'),
		payment_bank= Case(
			When(applicationpayment_requests_created_3__payment_bank__regex=r'^[0-9]+$', then=Value('Tech Process')),
			When(~Q(applicationpayment_requests_created_3__payment_bank__regex=r'^[0-9]+$'), then=F('applicationpayment_requests_created_3__payment_bank')),
		output_field=CharField(),
		)
		)

	query = query.filter(
				reduce(operator.and_, (
					Q(full_name__icontains = item)|
					Q(app_id__icontains = item)|
					Q(full_prog__icontains = item )
					for item in search.split()))
				) if search else query

	if from_date and to_date:
		query = query.exclude(
			payment_date__isnull=True
		).filter(
			payment_date__range=[from_date, to_date]
		)
	elif from_date:
		query = query.exclude(
			payment_date__isnull=True
		).filter(
			payment_date__gte=from_date
		)
	elif to_date:
		query = query.exclude(
			payment_date__isnull=True
		).filter(payment_date__lte=to_date)

	if bank_name:
		if 'TPSL' != bank_name:
			query = query.filter(payment_bank=bank_name)
		else:
			query = query.filter(payment_bank='Tech Process')
	
	query=query.values(*csv_fee_value).distinct()	
	return render_to_csv_response(query,append_datestamp=True,
		field_header_map=csv_fee_header,
		field_serializer_map=field_serializer_map_fee ,field_order=csv_fee_value,)

@method_decorator([login_required,reconsile_permission],name='dispatch')
class ProgramAdmissionsReport(BaseProgramAdmissionReport):
	template_name = 'payment_reviewer/pgm_adm_report.html'
	ajax_url = 'payment_reviewer:program-admissions-report-ajax'

@method_decorator([login_required,reconsile_permission],name='dispatch')
class ProgramAdmissionsReportAjax(BasePgmAdmReportAjaxData):
	token = pgm_adm_report_paging(ajax_url='payment_reviewer:program-admissions-report-ajax',).token

# payment data view end
