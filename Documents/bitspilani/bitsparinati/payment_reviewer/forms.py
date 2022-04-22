from django import forms
from django.conf import settings
from django.utils import timezone
from .models import *
from registrations.models import *
from django.contrib.auth import get_user_model
from dateutil.parser import parse
from dateutil.tz import gettz
from django.core.exceptions import ValidationError
from import_export import resources, fields as IEF, widgets as IEW
import magic
import phonenumbers
from functools import partial
from datetimewidget.widgets import DateTimeWidget
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

DateInput = partial(forms.DateInput, {'class': 'datepicker'})

class ManualUploadForm(forms.Form):
	file = forms.FileField(label = 'Choose Manual Payment File',)

	def clean_file(self):
		content = self.cleaned_data['file']
		if not content.name.split('.')[-1] == 'csv':
			raise ValidationError("Incorrect file format. Please upload csv file")
		return content

class GatewayUploadForm(forms.Form):
	file = forms.FileField(label = 'Choose Payment Gateway File ( as sent by Tech Process )',)

	def clean_file(self):
		content = self.cleaned_data['file']
		if not content.name.split('.')[-1] == 'csv':
			raise ValidationError("Incorrect file format. Please upload csv file")
		return content

class HiddenForm(forms.Form):
	file_name = forms.CharField(max_length = 254,widget = forms.HiddenInput(),)

	# def __init__(self,bits_prefix = 'bits', *args, **kwargs):
	# 	super(HiddenForm,self).__init__( *args, **kwargs )
	# 	self.bits_prefix = bits_prefix

class ManualPaymentDataUploadResource(resources.ModelResource):

	class PTFieldWidget(IEW.Widget):
		def render(self, value):
			payment_choice = dict(ManualPaymentDataUpload.PAYMENT_TYPE)
			
			return '{}'.format(payment_choice[value]) if value else ''

	class PDFieldWidget(IEW.DateWidget):
		def render(self, value):
			return '{}'.format(value.strftime('%d/%m/%y'))

	class PTField(IEF.Field):
		def clean(self, data):
			payment_type = data[self.column_name].strip()
			for k,v in ManualPaymentDataUpload.PAYMENT_TYPE:
				if v.lower() == payment_type.lower():
					return k
			else:
				 raise ValidationError("Invalid or missing payment type")

	class PRFField(IEF.Field):
		def clean(self, data):
			flag_list = { 'true':True, 'false':False, 0:False, 1:True, '0':False, '1':True }
			payment_reversal_flag = data[self.column_name].strip().lower()
			if not payment_reversal_flag in flag_list:
				raise ValidationError("Invalid or missing payment reversal flag")

			payment_type = map(lambda x:dict(ManualPaymentDataUpload.PAYMENT_TYPE)[x].lower(),['3','4'])

			try:
				payment_amount = float(data['Payment Amount'].strip())
			except ValueError as e:
				raise ValidationError("payment amount {0}".format(e))

			if flag_list[payment_reversal_flag] :
				if not (data['Payment Type'].lower() in payment_type  and payment_amount < 0):
					raise ValidationError("""
						payment type should be reversal and amount should be less than zero for flag true
						""")
			else :
				if data['Payment Type'].lower() in payment_type:
					raise ValidationError("""
						payment type is reversal for flag false
						""")


			return flag_list[payment_reversal_flag]


	class PAField(IEF.Field):
		def clean(self, data):
			payment_amount = data[self.column_name].strip()
			try:
				return float(payment_amount)
			except ValueError:
				raise ValidationError("Invalid or missing payment amount.")

	class PDField(IEF.Field):
		def clean(self, data):
			payment_date = data[self.column_name]
			tzinfos = {"IST": gettz("Asia/Kolkata")}
			try:
				return parse('{}'.format(payment_date),tzinfos=tzinfos,dayfirst=True)
			except Exception as e:
				raise ValidationError("{0}".format(e))


	class PMField(IEF.Field):
		def clean(self, data):
			payment_mode = data[self.column_name].strip()
			if payment_mode and not payment_mode.isalnum():
				raise ValidationError("Invalid payment mode.")
			return payment_mode

	class PIField(IEF.Field):
		def clean(self, data):
			payment_id = data[self.column_name].strip()
			student_application_id = data['Application ID'].strip()
			payment_type_value = data['Payment Type'].strip()
			payment_type = None
			for k,v in ManualPaymentDataUpload.PAYMENT_TYPE:
				if v.lower() == payment_type_value.lower():
					payment_type = k
			mpdu = ManualPaymentDataUpload.objects.exclude(
				application__student_application_id = student_application_id,
				payment_type = payment_type)
			if not payment_id.isalnum():
				raise ValidationError("Invalid or missing payment id.")
			if mpdu.filter(payment_id = payment_id).exists():
				raise ValidationError(
					"Duplicate entry {0} for Payment ID".format(payment_id)
					)
			return payment_id

	application = IEF.Field(column_name='Application ID',
		attribute='application',
		widget=IEW.ForeignKeyWidget(StudentCandidateApplication,'student_application_id')
		)
	payment_type = PTField(column_name='Payment Type',
		attribute = 'payment_type',widget = PTFieldWidget(),
		)
	payment_amount = PAField(column_name='Payment Amount',
		attribute = 'payment_amount',)
	payment_reversal_flag = PRFField(column_name='Reversal',
		attribute = 'payment_reversal_flag',)
	payment_date = PDField(column_name='Payment Date',
		attribute = 'payment_date',widget = PDFieldWidget() )
	payment_mode = PMField(column_name='Payment Mode',
		attribute = 'payment_mode',)
	payment_id = PIField(column_name='Payment ID',
		attribute = 'payment_id',)

	class Meta(object):
		model = ManualPaymentDataUpload
		fields = ('application', 'payment_id', 'payment_type', 
			'payment_date', 'payment_amount', 
			'payment_mode', 'payment_reversal_flag')
		export_order = fields
		import_id_fields = ('application','payment_type')

