from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.shortcuts import render
from registrations.models import *
from bits_admin.tables import *
from bits_admin.forms import *
from django.db.models.functions import *
from django.db.models import *
from django.conf import settings
from table.views import FeedDataView
from django_mysql.models import GroupConcat, ListCharField, SetCharField
from registrations.utils.table.views import FeedDataView as BitsFeedDataView
from bits_admin.utils.querysets import *
import operator
import logging
logger = logging.getLogger("main")
import time
import pandas as pd

class BaseArchiveDataView(FeedDataView):

	def get_queryset(self):
		
		query = super(BaseArchiveDataView, self).get_queryset().annotate(
				student_id=F('candidateselectionarchived_1__student_id'),
				pg_app = Concat('program__program_code',Value(' - '),
					'program__program_name',Value(' ('),
					'program__program_type',Value(')')
					),
				app_id = Case(
					When(
						candidateselectionarchived_1__new_application_id__isnull=False, 
						then = F('candidateselectionarchived_1__new_application_id')
				 ),
				default=F('student_application_id'),
				output_field=CharField(),
			),
		)

		pg1 = int(self.kwargs.get('pg',0)) or None
		status = self.kwargs.get('st') or 'n'
		pg_type = self.kwargs.get('pg_typ') or 'n'
		admit_batch = self.kwargs.get('adm_bat') or 'n'

		from_date = self.kwargs.get('fm_dt')
		to_date = self.kwargs.get('to_dt')
		from_date = from_date if not from_date == '00-00-0000' else None
		to_date = to_date if not to_date == '00-00-0000' else None

		query = query.filter(program__program_type=pg_type) if not pg_type == 'n' else query
		query = query.filter(application_status=status) if not status == 'n' else query
		query = query.filter(admit_batch=admit_batch) if not admit_batch == 'n' else query
		query = query.filter(program=pg1) if pg1 else query

		if from_date and to_date :
			query=query.filter(created_on_datetime__range = [
				dt.strptime(from_date,"%Y-%m-%d %H:%M:%S"),
				dt.strptime(to_date,"%Y-%m-%d %H:%M:%S")
				] )
		elif from_date :
			query=query.filter(created_on_datetime__gte=dt.strptime(from_date,"%Y-%m-%d %H:%M:%S") )
		elif to_date :
			query=query.filter(created_on_datetime__lte=dt.strptime(to_date,"%Y-%m-%d %H:%M:%S") )

		return query


