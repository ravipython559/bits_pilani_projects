from .models import *
from registrations.models import *
from table import Table
from table.utils import A, mark_safe
from table.columns import Column
from table.columns import LinkColumn, Link, DatetimeColumn,CheckboxColumn
from django.utils.html import format_html
from django.core.urlresolvers import reverse_lazy
from django.conf import settings
from table.utils import Accessor
from django.utils.html import escape
from dateutil.parser import parse
from datetime import datetime
from django.utils import timezone
import pytz

# Pagination for historical manual payments
def manual_payment_paging(status = None, from_date = None, to_date = None ):

	class DateTimeBitsColumn( DatetimeColumn ):
		def render(self, value):
			datetime = Accessor(self.field).resolve(value)
			text = timezone.localtime(datetime).strftime("%d/%m/%Y") if datetime else ''
			return escape(text)


	class ManualPaymentTable(Table):
		action = LinkColumn(header = 'Application ID',field='app_id', links=[
			Link(text=A('app_id'), 
			viewname='payment_reviewer:admin-application-views', 
			args=(A('sca_pk'),)
			),])	

		payment_id = Column( field = 'payment_id', header = 'Payment ID' )

		payment_type = Column( field = 'pay_type', header = 'Payment Type' )

		payment_date = DateTimeBitsColumn( field = 'payment_date', 
			header = 'Payment Date',searchable=False, )

		payment_amount = Column( field='payment_amount', header = 'Payment Amount',
		searchable=False )
		
		payment_mode = Column( field = 'payment_mode',
		 header = 'Payment Mode' )

		payment_reversal_flag = Column(field = 'payment_reversal_flag' ,
			header = 'Reversal',searchable=False)

		status = Column( field = 'man_status',header = 'Status' )

		accepted_rejected_datetime = DateTimeBitsColumn(field = 'accepted_rejected_datetime' ,
			header = 'Accepted / Rejected on',searchable=False )
			
		class Meta(object):
			model = ManualPaymentDataUpload
			ajax = True
			pagination = True
			ajax_source = reverse_lazy('payment_reviewer:hist-manual-payments-ajax',kwargs = {
				'st': status or 'n',
				'to_dt': to_date or '00-00-0000',
				'fm_dt': from_date or '00-00-0000',
				})

	return ManualPaymentTable

# Pagination for historical gateway payments
def gateway_payment_paging(status = None, from_date = None, to_date = None ):

	class DateTimeBitsColumn( DatetimeColumn ):
		def render(self, value):
			datetime = Accessor(self.field).resolve(value)
			text = timezone.localtime(datetime).strftime("%d/%m/%Y") if datetime else ''
			return escape(text)


	class GatewayPaymentTable(Table):
		action = LinkColumn(header = 'Application ID',field='app_id', links=[
			Link(text=A('app_id'), 
			viewname='payment_reviewer:admin-application-views', 
			args=(A('sca_pk'),)
			),])		

		src_itc_user_name = Column( field = 'src_itc_user_name', header = 'User Name' )

		bank_name = Column( field = 'bank_name', header = 'Bank Name' )

		tpsl_transaction_id = Column( field='tpsl_transaction_id', header = 'TPSL Transaction ID' )
		
		total_amount = Column( field = 'total_amount', header = 'Total Amount' ,searchable=False)

		net_amount = Column(field = 'net_amount' , header = 'Net Amount',searchable=False)

		transaction_date = DateTimeBitsColumn( field = 'transaction_date',
			header = 'Transaction Date',searchable=False, format="%d/%m/%Y" )

		status = Column( field = 'gp_status',header = 'Status' )

		accepted_rejected_datetime = DateTimeBitsColumn(field = 'accepted_rejected_datetime' ,
			header = 'Accepted / Rejected On',searchable=False)
			
		class Meta(object):
			model = PaymentGatewayRecord
			ajax = True
			pagination = True
			ajax_source = reverse_lazy('payment_reviewer:hist-gateway-payments-ajax',kwargs = {
				'st': status or 'n',
				'to_dt': to_date or '00-00-0000',
				'fm_dt': from_date or '00-00-0000',
				})

	return GatewayPaymentTable



