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
from semester_api.models import SemMetaZest, SemZestEmiTransaction

class SemZestEmiTable(Table):

	student_id = FilterColumn( field='student_id', header='Student ID' )
	loan_applied_on = DTColumn( field='requested_on', header='Loan Applied On', searchable=False)
	zest_id = FilterColumn( field='order_id', header='Zest Order ID', header_attrs={'width':'10%'})
	loan_status = ZestStatusColumn( field='status', header='Current Loan Status')
	approved_or_rejected_on = DTColumn( field='approved_or_rejected_on', header='Approved On')

	class Meta(object):
		model = SemZestEmiTransaction
		ajax = True
		pagination = True
		ajax_source = reverse_lazy('semester_api:emi-report-ajax')