class ApplicantAjaxDataView(FeedDataView):
	def get_queryset(self):
		query = super(ApplicantAjaxDataView, self).get_queryset().order_by('-last_updated')
		query = query.prefetch_related(
			Prefetch('applicationpayment_requests_created_3',
				queryset=ApplicationPayment.objects.filter(fee_type=1,
					application__application_status=settings.APP_STATUS[11][0]),
				to_attr='adm'),
			Prefetch('applicationpayment_requests_created_3',
				queryset=ApplicationPayment.objects.filter(fee_type=2,
					application__application_status=settings.APP_STATUS[13][0]),
				to_attr='app'),

			)
		
		pg1 = int(self.kwargs.get('pg',None))
		status = self.kwargs.get('st',None)
		from_date = self.kwargs.get('fm_dt',None)
		to_date = self.kwargs.get('to_dt',None)
		pg_type = self.kwargs.get('pg_typ',None)
		admit_batch = self.kwargs.get('adm_bat',None)

		from_date = from_date if not from_date == '00-00-0000' else None
		to_date = to_date if not to_date == '00-00-0000' else None
		pg_type = None if pg_type=='n' else pg_type
		admit_batch = None if admit_batch=='n' else admit_batch

		query = query.filter( program__program_type=pg_type ) if pg_type else query
		query = query.filter( admit_batch=admit_batch ) if admit_batch else query

		if from_date and to_date :
			query=query.filter(created_on_datetime__range = [
				dt.strptime(from_date,"%Y-%m-%d %H:%M:%S"),
				dt.strptime(to_date,"%Y-%m-%d %H:%M:%S")
				] )
		elif from_date :
			query=query.filter(created_on_datetime__gte = dt.strptime(from_date,"%Y-%m-%d %H:%M:%S") )
		elif to_date :
			query=query.filter(created_on_datetime__lte = dt.strptime(to_date,"%Y-%m-%d %H:%M:%S") )

		query = query.filter( program=pg1 ) if pg1 and pg1 > 0 else query
		query = query.filter( application_status = status ) if status and not status == 'n' else query
		query = query.annotate(
			c_l = F('current_location__location_name'),
			app_id = Case(
				When(candidateselection_requests_created_5550__new_application_id=None, 
					then=Concat('student_application_id',Value(' '))),
				default=Concat('candidateselection_requests_created_5550__new_application_id',Value(' ')),
				output_field=CharField(),
				),
			pg_name = F('program__program_name'),
			email =F('login_email__email'),
			student_id = F('candidateselection_requests_created_5550__student_id'),
			last_updated = Case(
				When(application_status__in=[settings.APP_STATUS[0][0],settings.APP_STATUS[4][0],
					settings.APP_STATUS[14][0]], 
					then=Max('applicationdocument_requests_created_1__last_uploaded_on')
					),
				When(application_status__in=[settings.APP_STATUS[5][0],settings.APP_STATUS[7][0]], 
					then=F('candidateselection_requests_created_5550__selected_rejected_on')
					),
				When(application_status__in=[settings.APP_STATUS[6][0],settings.APP_STATUS[8][0]], 
					then=F('candidateselection_requests_created_5550__offer_reject_mail_sent')
					),
				When(application_status__in=[settings.APP_STATUS[9][0],settings.APP_STATUS[10][0]], 
					then=F('candidateselection_requests_created_5550__accepted_rejected_by_candidate')
					),
				When(application_status=settings.APP_STATUS[15][0], 
					then=F('candidateselection_requests_created_5550__es_to_su_rev_dt')
					),
				When(application_status=settings.APP_STATUS[16][0], 
					then=F('candidateselection_requests_created_5550__app_rej_by_su_rev_dt')
					),
				When(application_status__in=[settings.APP_STATUS[1][0],settings.APP_STATUS[2][0],
					settings.APP_STATUS[3][0],settings.APP_STATUS[12][0], settings.APP_STATUS[17][0]],
					then=F('last_updated_on_datetime'),
					),
				When(Q(application_status=settings.APP_STATUS[13][0],
						applicationpayment_requests_created_3__fee_type='2',), #datetime for application fees paid.
					then=Min('applicationpayment_requests_created_3__payment_date')
					),
				When(Q(application_status=settings.APP_STATUS[11][0],
						applicationpayment_requests_created_3__fee_type='1',), # datetime for admission fees paid.
					then=Max('applicationpayment_requests_created_3__payment_date')
					),
				When(application_status__in=[settings.APP_STATUS[18][0],settings.APP_STATUS[19][0]],
					then=F('pre_selected_rejected_on_datetime'),
					),

				default=F('last_updated_on_datetime'),
				output_field=DateTimeField()
				),

		)
		return query


class BaseAEView(FeedDataView):

	def get_queryset(self):
		query = super(BaseAEView, self).get_queryset()
		query = query.filter(
			transfer_program__isnull = False
			).annotate(
			app_id = F('application__student_application_id'),
			pg_app = Concat('program__program_code',Value(' - '),
				'program__program_name',Value(' ('),
				'program__program_type',Value(')')
				),
			pg_adm = Concat('transfer_program__program_code',Value(' - '),
				'transfer_program__program_name',Value(' ('),
				'transfer_program__program_type',Value(')')
				),
			stud_id = F('application__candidateselection_requests_created_5550__student_id'),
			cur_status = F('application__application_status'),
			app_on = F('application__created_on_datetime'),
			)

		return query

class BaseElectiveSelectionsAppAjaxData(FeedDataView):

	def get_queryset(self):
		query = super(BaseElectiveSelectionsAppAjaxData, self).get_queryset()
		query = query.filter(application__program__in=Program.objects.filter(
					firstsemcourselist_requests_created_1__active_flag=True,
					firstsemcourselist_requests_created_1__is_elective=True
					).distinct(),)

		pg1 = int(self.kwargs.get('pg',None))
		query = query.filter(application__program=pg1 ) if pg1 and pg1 > 0 else query

		query = query.annotate(
			stud_id = Case(
				When(Q(student_id__isnull=True), then=Value(''),),
				default=F('student_id'),
				output_field=CharField(),
			),
			full_name = F('application__full_name'),
			pg_name = Concat(F('application__program__program_code'),
						Value(' - '),F('application__program__program_name')),
			c_slot = Case(
				When(Q(studentelectiveselection_1__course_id_slot__isnull=True), then=Value(''),),
				default=F('studentelectiveselection_1__course_id_slot__course_id'),
				output_field=CharField(),
			),
			c_id = Case(
				When(Q(studentelectiveselection_1__course__pk__isnull=True), then=Value(''),),
				default=F('studentelectiveselection_1__course__course_id'),
				output_field=CharField(),
			),
			c_unit = Case(
				When(Q(studentelectiveselection_1__course_units__pk__isnull=True), then=Value(''),),
				default=F('studentelectiveselection_1__course_units__course_units'),
				output_field=CharField(),
			),
			c_name = Case(
				When(Q(studentelectiveselection_1__course__pk__isnull=True), then=Value(''),),
				default=F('studentelectiveselection_1__course__course_name'),
				output_field=CharField(),
			),
			)

		return query