def review_manual_payment_upload( file_name = None, prefix = 'bits' ):

	class ManualPaymentTable(Table):	

		class DateTimeBitsColumn( DatetimeColumn ):
			def render(self, value):
				datetime = Accessor(self.field).resolve(value)
				text = timezone.localtime(datetime).strftime("%d/%m/%Y") if datetime else ''
				return escape(text)

		class BitsCheckboxColumn( CheckboxColumn ):
			def render(self, value):
				accept_reject = Accessor(self.field).resolve(value)
				args = {'pfx':prefix,'id':value.id}
			
				if accept_reject:
					return mark_safe(
						'''
						<input checked type="checkbox" value="%(id)s" 
						 name="%(pfx)s_check_name_%(id)s"
						 id="%(pfx)s_check_id_%(id)s">
						<input type="hidden" value="%(id)s" name="%(pfx)s_hidden_name_%(id)s"
						 id="%(pfx)s_hidden_id_%(id)s">
						'''% args
						)
				else :
					return mark_safe(
						'''
						<input type="checkbox" name="%(pfx)s_check_name_%(id)s" 
						 value="%(id)s"
						 id="%(pfx)s_check_id_%(id)s">
						<input type="hidden" value="%(id)s" name="%(pfx)s_hidden_name_%(id)s"
						 id="%(pfx)s_hidden_id_%(id)s">
						'''% args
						)

		action = LinkColumn(header = 'Application ID',field='app_id', links=[
			Link(text=A('app_id'), 
			viewname='payment_reviewer:admin-application-views', 
			args=(A('sca_pk'),)
			),])	

		payment_id = Column( field = 'payment_id', header = 'Payment ID' )

		payment_type = Column( field = 'pay_type', header = 'Payment Type' )

		payment_date = DateTimeBitsColumn( field = 'payment_date', 
			header = 'Payment Date' )

		payment_amount = Column( field='payment_amount', header = 'Payment Amount' )
		
		payment_mode = Column( field = 'payment_mode',
		 header = 'Payment Mode' )

		payment_reversal_flag = Column(field = 'payment_reversal_flag' ,
			header = 'Reversal')

		status = Column( field = 'man_status',header = 'Status' )

		accepted_rejected_datetime = DateTimeBitsColumn(field = 'accepted_rejected_datetime',
			header = 'Accepted / Rejected on')
		accepted_rejected = BitsCheckboxColumn(field='acc_rej', header = 'Approve/Reject')

		bits_prefix = prefix
			
		class Meta(object):
			model = ManualPaymentDataUpload
			ajax = True
			pagination = True
			ajax_source = reverse_lazy('payment_reviewer:rec-manual-payments-ajax',
				kwargs = {'file_name':file_name}
				)

	return ManualPaymentTable

