from table import Table
from table.columns import Column
from table.columns import LinkColumn, Link, DatetimeColumn
from django.utils.html import format_html
from django.core.urlresolvers import reverse_lazy
from django.utils.html import escape
from table.utils import Accessor
from dateutil.parser import parse
from datetime import datetime
from django.utils import timezone
import pytz
from bits_admin.table_filter_column import *
from .models import AdhocZestEmiTransaction, AdhocEduvanzApplication
from .models import AdhocZestEmiTransaction, AdhocEduvanzApplication, AdhocPropelldApplication


def adhoc_zest_paging(ajax_url=None,):
	class AdhocZestTable(Table):

		email = FilterColumn( field='email', header='Student ID' )
		loan_applied_on = DTColumn( field='requested_on', header='Loan Applied On', searchable=False)
		zest_id = FilterColumn( field='order_id', header='Zest Order ID', header_attrs={'width':'10%'})
		pay_dt = DTColumn( field='approved_or_rejected_on', header='Payment Date', searchable=False)
		loan_status = ZestStatusColumn( field='status', header='Current Loan Status' )
		
		class Meta(object):
			model = AdhocZestEmiTransaction
			ajax = True
			pagination = True
			ajax_source = reverse_lazy(ajax_url)

	return AdhocZestTable

def adhoc_eduv_paging(ajax_url=None,):
	class AdhocEduvTable(Table):

		email = FilterColumn( field='email', header='Student ID' )
		lead_id = Column( field='lead_id', header='Eduvanz Lead ID' )
		loan_applied_on = DTColumn( field='created_on', header='Loan Applied On', searchable=False)
		loan_paid_on = PaidDateColumn( field='updated_on', header='Payment Date', searchable=False)
		last_upd = DTColumn( field='updated_on', header='Last Status Update Date', searchable=False)
		eduv_id = FilterColumn( field='order_id', header='Eduvanz Order ID', header_attrs={'width':'10%'})
		loan_status = EduvStatusColumn( field='status_code', header='Current Loan Status' )
		
		class Meta(object):
			model = AdhocEduvanzApplication
			ajax = True
			pagination = True
			ajax_source = reverse_lazy(ajax_url)

	return AdhocEduvTable

def adhoc_propelld_paging(ajax_url=None,):
	class AdhocProTable(Table):

		email = FilterColumn( field='email', header='Student / Applicant email ID' )
		loan_applied_on = DTColumn( field='created_on', header='Loan Applied On', searchable=False)
		quote_id = FilterColumn( field='quote_id', header='Propelld Quote ID', header_attrs={'width':'10%'})
		loan_paid_on = DTColumn( field='disbursement_date', header='Payment Date', searchable=False)
		lst_upd = DTColumn( field='updated_on', header='Last Status Update Date', searchable=False)
		loan_status = PropelldStatusColumn( field='status', header='Current Loan Status' )
		utr_number = FilterColumn(field = 'utr_number', header = 'UTR Number', searchable = False)
		
		class Meta(object):
			model = AdhocPropelldApplication
			ajax = True
			pagination = True
			ajax_source = reverse_lazy(ajax_url)
			ordering = ['-loan_applied_on']
			# sortable =True

	return AdhocProTable