class BaseEMIReportAppAjaxData(BitsFeedDataView):

	def filter_queryset(self, queryset, extra_queryset):
		search = self.query_data.get("sSearch",'')
		queryset = queryset.filter(
				reduce(operator.and_, (
					Q(application__student_application_id__icontains = x)|
					Q(application__admit_batch__icontains = x)|
					Q(application__candidateselection_requests_created_5550__student_id__icontains = x)|
					Q(application__full_name__icontains = x)|
					Q(application__program__program_name__icontains = x)|
					Q(order_id__icontains = x)|
					Q(status__icontains = x)|
					Q(application__application_status__icontains = x)|
					Q(application__program__program_type__icontains = x)
					for x in search.split()
					)
				)) if search else queryset

		extra_queryset = extra_queryset.filter(
				reduce(operator.and_, (
					Q(application__student_application_id__icontains = x)|
					Q(application__admit_batch__icontains = x)|
					Q(application__candidateselectionarchived_1__student_id__icontains = x)|
					Q(application__full_name__icontains = x)|
					Q(application__program__program_name__icontains = x)|
					Q(order_id__icontains = x)|
					Q(status__icontains = x)|
					Q(application__program__program_type__icontains = x)|
					Q(application__application_status__icontains = x)
					for x in search.split()
					)
				)) if search else extra_queryset
		
		return queryset,extra_queryset

	def get_queryset(self):
		query = super(BaseEMIReportAppAjaxData, self).get_queryset()
		pg1 = int(self.kwargs.get('pg',None))
		status = self.kwargs.get('st',None)
		admit_batch = self.kwargs.get('b_id',None)
		pg_type = self.kwargs.get('p_type',None)
		pg_code = Program.objects.get(pk=pg1).program_code if pg1 else None
		query = query.filter(application__program__program_code = pg_code ) if pg_code else query
		query = query if admit_batch=='0' or not admit_batch else query.filter(application__admit_batch=admit_batch)
		query = query.filter(application__program__program_type=pg_type ) if pg_type and not pg_type == '0' else query
		query = query.filter(status=status ) if status and not status == 'n' else query

		app_id_case = lambda : Case(
				When(Q(application__candidateselection_requests_created_5550__new_application_id__isnull=False,
					application__candidateselection_requests_created_5550__application__pk=F('pk')
					), 
					then=F('application__candidateselection_requests_created_5550__new_application_id')),
				default=F('application__student_application_id'),
				output_field=CharField(),
				)

		app_id_str = GroupConcat(app_id_case(), 
			distinct=True, 
			output_field=CharField()
		)

		query = query.annotate(
			sca_id=F('application__pk'),
			app_id = app_id_str,
			student_id=F('application__candidateselection_requests_created_5550__student_id'),
			full_name=F('application__full_name'),
			pg_name=Concat('application__program__program_name',Value(' - '),
				'application__program__program_code',Value(' ('),
				'application__program__program_type',Value(')')),
			app_status=F('application__application_status'),
			admit_batch=F('application__admit_batch'),
		)
		return query.distinct()

	def get_extra_queryset(self):
		query = super(BaseEMIReportAppAjaxData, self).get_extra_queryset()
		pg1 = int(self.kwargs.get('pg',None))
		status = self.kwargs.get('st',None)
		admit_batch = self.kwargs.get('b_id')
		pg_type = self.kwargs.get('p_type',None)
		pg_code = Program.objects.get(pk=pg1).program_code if pg1 else None
		query = query.filter(application__program__program_code = pg_code ) if pg_code else query
		query = query if admit_batch=='0' or not admit_batch else query.filter(application__admit_batch=admit_batch)
		query = query.filter(status=status ) if status and not status == 'n' else query
		query = query.filter(application__program__program_type=pg_type ) if pg_type and not pg_type == '0' else query

		app_id_case = lambda : Case(
				When(Q(application__candidateselectionarchived_1__new_application_id__isnull=False,
					application__candidateselectionarchived_1__application__pk=F('pk')
					), 
					then=F('application__candidateselectionarchived_1__new_application_id')),
				default=F('application__student_application_id'),
				output_field=CharField(),
				)

		app_id_str = GroupConcat(app_id_case(), 
			distinct=True, 
			output_field=CharField()
		)

		query = query.annotate(
			sca_id=F('application__pk'),
			app_id = app_id_str,
			student_id=F('application__candidateselectionarchived_1__student_id'),
			full_name=F('application__full_name'),
			pg_name=Concat('application__program__program_name',Value(' - '),
				'application__program__program_code',Value(' ('),
				'application__program__program_type',Value(')')),
			app_status=F('application__application_status'),
			admit_batch=F('application__admit_batch'),
		)

		return query.distinct()