def review_gateway_payment_upload( file_name = None, prefix = 'bits' ):

	class GatewayPaymentTable(Table):
		class DateTimeBitsColumn( DatetimeColumn ):
			def render(self, value):
				datetime = Accessor(self.field).resolve(value)
				text = timezone.localtime(datetime).strftime("%d/%m/%Y") if datetime else ''
				return escape(text)
	

		class MissingBitsColumn( Column ):
			def render(self, value):
				missing_in_application_center = Accessor(self.field).resolve(value)

				ap = ApplicationPayment.objects.filter(
					application = value.sca_pk,
					transaction_id=value.tpsl_transaction_id,
					payment_id=value.sm_transaction_id,
				)
				return escape('Yes' if ap.exists() else 'No')

		class BitsCheckboxColumn( CheckboxColumn ):
			def render(self, value):
				accept_reject = Accessor(self.field).resolve(value)
				args = {'pfx':prefix,'id':value.id}
			
				if accept_reject:
					return mark_safe(
						'''
						<input checked type="checkbox" value="%(id)s" 
						 name="%(pfx)s_check_name_%(id)s"
						 id="%(pfx)s_check_id_%(id)s">
						<input type="hidden" value="%(id)s" name="%(pfx)s_hidden_name_%(id)s"
						 id="%(pfx)s_hidden_id_%(id)s">
						'''% args
						)
				else :
					return mark_safe(
						'''
						<input type="checkbox" name="%(pfx)s_check_name_%(id)s" 
						 value="%(id)s"
						 id="%(pfx)s_check_id_%(id)s">
						<input type="hidden" value="%(id)s" name="%(pfx)s_hidden_name_%(id)s"
						 id="%(pfx)s_hidden_id_%(id)s">
						'''% args
						)

		action = LinkColumn(header = 'Application ID',field='app_id', links=[
			Link(text=A('app_id'), 
			viewname='payment_reviewer:admin-application-views', 
			args=(A('sca_pk'),)
			),])	

		src_itc_user_name = Column( field = 'src_itc_user_name',
			header = 'User Name' )
		bank_name = Column( field = 'bank_name',
			header = 'Bank Name' )
		tpsl_transaction_id = Column( field = 'tpsl_transaction_id',
			header = 'TPSL Transaction ID' )
		total_amount = Column( field = 'total_amount',
			header = 'Total Amount' )
		net_amount = Column( field = 'net_amount',
			header = 'Net Amount' )
		transaction_date = DateTimeBitsColumn( field = 'transaction_date', 
			header = 'Transaction Date',format="%d/%m/%Y"  )
		status = Column( field = 'gateway_status',header = 'Status' )
		missing_in_application_center = MissingBitsColumn( field = 'tpsl_transaction_id',
			header = 'Present In App Center' )
		accepted_rejected = BitsCheckboxColumn(field='acc_rej',
			header = 'Approve/Reject')

		bits_prefix = prefix
			
		class Meta(object):
			model = PaymentGatewayRecord
			ajax = True
			pagination = True
			ajax_source = reverse_lazy('payment_reviewer:rec-gateway-payments-ajax',
				kwargs = {'file_name':file_name}
				)

	return GatewayPaymentTable

#payment data view table start
def usr_payment_filter_paging(from_date = None, to_date = None, count = None, bank =None ):

	class DateTimeBitsColumn( DatetimeColumn ):
		def render(self, value):
			datetime = Accessor(self.field).resolve(value)
			text = timezone.localtime(datetime).strftime("%d-%m-%Y %I:%M %p") if datetime else ''
			return escape(text)

	class FilterColumn( Column ):
		def render(self, value):
			data = Accessor(self.field).resolve(value)
			
			return escape(data if data else '')

	class PaymentBankColumn(Column):
		def render(self, value):
			data = Accessor(self.field).resolve(value)
			if data:
				if data.isnumeric(): #to check if the unicode field value is an integer
					text = 'Tech Process'
				else:
					text = data
			else:
				text = ''
			return escape(text)

	class SCATable(Table):

		action = LinkColumn(header = 'Application ID',field='app_id', links=[
			Link(text=A('app_id'), 
			viewname='payment_reviewer:admin-application-views', 
			args=(A('id'),)
			),])

		finalName = Column( field = 'full_name', header = 'Name' )

		pg_name = Column( field='full_prog', header = 'Program Applied for' )

		created_on_datetime = DateTimeBitsColumn( field = 'created_on_datetime', 
			header = 'Applied On', searchable=False )

		payment_date = DateTimeBitsColumn( field = 'payment_date', 
			header = 'Payment Date', searchable=False )

		payment_amount = FilterColumn( field='payment_amount',
			header = 'Payment Amount', searchable=False )

		payment_bank = PaymentBankColumn( field='payment_bank',
			header = 'Payment Bank' )

		transaction_id = FilterColumn( field='transaction_id',
			header = 'Transaction ID', searchable=False )

		class Meta(object):
			model = StudentCandidateApplication
			ajax = True
			pagination = True
			search_placeholder='Search by Application ID or Applicant Name'
			ajax_source = reverse_lazy('payment_reviewer:pay_app_table_data',
				kwargs = {
				'to_dt': to_date or '00-00-0000',
				'fm_dt': from_date or '00-00-0000',
				'bank': bank or 'n',
				})

	return SCATable
#payment data view table end