class PaymentGatewayDataUploadResource(resources.ModelResource):
	class TTIField(IEF.Field):
		def clean(self, data):
			tpsl_transaction_id = data[self.column_name].strip()
			if not tpsl_transaction_id:
				raise ValidationError("Missing tpsl Transaction id")
			return tpsl_transaction_id

	class BIField(IEF.Field):
		def clean(self, data):
			bank_id = data[self.column_name].strip()
			if not bank_id:
				raise ValidationError("Missing bank id.")
			return bank_id

	class BNField(IEF.Field):
		def clean(self, data):
			bank_name = data[self.column_name].strip()
			if not bank_name:
				raise ValidationError("Missing bank name.")
			return bank_name

	class STIField(IEF.Field):
		def clean(self, data):
			sm_transaction_id = data[self.column_name].strip()
			if not sm_transaction_id:
				raise ValidationError("Missing sm transaction id.")
			return sm_transaction_id

	class BTIField(IEF.Field):
		def clean(self, data):
			bank_transaction_id = data[self.column_name].strip()
			if not bank_transaction_id:
				raise ValidationError("Missing bank transaction id.")
			return bank_transaction_id

	class TAField(IEF.Field):
		def clean(self, data):
			total_amount = data[self.column_name].strip()
			try:
				return float(total_amount)
			except ValueError:
				raise ValidationError("Invalid or missing total amount.")

	class CField(IEF.Field):
		def clean(self, data):
			charges = data[self.column_name].strip()
			try:
				return float(charges)
			except ValueError:
				raise ValidationError("Invalid or missing charges amount.")

	class STField(IEF.Field):
		def clean(self, data):
			service_tax = data[self.column_name].strip()
			try:
				return float(service_tax)
			except ValueError:
				raise ValidationError("Invalid or missing service amount.")

	class NAField(IEF.Field):
		def clean(self, data):
			net_amount = data[self.column_name].strip()
			try:
				return float(net_amount)
			except ValueError:
				raise ValidationError("Invalid or missing net amount.")

	class TDField(IEF.Field):
		def clean(self, data):
			transaction_date = data[self.column_name].strip()
			try:
				return parse('{}'.format(transaction_date))
			except Exception as e:
				raise ValidationError("Transaction Date - {0}".format(e))

	class CNField(IEF.Field):
		def clean(self, data):
			customer_name = data[self.column_name].strip()
			if not customer_name:
				raise ValidationError("Missing customer name.")
			return customer_name


	class UEField(IEF.Field) :
		def clean(self, data):
			email = data[self.column_name].strip()
			try:
				validate_email( email.strip() )
				if len(email.strip())>50:
					raise ValidationError('Email string length more than 50.')
			except ValidationError as e:
				raise ValidationError('Email type error.')
			return email

	class MField(IEF.Field):
		def clean(self, data):
			phone = data[self.column_name].strip()
			x = phonenumbers.parse(phone,None)
			if not phonenumbers.is_valid_number(x):
				raise ValidationError('Incorrect or missing phone number.')
			return phone

	class PFDField(IEF.Field):
		def clean(self, data):
			pay_report_date = data[self.column_name]
			try:
				return parse('{}'.format(pay_report_date))
			except Exception as e:
				raise ValidationError("Payment File Date - {0}".format(e)) 

	tpsl_transaction_id = TTIField(column_name='TPSL Transaction ID',
		attribute = 'tpsl_transaction_id',)
	bank_id = BIField(column_name='Bank ID',
		attribute = 'bank_id',)
	bank_name = BNField(column_name='Bank Name',
		attribute = 'bank_name',)
	sm_transaction_id = STIField(column_name='SM Transaction ID',
		attribute = 'sm_transaction_id',)
	bank_transaction_id = BTIField(column_name='Bank Transaction ID',
		attribute = 'bank_transaction_id',)
	total_amount = TAField(column_name='Total Amount',
		attribute = 'total_amount',)
	charges = CField(column_name='Charges',
		attribute = 'charges',)
	service_tax = STField(column_name='Taxes',
		attribute = 'service_tax',)
	net_amount = NAField(column_name='Net Amount',
		attribute = 'net_amount',)
	transaction_date = TDField(column_name='Transaction Date',
		attribute = 'transaction_date',)
	src_itc_user_id = UEField(column_name='Email',
		attribute='src_itc_user_id',)
	src_itc_user_name = CNField(column_name='User Name',
		attribute = 'src_itc_user_name',)
	src_itc_mobile = MField(column_name='Mobile',
		attribute = 'src_itc_mobile',)
	src_itc_application = IEF.Field(column_name='Application ID',
		attribute = 'src_itc_application',
		widget = IEW.ForeignKeyWidget(StudentCandidateApplication,
			'student_application_id'))
	payment_report_date = PFDField(column_name='Payment File Date',
		attribute = 'payment_report_date',)


	class Meta(object):
		model = PaymentGatewayRecord
		fields = ('bank_id','bank_name','tpsl_transaction_id',
			'sm_transaction_id','total_amount',
			'charges','service_tax','net_amount','transaction_date',
			'src_itc_application','src_itc_user_id','src_itc_mobile',
			'src_itc_user_name','payment_report_date',)	
		export_order = fields
		import_id_fields = ('tpsl_transaction_id','src_itc_application')