class DefDocView(FeedDataView):
	# missing_case = lambda self: Case(
	# 	When(
	# 		Q(
	# 			Q(
	# 				Q(applicationdocument_requests_created_1__file__isnull=True) |
	# 				Q(applicationdocument_requests_created_1__file=Value(''))
	# 			) |
	# 			Q(
	# 				Q(applicationdocument_requests_created_1__file__isnull=False) &
	# 				Q(applicationdocument_requests_created_1__rejected_by_bits_flag=True)
	# 			)
	# 		) &
	# 		Q(
	# 			Q(applicationdocument_requests_created_1__program_document_map__deffered_submission_flag=True) |
	# 			Q(applicationdocument_requests_created_1__program_document_map__mandatory_flag=True)
	# 		) &
	# 		Q(applicationdocument_requests_created_1__application=F('pk')),
	# 		then=F('applicationdocument_requests_created_1__document__document_name'),
	# 	),
	# 	output_field=CharField(),
	# )

	def get_queryset(self):
		query = super(DefDocView, self).get_queryset()
		pg1 = int(self.kwargs.get('pg',None))
		admit_batch = self.kwargs.get('adm_bat',None)
		status = self.kwargs.get('st',None)

		pdm_program_list = ProgramDocumentMap.objects.filter(deffered_submission_flag=True).values_list('program__pk', flat=True)
		query = StudentCandidateApplication.objects.filter(program__in=pdm_program_list,
			application_status__in = [x[0] for x in list(settings.APP_STATUS[0:7]) + [settings.APP_STATUS[9],settings.APP_STATUS[11]] + list(settings.APP_STATUS[15:])])

		# missing_concat = GroupConcat(self.missing_case(),
		# 	distinct=True,)
		# 	output_field=SetCharField(base_field=CharField())
		# )
		# missing_concat_str = GroupConcat(self.missing_case(),
		# 	distinct=True,
		# 	output_field=CharField()
		# )

		app_id_case = lambda : Case(
				When(Q(candidateselection_requests_created_5550__new_application_id__isnull=False,
					candidateselection_requests_created_5550__application__pk=F('pk')
					),
					then=F('candidateselection_requests_created_5550__new_application_id')),
				default=F('student_application_id'),
				output_field=CharField(),
				)

		app_id_str = GroupConcat(app_id_case(),
			distinct=True,
			output_field=CharField()
		)

		df = pd.DataFrame(list(query.values('program', 'student_application_id')))
		df2 = pd.DataFrame(
			list(ProgramDocumentMap.objects.filter(deffered_submission_flag=True).values('document_type', 'program')))
		s1 = pd.merge(df, df2, how='left', on=['program'])
		df3 = pd.DataFrame(list(
			ApplicationDocument.objects.values('application__student_application_id', 'document__id', 'reload_flag',
											   'rejected_by_bits_flag', 'program_document_map__program', 'file')))
		df3 = df3.rename(columns={'application__student_application_id': 'student_application_id',
								  'program_document_map__program': 'program',
								  'document__id': 'document_type'})
		s2 = pd.merge(s1, df3, how='left', on=["student_application_id", "document_type"])
		#To get def docs not submitted
		s3 = s2[s2['program_y'].isnull()]
		#To get def docs not submitted, some times stores doc as file with empty value
		s4 = s2[s2['file']=='']
		#To get def docs submitted but got rejected or deferred for later submission
		s5 = s2[s2.rejected_by_bits_flag.isin(['nan', True]) | s2.reload_flag.isin(['nan', True])]
		s6 = pd.concat([s3, s4, s5])
		results = s6.student_application_id.unique()
		query = query.filter(Q(student_application_id__in=results))

		# query = query.annotate(missingSet=missing_concat, missing=missing_concat_str)
		# query = query.filter(missingSet__isnull=False)

		query = query.filter(program=pg1 ) if pg1 and pg1 > 0 else query
		query = query.filter(admit_batch=admit_batch ) if admit_batch and not admit_batch == 'n' else query
		query = query.filter(application_status=status ) if status and not status == 'n' else query
		query = query.annotate(
			app_id = app_id_str,
			location = F('current_location__location_name'),
			pg_name = F('program__program_name'),
			student_id = F('candidateselection_requests_created_5550__student_id'),
			last_updated = Case(
				When(application_status__in=[settings.APP_STATUS[0][0],
					settings.APP_STATUS[4][0]],
					then=Max(F('applicationdocument_requests_created_1__last_uploaded_on'))
					),
				When(application_status__in=[settings.APP_STATUS[5][0],settings.APP_STATUS[7][0]],
					then=F('candidateselection_requests_created_5550__selected_rejected_on')
					),
				When(application_status__in=[settings.APP_STATUS[6][0],settings.APP_STATUS[8][0]],
					then=F('candidateselection_requests_created_5550__offer_reject_mail_sent')
					),
				When(application_status__in=[settings.APP_STATUS[9][0],settings.APP_STATUS[10][0]],
					then=F('candidateselection_requests_created_5550__accepted_rejected_by_candidate')
					),
				When(application_status=settings.APP_STATUS[15][0],
					then=F('candidateselection_requests_created_5550__es_to_su_rev_dt')
					),
				When(application_status=settings.APP_STATUS[16][0],
					then=F('candidateselection_requests_created_5550__app_rej_by_su_rev_dt')
					),
				When(application_status__in=[settings.APP_STATUS[1][0],settings.APP_STATUS[2][0],
					settings.APP_STATUS[3][0], settings.APP_STATUS[17][0]],
					then=F('last_updated_on_datetime'),
					),
				When(Q(application_status=settings.APP_STATUS[11][0],
						applicationpayment_requests_created_3__fee_type='1',), # datetime for admission fees paid.
					then=Max('applicationpayment_requests_created_3__payment_date')
					),
				When(application_status__in=[settings.APP_STATUS[18][0],settings.APP_STATUS[19][0]],
					then=F('pre_selected_rejected_on_datetime'),
					),
				default=F('last_updated_on_datetime'),
				output_field=DateTimeField(),
				),
			)
		return query

	def get_queryset_length(self, queryset):
		return len(queryset)

	def filter_queryset(self, queryset):
		def get_filter_arguments(filter_target):
			queries = []
			fields = [col.field for col in self.columns if col.searchable]
			for field in fields:
				key = "__".join(field.split(".") + ["icontains"])
				value = filter_target
				queries.append(Q(**{key: value}))
			return reduce(lambda x, y: x | y, queries)
		filter_text = self.query_data["sSearch"].replace(',',' ')
		if filter_text:
			for target in filter_text.split():
				queryset = queryset.filter(get_filter_arguments(target))
		return queryset


