from master.models import *
from table import Table
from master.utils.datatable.columns import *
from table.columns import Column, LinkColumn
from django.urls import reverse_lazy


class APPLCenterSyncLogTable(Table):
	source = Column( field = 'source', 
			header = 'Source', sortable = True, searchable=False )
	sync_on = DTColumn( field = 'synced_on', 
			header = 'Sync Date', sortable = False, searchable=False )
	record = Column(field='records_pulled', header='Records Pulled')
	parameter = HTMLColumn(field='parameters', header='Parameters')
	status = Column(field='status', header='Status')
	

	class Meta(object):
		model = DataSyncLogs
		ajax = True
		pagination = True
		page_length = 5
		length_menu = False
		search=False
		ajax_source = reverse_lazy('administrator:admin_ajax:data-sync-log-ajax')
