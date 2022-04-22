from master.models import *
from table import Table
from master.utils.datatable.columns import *
from table.columns import Column, LinkColumn


class PreviewHTicketTable(Table):
	source = FilterColumn( field = 'code', header = 'Course Code')
	record = FilterColumn(field='cname', header='Course Name')
	sync_on = DTColumn( field = 'eslot', 
			header = 'Exam Slot', sortable = False, searchable=False )
	parameter = FilterColumn(field='evenue', header='Exam Venue')
	
	

	class Meta(object):
		model = HallTicket
		ajax = False
		pagination = False
		search=False