class DefDocViewForSubView(FeedDataView):
	missing_case = lambda self: Case(
		When(
			Q(
				Q(
					Q(applicationdocument_requests_created_1__file__isnull=True) |
					Q(applicationdocument_requests_created_1__file=Value(''))
				) |
				Q(
					Q(applicationdocument_requests_created_1__file__isnull=False) &
					Q(applicationdocument_requests_created_1__rejected_by_bits_flag=True)
				)
			) &
			Q(
				Q(applicationdocument_requests_created_1__program_document_map__deffered_submission_flag=True) |
				Q(applicationdocument_requests_created_1__program_document_map__mandatory_flag=True)
			) &
			Q(applicationdocument_requests_created_1__application=F('pk')),
			then=F('applicationdocument_requests_created_1__document__document_name'),
		),
		output_field=CharField(),
	)

	def get_queryset(self):
		query = super( DefDocViewForSubView, self).get_queryset()
		pg1 = int(self.kwargs.get('pg', None))
		admit_batch = self.kwargs.get('adm_bat', None)
		status = self.kwargs.get('st', None)

		pdm_program_list = ProgramDocumentMap.objects.values_list('program__pk', flat=True)
		query = StudentCandidateApplication.objects.filter(program__in=pdm_program_list,
														   application_status__in=[x[0] for x in
																				   list(settings.APP_STATUS[0:7]) + [
																					   settings.APP_STATUS[9],
																					   settings.APP_STATUS[11]] + list(
																					   settings.APP_STATUS[15:])])

		missing_concat = GroupConcat(self.missing_case(),
									 distinct=True,
									 output_field=SetCharField(base_field=CharField())
									 )
		missing_concat_str = GroupConcat(self.missing_case(),
										 distinct=True,
										 output_field=CharField()
										 )

		app_id_case = lambda: Case(
			When(Q(candidateselection_requests_created_5550__new_application_id__isnull=False,
				   candidateselection_requests_created_5550__application__pk=F('pk')
				   ),
				 then=F('candidateselection_requests_created_5550__new_application_id')),
			default=F('student_application_id'),
			output_field=CharField(),
		)

		app_id_str = GroupConcat(app_id_case(),
								 distinct=True,
								 output_field=CharField()
								 )

		query = query.annotate(missingSet=missing_concat, missing=missing_concat_str)

		query = query.filter(missingSet__isnull=False)

		query = query.filter(program=pg1) if pg1 and pg1 > 0 else query
		query = query.filter(admit_batch=admit_batch) if admit_batch and not admit_batch == 'n' else query
		query = query.filter(application_status=status) if status and not status == 'n' else query
		query = query.annotate(
			app_id=app_id_str,
			location=F('current_location__location_name'),
			pg_name=F('program__program_name'),
			student_id=F('candidateselection_requests_created_5550__student_id'),
			last_updated=Case(
				When(application_status__in=[settings.APP_STATUS[0][0],
											 settings.APP_STATUS[4][0]],
					 then=Max(F('applicationdocument_requests_created_1__last_uploaded_on'))
					 ),
				When(application_status__in=[settings.APP_STATUS[5][0], settings.APP_STATUS[7][0]],
					 then=F('candidateselection_requests_created_5550__selected_rejected_on')
					 ),
				When(application_status__in=[settings.APP_STATUS[6][0], settings.APP_STATUS[8][0]],
					 then=F('candidateselection_requests_created_5550__offer_reject_mail_sent')
					 ),
				When(application_status__in=[settings.APP_STATUS[9][0], settings.APP_STATUS[10][0]],
					 then=F('candidateselection_requests_created_5550__accepted_rejected_by_candidate')
					 ),
				When(application_status=settings.APP_STATUS[15][0],
					 then=F('candidateselection_requests_created_5550__es_to_su_rev_dt')
					 ),
				When(application_status=settings.APP_STATUS[16][0],
					 then=F('candidateselection_requests_created_5550__app_rej_by_su_rev_dt')
					 ),
				When(application_status__in=[settings.APP_STATUS[1][0], settings.APP_STATUS[2][0],
											 settings.APP_STATUS[3][0], settings.APP_STATUS[17][0]],
					 then=F('last_updated_on_datetime'),
					 ),
				When(Q(application_status=settings.APP_STATUS[11][0],
					   applicationpayment_requests_created_3__fee_type='1', ),  # datetime for admission fees paid.
					 then=Max('applicationpayment_requests_created_3__payment_date')
					 ),
				When(application_status__in=[settings.APP_STATUS[18][0], settings.APP_STATUS[19][0]],
					 then=F('pre_selected_rejected_on_datetime'),
					 ),
				default=F('last_updated_on_datetime'),
				output_field=DateTimeField(),
			),
		)
		return query

	def get_queryset_length(self, queryset):
		return len(queryset)

	def filter_queryset(self, queryset):
		def get_filter_arguments(filter_target):
			queries = []
			fields = [col.field for col in self.columns if col.searchable]
			for field in fields:
				key = "__".join(field.split(".") + ["icontains"])
				value = filter_target
				queries.append(Q(**{key: value}))
			return reduce(lambda x, y: x | y, queries)

		filter_text = self.query_data["sSearch"].replace(',', ' ')
		if filter_text:
			for target in filter_text.split():
				queryset = queryset.filter(get_filter_arguments(target))
		return queryset
		