class ManualDateandStatusForm(forms.Form):
	from_date = forms.DateField(widget=DateInput(
		format = '%d-%m-%Y'),input_formats=('%d-%m-%Y',))
	to_date = forms.DateField(widget=DateInput(
		format = '%d-%m-%Y'),input_formats=('%d-%m-%Y',))
	status = forms.ChoiceField(
		widget=forms.Select(attrs={'style':'width:50%'}),
		choices=ManualPaymentDataUpload.STATUS_MAN, required=False)


class GatewayDateandStatusForm(forms.Form):
	from_date = forms.DateField(widget=DateInput(
		format = '%d-%m-%Y'),input_formats=('%d-%m-%Y',))
	to_date = forms.DateField(widget=DateInput(
		format = '%d-%m-%Y'),input_formats=('%d-%m-%Y',))
	status = forms.ChoiceField(
		widget=forms.Select(attrs={'style':'width:50%'}),
		choices=PaymentGatewayRecord.STATUS_GATEWAY, required=False)


class DisplayPaymentGatewayDataResource(resources.ModelResource):
	tpsl_transaction_id = IEF.Field(column_name='TPSL Transaction ID',
		attribute = 'tpsl_transaction_id',)
	bank_name = IEF.Field(column_name='Bank Name',
		attribute = 'bank_name',)
	total_amount = IEF.Field(column_name='Total Amount',
		attribute = 'total_amount',)
	net_amount = IEF.Field(column_name='Net Amount',
		attribute = 'net_amount',)
	transaction_date = IEF.Field(column_name='Transaction Date',
		attribute = 'transaction_date',)
	src_itc_user_name = IEF.Field(column_name='User Name',
		attribute = 'src_itc_user_name',)
	src_itc_application = IEF.Field(column_name='Application ID',
		attribute = 'src_itc_application',
		widget = IEW.ForeignKeyWidget(StudentCandidateApplication,
			'student_application_id'))
	payment_report_date = IEF.Field(column_name='Payment File Date',
		attribute = 'payment_report_date',)


	class Meta(object):
		model = PaymentGatewayRecord
		fields = ('src_itc_application','src_itc_user_name','bank_name',
			'tpsl_transaction_id','total_amount','net_amount','transaction_date',
			'payment_report_date',
			)	
		export_order = fields
		import_id_fields = ('tpsl_transaction_id','src_itc_application')