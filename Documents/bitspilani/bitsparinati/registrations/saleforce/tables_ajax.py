import operator
from table.views import FeedDataView
from .tables import *
class SFDataLogAjaxView(FeedDataView):
	token = salesforce_data_log().token

	def get_queryset(self):
		query = super(SFDataLogAjaxView, self).get_queryset()
		status = self.kwargs.get('status') or 'n'
		query = query.filter(status=status) if status !='n' else query
		return query

class SpecificSummaryDataAjaxView(FeedDataView):
	token = specific_program_summary_data().token

	def filter_queryset(self, queryset):
		search = self.query_data.get("sSearch", '')
		queryset = queryset.filter(
			reduce(operator.and_, (
				Q(specific_program_id__program_code__icontains=x)|
				Q(specific_program_id__program_name__icontains = x)|
				Q(specific_program_id__program_type__icontains=x)
				for x in search.split()
			)
				   )) if search else queryset
		return queryset

	def get_queryset(self):
		query = super(SpecificSummaryDataAjaxView, self).get_queryset()
		program = self.kwargs.get('program')

		if program and program != 'n':
			query = query.filter(specific_program_id=program)

		return query