class DefDocSubView(DefDocViewForSubView):

	document_name = lambda self, verified: When(
		~Q(applicationdocument_requests_created_1__file=Value('')) &
		Q(applicationdocument_requests_created_1__program_document_map__deffered_submission_flag=True) &
		Q(applicationdocument_requests_created_1__rejected_by_bits_flag=False) &
		Q(applicationdocument_requests_created_1__reload_flag=False) &
		Q(applicationdocument_requests_created_1__accepted_verified_by_bits_flag=verified),
		then=Concat(
			'applicationdocument_requests_created_1__document__document_name', 
			Value((': <b>VERIFIED</b>' if verified else ': <b>NOT VERIFIED</b>'))
		),
	)

	missing_case = lambda self: Case(
		self.document_name(True),
		self.document_name(False),
		output_field=CharField(),
	)

class PreSelAppView(FeedDataView):

	def get_queryset(self):
		query = super(PreSelAppView, self).get_queryset()
		pg1 = int(self.kwargs.get('pg',None))
		loc = int(self.kwargs.get('loc',None))

		query = StudentCandidateApplication.objects.filter(program__enable_pre_selection_flag = True,
				application_status__in =[
					settings.APP_STATUS[12][0],
					settings.APP_STATUS[18][0],
					settings.APP_STATUS[19][0],
					])

		app_id_case = lambda : Case(
				When(Q(candidateselection_requests_created_5550__new_application_id__isnull=False,
					candidateselection_requests_created_5550__application__pk=F('pk')
					), 
					then=F('candidateselection_requests_created_5550__new_application_id')),
				default=F('student_application_id'),
				output_field=CharField(),
				)

		app_id_str = GroupConcat(app_id_case(), 
			distinct=True, 
			output_field=CharField()
		)

		query = query.filter(program=pg1 ) if pg1 and pg1 > 0 else query
		query = query.filter(current_location=loc ) if loc and loc > 0 else query
		
		query = query.annotate(
			
			app_id = app_id_str, #This is done as a temporary workaround for search functionality
			pg_name = F('program__program_name'),
			email =F('login_email__email'),
			c_l = F('current_location__location_name'),
			last_updated = Case(
				When(application_status__in=[settings.APP_STATUS[0][0],
					settings.APP_STATUS[4][0]], 
					then=Max(F('applicationdocument_requests_created_1__last_uploaded_on'))
					),
				When(application_status__in=[settings.APP_STATUS[5][0],settings.APP_STATUS[7][0]], 
					then=F('candidateselection_requests_created_5550__selected_rejected_on')
					),
				When(application_status__in=[settings.APP_STATUS[6][0],settings.APP_STATUS[8][0]], 
					then=F('candidateselection_requests_created_5550__offer_reject_mail_sent')
					),
				When(application_status__in=[settings.APP_STATUS[9][0],settings.APP_STATUS[10][0]], 
					then=F('candidateselection_requests_created_5550__accepted_rejected_by_candidate')
					),
				When(application_status=settings.APP_STATUS[15][0], 
					then=F('candidateselection_requests_created_5550__es_to_su_rev_dt')
					),
				When(application_status=settings.APP_STATUS[16][0], 
					then=F('candidateselection_requests_created_5550__app_rej_by_su_rev_dt')
					),
				When(application_status__in=[settings.APP_STATUS[1][0],settings.APP_STATUS[2][0],
					settings.APP_STATUS[3][0], settings.APP_STATUS[17][0]],
					then=F('last_updated_on_datetime'),
					),
				When(Q(application_status=settings.APP_STATUS[11][0],
						applicationpayment_requests_created_3__fee_type='1',), # datetime for admission fees paid.
					then=Max('applicationpayment_requests_created_3__payment_date')
					),
				When(application_status__in=[settings.APP_STATUS[18][0],settings.APP_STATUS[19][0]],
					then=F('pre_selected_rejected_on_datetime'),
					),
				default=F('last_updated_on_datetime'),
				output_field=DateTimeField(),
				),
			)
		return query


class BaseEMIReportEduvAppAjaxData(BitsFeedDataView):

	def filter_queryset(self, queryset, extra_queryset):
		search = self.query_data.get("sSearch",'')
		queryset = eduv_search(queryset,search)
		extra_queryset = eduv_search(extra_queryset,search)
		
		return queryset,extra_queryset

	def get_queryset(self):
		query = get_eduv_queryset(EduvanzApplication)
		pg1 = int(self.kwargs.get('pg',None))
		admit_batch = self.kwargs.get('b_id',None)
		pg_type = self.kwargs.get('p_type',None)
		status = self.kwargs.get('st',None)
		pg_code = Program.objects.get(pk=pg1).program_code if pg1 else None
		query = query.filter(application__program__program_code = pg_code ) if pg_code else query
		query = query if admit_batch=='0' or not admit_batch else query.filter(application__admit_batch=admit_batch)
		query = query.filter(application__program__program_type=pg_type ) if pg_type and not pg_type == '0' else query
		query = query.filter(status_code=status ) if status and not status == 'n' else query

		return query

	def get_extra_queryset(self):
		query = get_eduv_queryset(EduvanzApplicationArchived)
		pg1 = int(self.kwargs.get('pg',None))
		status = self.kwargs.get('st',None)

		pg_code = Program.objects.get(pk=pg1).program_code if pg1 else None
		admit_batch = self.kwargs.get('b_id',None)
		pg_type = self.kwargs.get('p_type',None)
		query = query.filter(application__program__program_code = pg_code ) if pg_code else query
		query = query if admit_batch=='0' or not admit_batch else query.filter(application__admit_batch=admit_batch)
		query = query.filter(application__program__program_type=pg_type ) if pg_type and not pg_type == '0' else query
		query = query.filter(status_code=status ) if status and not status == 'n' else query

		return query

class BaseEMIReportEzcredAppAjaxData(FeedDataView):

	def get_queryset(self):
		pg1 = int(self.kwargs.get('pg',None))
		status = self.kwargs.get('st',None)
		admit_batch = self.kwargs.get('b_id',None)
		pg_type = self.kwargs.get('p_type',None)
		query = super(BaseEMIReportEzcredAppAjaxData, self).get_queryset()
		pg1 = int(self.kwargs.get('pg',None))
		status = self.kwargs.get('st',None)
		admit_batch = self.kwargs.get('b_id',None)
		pg_type = self.kwargs.get('p_type',None)
		pg_code = Program.objects.get(pk=pg1).program_code if pg1 else None
		query = query.filter(application__program__program_code = pg_code ) if pg_code else query
		query = query if admit_batch=='0' or not admit_batch else query.filter(application__admit_batch=admit_batch)
		query = query.filter(application__program__program_type=pg_type ) if pg_type and not pg_type == '0' else query
		query = query.filter(status=status ) if status and not status == 'n' else query

		query=query.annotate(app_id=Case(
					When(Q(application__candidateselection_requests_created_5550__new_application_id__isnull=False,
							application__candidateselection_requests_created_5550__application__pk=F('pk')
							), 
							then=F('application__candidateselection_requests_created_5550__new_application_id')),
							default=F('application__student_application_id'),
							output_field=CharField(),
							),
							app_status=F('application__application_status'),
							full_name=F('application__full_name'),
							pg_full=Concat(F('application__program__program_name'),Value(' - '),
								F('application__program__program_code'),Value(' ('),
								F('application__program__program_type'),Value(')')),
							stud_id=F('application__candidateselection_requests_created_5550__student_id'),
							adm_batch=F('application__admit_batch'),
							sca_id=F('application__pk'),

			)
		return query

class BaseEMIReportPropelldAppAjaxData(FeedDataView):

	def get_queryset(self):
		pg1 = int(self.kwargs.get('pg',None))
		status = self.kwargs.get('st',None)
		admit_batch = self.kwargs.get('b_id',None)
		pg_type = self.kwargs.get('p_type',None)
		query = super(BaseEMIReportPropelldAppAjaxData, self).get_queryset()
		pg1 = int(self.kwargs.get('pg',None))
		status = self.kwargs.get('st',None)
		admit_batch = self.kwargs.get('b_id',None)
		pg_type = self.kwargs.get('p_type',None)
		pg_code = Program.objects.get(pk=pg1).program_code if pg1 else None
		query = query.filter(application__program__program_code = pg_code ) if pg_code else query
		query = query if admit_batch=='0' or not admit_batch else query.filter(application__admit_batch=admit_batch)
		query = query.filter(application__program__program_type=pg_type ) if pg_type and not pg_type == '0' else query
		query = query.filter(status=status ) if status and not status == 'n' else query

		query=query.annotate(app_id=Case(
					When(Q(application__candidateselection_requests_created_5550__new_application_id__isnull=False,
							application__candidateselection_requests_created_5550__application__pk=F('pk')
							), 
							then=F('application__candidateselection_requests_created_5550__new_application_id')),
							default=F('application__student_application_id'),
							output_field=CharField(),
							),
							app_status=F('application__application_status'),
							fullname=F('application__full_name'),
							pg_full=Concat(F('application__program__program_name'),Value(' - '),
								F('application__program__program_code'),Value(' ('),
								F('application__program__program_type'),Value(')')),
							stud_id=F('application__candidateselection_requests_created_5550__student_id'),
							adm_batch=F('application__admit_batch'),
							sca_id=F('application__pk'),

			).order_by('created_on')

		return query		
