from table.views import FeedDataView
from registrations.tables import *
from django.db.models.functions import *
from django.db.models import *
from registrations.models import *
from django.conf import settings
from bits_admin.tables_ajax import BaseAEView as BAdminAEV
from registrations.utils.table.views import FeedDataView as BitsFeedDataView
import operator
from django.db.models import Prefetch, Case, When
from dateutil.parser import parse
from bits_admin.utils.datetime import *
from bits_admin.tables import inbound_call_log_paging, outbound_call_log_paging
from django.db import models
from django.db.models.functions import Concat, Value
from django_mysql.models import (GroupConcat, ListCharField, functions as MySqlFunc)

india = settings.INDIAN_TIME_ZONE

class  BaseAEView(BAdminAEV):pass

class BaseMilestoneView(FeedDataView):
	def filter_queryset(self, queryset):
		search = self.query_data.get("sSearch",'')
		queryset = queryset.filter(
			reduce(operator.and_, (
				Q(candidateselection_requests_created_5550__new_application_id__icontains = x )|
				Q(student_application_id__icontains = x )|
				Q(program__program_code__icontains = x )|
				Q(program__program_name__icontains = x )|
				Q(program__program_type__icontains = x )|
				Q(application_status__icontains = x )|
				Q(full_prog__icontains = x )|
				Q(fee_waiver__icontains = x )|
				Q(adm_batch__icontains  = x)
				for x in search.split()
				)
			)) if search else queryset
		filter_batch = self.kwargs.get('b_id')
		filter_program = self.kwargs.get('p_id')
		filter_program_type = self.kwargs.get('p_type')
		queryset = queryset.filter(program__program_type=filter_program_type ) if filter_program_type and not filter_program_type == '0' else queryset
		queryset = queryset if filter_program=='0' or not filter_program else queryset.filter(program=filter_program)
		queryset = queryset if filter_batch=='0' or not filter_batch else queryset.filter(admit_batch=filter_batch)
		return queryset

	def get_queryset(self):
		query = super(BaseMilestoneView, self).get_queryset()
		eloa = ExceptionListOrgApplicants.objects.filter(
			Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
			exception_type = 2,
			application__isnull = False,
			).values('employee_email','program')
		query = query.annotate(
			full_prog = Concat('program__program_name',Value(' - '),
				'program__program_code',Value(' ('),
				'program__program_type',Value(')')),
			app_id = Case(
				When(candidateselection_requests_created_5550__new_application_id__isnull = True, 
					then=Concat('student_application_id',Value(' '))),
				default=Concat('candidateselection_requests_created_5550__new_application_id',Value(' ')),
				output_field=CharField(),
				),
			off_rej_date = F('candidateselection_requests_created_5550__offer_reject_mail_sent'),
			acc_rej_cand_date = F('candidateselection_requests_created_5550__accepted_rejected_by_candidate'),
			doc_sub_date = Max(
				Case(
					When(~(
							Q(application_status=settings.APP_STATUS[14][0])|
							Q(application_status=settings.APP_STATUS[3][0])
							),
						then=F('applicationdocument_requests_created_1__last_uploaded_on'),
						),
					),
				output_field=DateField(),
				),
			fee_waiver = Case(
				When(
					login_email__email__in = eloa.values_list('employee_email',flat=True),
					then=Value('Admission Fee waived')
					),
				default=Value('-'),
				output_field=CharField(),
				),
			profile_created_date = F('login_email__date_joined'),
			pre_selected_rejected_date=F('pre_selected_rejected_on_datetime'),
			adm_batch = F('admit_batch'),
			fee_paym_deadline_date =F('candidateselection_requests_created_5550__fee_payment_deadline_dt'),
			pgtype= F('program__program_type'),
		)
		return query

	def sort_queryset(self, queryset):
		def get_sort_arguments():
			arguments = []
			
			for key, value in self.query_data.items():
				if not key.startswith("iSortCol_"):
					continue
				if not self.columns[value].field: return None

				field = self.columns[value].field.replace('.', '__')
				dir = self.query_data["sSortDir_" + key.split("_")[1]]
				if dir == "asc":
					arguments.append(field)
				else:
					arguments.append("-" + field)
			return arguments
		order_args = get_sort_arguments()

		if order_args:
			queryset = queryset.order_by(*order_args)
		else:
			ap = ApplicationPayment.objects.filter(fee_type='1')
			
			if  'iSortCol_0' in self.query_data:
				dir = self.query_data['sSortDir_0']
				
				if self.query_data['iSortCol_0'] == 6:
					ap = ap.order_by('{0}{1}'.format('' if dir=='asc' else '-','payment_date'))

				ex_app = list(StudentCandidateApplication.objects.exclude(
					pk__in = ap.values_list('application',flat=True) 
					).values_list('pk',flat=True))
				app = list(ap.values_list('application',flat=True))

				preserved = Case(*[When(pk=pk,
				 then=pos) for pos, pk in enumerate((ex_app + app) if dir=='asc' else (app + ex_app) )])
				queryset = queryset.filter(
					pk__in = app + ex_app
					).order_by(preserved)
		return queryset

class BaseWaiverReportDataView(BitsFeedDataView):

	def filter_queryset(self, queryset, extra_queryset):
		search = self.query_data.get("sSearch",'')
		queryset = queryset.filter(
			reduce(operator.and_, (
				Q(employee_name__icontains = x )|
				Q(employee_email__icontains = x )|
				Q(program__program_code__icontains = x )|
				Q(program__program_name__icontains = x )|
				Q(program__program_type__icontains = x )|
				Q(org__org_name__icontains = x )|
				Q(app_status__icontains = x )|
				Q(app_id__icontains = x )|
				Q(full_prog__icontains = x )|
				Q(student_id__icontains = x )|
				Q(adm_batch__icontains  = x)
				for x in search.split()
				)
			)) if search else queryset

		extra_queryset = extra_queryset.filter(
			reduce(operator.and_, (
				Q(employee_name__icontains = x )|
				Q(employee_email__icontains = x )|
				Q(program__icontains = x )|
				Q(org__icontains = x )|
				Q(app_status__icontains = x )|
				Q(app_id__icontains = x )|
				Q(full_prog__icontains = x )|
				Q(student_id__icontains = x )|
				Q(adm_batch__icontains  = x)
				for x in search.split()
				)
			)) if search else extra_queryset

		return queryset, extra_queryset

	def get_queryset(self):

		queryset = super(BaseWaiverReportDataView, self).get_queryset().filter(Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True))
		admit_batch =  self.kwargs.get('b_id')
		eloa_with_count_two = queryset.filter(
				exception_type__in=['1','2']
			).values(
			'employee_email','program'
			).annotate(
			emp_count = Count('pk'),
			pks = GroupConcat('pk'), 
			).distinct().filter(emp_count=2)
		exclude_list = map(lambda x:int(x['pks'].split(',')[0]),eloa_with_count_two)
		include_list = map(lambda x:int(x['pks'].split(',')[1]),eloa_with_count_two)
		queryset = queryset.exclude(
				pk__in = exclude_list
			).annotate(emp_type=Case(
			When(
				Q(pk__in = include_list),
				then=Value('Application and Admission Fees')
				),
			When(
				Q(exception_type='2'),
				then=Value('Admission Fees')
				),
			When(
				Q(exception_type='1'),
				then=Value('Application Fees')
				),
			output_field=CharField(),
			),

			cod = F('application__created_on_datetime'),
			app_id = Case(
						When(application__candidateselection_requests_created_5550__new_application_id__isnull = True, 
							then=Concat('application__student_application_id',Value(' '))),
						default=Concat('application__candidateselection_requests_created_5550__new_application_id',Value(' ')),
						output_field=CharField(),
						),
			student_id = F('application__candidateselection_requests_created_5550__student_id'),
			app_status = F('application__application_status'),
			adm_batch = F('application__admit_batch'),
			full_prog = Concat('program__program_name',Value(' - '),
				'program__program_code',Value(' ('),
				'program__program_type',Value(')')),

		)

		queryset = queryset if admit_batch=='0' or not admit_batch else queryset.filter(application__admit_batch=admit_batch)

		return queryset.distinct()

	def get_extra_queryset(self):

		queryset = super(BaseWaiverReportDataView, self).get_extra_queryset().filter(Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True))
		admit_batch =  self.kwargs.get('b_id')
		eloa_with_count_two = queryset.filter(
			exception_type__in=['1','2']
		).values('employee_email','program', 'run').annotate(
			emp_count = Count('pk'),
			pks = GroupConcat('pk'), 
		).distinct().filter(emp_count=2)
		exclude_list = map(lambda x:int(x['pks'].split(',')[0]), eloa_with_count_two)
		include_list = map(lambda x:int(x['pks'].split(',')[1]), eloa_with_count_two)
		queryset = queryset.exclude(
				pk__in = exclude_list
			).annotate(emp_type=Case(
			When(
				Q(pk__in = include_list),
				then=Value('Application and Admission Fees')
				),
			When(
				Q(exception_type='2'),
				then=Value('Admission Fees')
				),
			When(
				Q(exception_type='1'),
				then=Value('Application Fees')
				),
			output_field=CharField(),
			),

			cod = F('application__created_on_datetime'),
			app_id = Case(
						When(application__candidateselectionarchived_1__new_application_id__isnull = True, 
							then=Concat('application__student_application_id',Value(' '))),
						default=Concat('application__candidateselectionarchived_1__new_application_id',Value(' ')),
						output_field=CharField(),
						),
			student_id = F('application__candidateselectionarchived_1__student_id'),
			app_status = F('application__application_status'),
			adm_batch = F('application__admit_batch'),
			full_prog = F('program'),

		)


		queryset = queryset if admit_batch=='0' or not admit_batch else queryset.filter(application__admit_batch=admit_batch)

		return queryset.distinct()


class ReviewerDataView(FeedDataView):
	def get_queryset(self):
		query = super(ReviewerDataView, self).get_queryset()
		pg1 = int(self.kwargs.get('pg',None))
		pg_type = self.kwargs.get('pg_typ',None)
		status = self.kwargs.get('st',None)
		admit_batch = self.kwargs.get('adm_bat', None)
		query = query.filter( program=pg1 ) if pg1 and pg1 > 0 else query
		query = query.filter( program__program_type=pg_type ) if pg_type and not pg_type == 'n' else query
		query = query.filter( application_status = status ) if status and not status == 'n' else query
		query = query.filter(admit_batch=admit_batch) if admit_batch and not admit_batch == 'n' else query
		query = query.filter(
			application_status__in=[ x[0] for x in settings.APP_STATUS[:12]]+[settings.APP_STATUS[17][0]]
			)
		query = query.prefetch_related(
			Prefetch('applicationpayment_requests_created_3',
				queryset=ApplicationPayment.objects.filter(fee_type=1,
					application__application_status=settings.APP_STATUS[11][0]),
				to_attr='adm'),
			).annotate(
		su_comment=F('candidateselection_requests_created_5550__su_rev_com'),
		rev_comment=F('candidateselection_requests_created_5550__es_com'),
		app_id = Case(
			When(candidateselection_requests_created_5550__new_application_id=None, 
				then=Concat('student_application_id',Value(' '))),
			default=Concat('candidateselection_requests_created_5550__new_application_id',Value(' ')),
			output_field=CharField(),
			),
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
			output_field=DateTimeField()
			),
		)
		return query

class BaseProgChangeReport(BitsFeedDataView):
	def filter_queryset(self, queryset, extra_queryset):
		search = self.query_data.get("sSearch",'')
		queryset = queryset.filter(
				reduce(operator.and_, (
					Q(app_id__icontains = x )|
					Q(old_prog__icontains = x)|
					Q(student_id__icontains = x )|
					Q(old_student_id__icontains = x )|
					Q(new_prog__icontains = x )|
					Q(application_status__icontains = x )|
					Q(adm_batch__icontains  = x)
					for x in search.split()
					)
				)) if search else queryset

		extra_queryset = extra_queryset.filter(
				reduce(operator.and_, (
					Q(app_id__icontains = x )|
					Q(old_prog__icontains = x)|
					Q(student_id__icontains = x )|
					Q(old_student_id__icontains = x )|
					Q(new_prog__icontains = x )|
					Q(application_status__icontains = x )|
					Q(adm_batch__icontains  = x)
					for x in search.split()
					)
				)) if search else extra_queryset
		
		return queryset,extra_queryset
		

	def get_queryset(self):
		admit_batch =  self.kwargs.get('b_id')
		queryset = super(BaseProgChangeReport, self).get_queryset().filter(
			candidateselection_requests_created_5550__new_sel_prog__isnull=False
		).annotate(
			app_id = Case(
				When(
					candidateselection_requests_created_5550__new_application_id=None, 
					then=Concat(
						'student_application_id',
						Value(' ')
					)
				),
				default=Concat('candidateselection_requests_created_5550__new_application_id',Value(' ')),
				output_field=CharField(),
			),
			student_id = F('candidateselection_requests_created_5550__student_id'),
			old_student_id = F('candidateselection_requests_created_5550__old_student_id'),
			old_prog = Concat(
				'candidateselection_requests_created_5550__new_sel_prog__program_name',
				Value(' - '),
				'candidateselection_requests_created_5550__new_sel_prog__program_code',
				Value(' ('),
				'candidateselection_requests_created_5550__new_sel_prog__program_type',
				Value(')')
			),
			prog_changed_on = F('candidateselection_requests_created_5550__app_rej_by_su_rev_dt'),
			adm_batch = F('admit_batch'),
			new_prog = Concat(
				'program__program_code',Value(' - '),
				'program__program_name',Value(' ('),
				'program__program_type',Value(')')
			),
		)

		queryset = queryset if admit_batch=='0' or not admit_batch else queryset.filter(admit_batch=admit_batch)

		return queryset.distinct()

	def get_extra_queryset(self):
		admit_batch =  self.kwargs.get('b_id')

		queryset = super(BaseProgChangeReport, self).get_extra_queryset().filter(
			candidateselectionarchived_1__new_sel_prog__isnull=False
		).annotate(
			app_id = Case(
				When(
					candidateselectionarchived_1__new_application_id=None, 
					then=Concat(
						'student_application_id',
						Value(' ')
					)
				),
				default=Concat('candidateselectionarchived_1__new_application_id',Value(' ')),
				output_field=CharField(),
			),
			student_id = F('candidateselectionarchived_1__student_id'),
			old_student_id = F('candidateselectionarchived_1__old_student_id'),
			old_prog = F('candidateselectionarchived_1__new_sel_prog'),
			prog_changed_on = F('candidateselectionarchived_1__app_rej_by_su_rev_dt'),
			adm_batch = F('admit_batch'),
			new_prog = Concat(
				'program__program_code',Value(' - '),
				'program__program_name',Value(' ('),
				'program__program_type',Value(')')
			),
		)

		queryset = queryset if admit_batch=='0' or not admit_batch else queryset.filter(admit_batch=admit_batch)

		return queryset.distinct()
		
class BaseProgramLocationReportAjax(FeedDataView):

	def get_queryset(self):
		query = super(ProgramLocationReportAjax, self).get_queryset()
		
		prog = int(self.kwargs.get('prog',None))
		prog = None if prog==0 else prog
		loc = int(self.kwargs.get('loc',None))
		loc = None if loc==0 else loc

		query = query.filter(current_location__pk=loc) if loc else query
		query = query.filter(program__pk=prog) if prog else query

		query = query.values('program','current_location')
		query = query.annotate(
			full_pg = Concat('program__program_name',Value(' - '),
				'program__program_code',Value(' ('),
				'program__program_type',Value(')')),
			loc_name = F('current_location__location_name'),
			sub=Count(
				Case(
					When(application_status =settings.APP_STATUS[12][0],
						then=F('application_status'),
						),
					),
				),
			app_fees_paid=Count(
				Case(
					When(application_status =settings.APP_STATUS[13][0],
						then=F('application_status'),
						),
					),
				),
			adm_fees_paid=Count(
				Case(
					When(application_status =settings.APP_STATUS[11][0],
						then=F('application_status'),
						),
					),
				),
			total_status_count=Count(
				Case(
					When(application_status__in =[settings.APP_STATUS[13][0],
						settings.APP_STATUS[12][0],
						settings.APP_STATUS[11][0],],
						then=F('application_status'),
						),
					),
				),

			)
		return query


class BaseStudentCourseReportDataView(FeedDataView):

	def filter_queryset(self, queryset):
		search = self.query_data.get("sSearch",'')
		queryset = queryset.filter(
			reduce(operator.and_, (
					Q(student_id__icontains = x )|
					Q(name__icontains = x)|
					Q(batch__icontains = x)|
					Q(courses_str__icontains = x)
					for x in search.split()
					)
				)) if search else queryset
		return queryset

	def get_queryset(self):
		queryset = super(BaseStudentCourseReportDataView, self).get_queryset()

		all_courses = Case(
			When(
				Q(
					Q(application__program__firstsemcourselist_requests_created_1__admit_year=F('application__admit_year')) &
					Q(application__program__firstsemcourselist_requests_created_1__active_flag=True) &
					Q(application__program__firstsemcourselist_requests_created_1__is_elective=False) 
				),
				then=F('application__program__firstsemcourselist_requests_created_1__course_id'),
			),
			When(
					Q(studentelectiveselection_1__course__course_id__isnull=False), 
					then=F('studentelectiveselection_1__course__course_id')
				),
			output_field=CharField(),
		)
		all_cources_concat = GroupConcat(all_courses, distinct=True, 
			output_field=ListCharField(base_field=CharField()))

		all_cources_concat_str= GroupConcat(all_courses, distinct=True, 
			output_field=CharField())

		queryset = queryset.exclude(Q(student_id__isnull=True) | Q(student_id='')).annotate(
			batch=F('application__admit_batch'),
			name=F('application__full_name'),
			courses=all_cources_concat,
			courses_str=all_cources_concat_str,
				)

		return queryset

class BasePgmAdmReportAjaxData(BitsFeedDataView):

	def get_queryset(self):
		query = super(BasePgmAdmReportAjaxData, self).get_queryset()
		query = query.exclude(
			Q(student_id__isnull=True) | Q(student_id='')).values('application__program','application__admit_batch',).annotate(
			adm_count=Count('pk'),
			pgm = Concat('application__program__program_name',Value(' - '),
				'application__program__program_code',Value(' ('),
				'application__program__program_type',Value(')')),
			btc = F('application__admit_batch'),
			)
		pg = int(self.kwargs.get('pg',None))
		pg_type = self.kwargs.get('pg_type',None)
		adm_btc = self.kwargs.get('adm_btc',None)
		pg_code = Program.objects.get(pk=pg).program_code if pg else None
		query = query.filter(application__program__program_code=pg_code ) if pg_code else query
		query = query.filter(application__program__program_type=pg_type ) if pg_type and not pg_type == 'n' else query
		query = query.filter(application__admit_batch=adm_btc ) if adm_btc and not adm_btc == 'n' else query

		return query.distinct()

	def get_extra_queryset(self):
		query = super(BasePgmAdmReportAjaxData, self).get_extra_queryset()
		query = query.exclude(
			Q(student_id__isnull=True) | Q(student_id='')).values('application__program','application__admit_batch',).annotate(
			adm_count=Count('pk'),
			pgm = Concat('application__program__program_name',Value(' - '),
				'application__program__program_code',Value(' ('),
				'application__program__program_type',Value(')')),
			btc = F('application__admit_batch'),
			)
		pg = int(self.kwargs.get('pg',None))
		pg_type = self.kwargs.get('pg_type',None)
		adm_btc = self.kwargs.get('adm_btc',None)
		pg_code = Program.objects.get(pk=pg).program_code if pg else None
		query = query.filter(application__program__program_code=pg_code ) if pg_code else query
		query = query.filter(application__program__program_type=pg_type ) if pg_type and not pg_type == 'n' else query
		query = query.filter(application__admit_batch=adm_btc ) if adm_btc and not adm_btc == 'n' else query

		return query.distinct()


#Base Call Bound Ajax
class BaseBoundLogAjax(FeedDataView):
	def get_queryset(self):
		to_date = self.kwargs.get('to_dt') or '00-00-0000'
		from_date = self.kwargs.get('fm_dt') or '00-00-0000'
		query = super(BaseBoundLogAjax, self).get_queryset()

		if not query.exists(): return query 

		query = query.annotate(
				called_on_date=Trunc(
					'called_on',
					'day',
					output_field=DateField(),
					tzinfo=india
				),
				app = GroupConcat(
					Case(
						When(
							Q(application__isnull=False),
							then=Concat(
								Value('App Id: '),
								'application__student_application_id', 
								Value('<br > Name: '), 
								'application__full_name',
								Value('<br > Status: '), 
								'application__application_status',
							)
						),
						default=Value(''),
						output_field=models.CharField(),
					),
					distinct=True, 
					output_field=models.CharField(),
					separator='<br > ------------------------- <br >',
				),
			)

		from_date = parse(from_date, dayfirst=True) if not from_date == '00-00-0000' else timezone.datetime.min.date()
		to_date = parse(to_date, dayfirst=True) if not to_date == '00-00-0000' else timezone.datetime.max.date()
		
		query = query.filter(
				called_on_date__gte = from_date,
				called_on_date__lte = to_date,
		)

		return query

class BaseInboundLogAjax(BaseBoundLogAjax):
	token = inbound_call_log_paging().token

	def get_queryset(self):
		queryset = super(BaseInboundLogAjax, self).get_queryset()
		program_interested = GroupConcat(
			Case(
				When(
					Q(inboundprograminterested_bound__isnull=False),
					then=Concat(
						'inboundprograminterested_bound__data_type', 
						Value(' : '), 
						'inboundprograminterested_bound__program'
					)
				),
				default=Value(''),
				output_field=models.CharField(),
			),
			distinct=True, 
			output_field=models.CharField(),
			separator='<br />'
		)

		phone = GroupConcat(
			Case(
				When(
					Q(inboundphone_bound__isnull=False),
					then=Concat(
						'inboundphone_bound__data_type', 
						Value(' : '), 
						'inboundphone_bound__phone'
					)
				),
				default=Value(''),
				output_field=models.CharField(),
			),
			distinct=True, 
			output_field=models.CharField(),
			separator='<br />'
		)

		boundquery = GroupConcat(
			Case(
				When(
					Q(inboundquery_bound__isnull=False),
					then=Concat(
						'inboundquery_bound__data_type', 
						Value(' : '), 
						'inboundquery_bound__query'
					)
				),
				default=Value(''),
				output_field=models.CharField(),
			),
			distinct=True, 
			output_field=models.CharField(),
			separator='<br />'
		)

		voc = GroupConcat(
			Case(
				When(
					Q(inboundvoc_bound__isnull=False),
					then=Concat(
						'inboundvoc_bound__data_type', 
						Value(' : '), 
						'inboundvoc_bound__content'
					)
				),
				default=Value(''),
				output_field=models.CharField(),
			),
			distinct=True, 
			output_field=models.CharField(),
			separator='<br />'
		)

		queryset = queryset.annotate(
			voc=voc, 
			query=boundquery, 
			phone=phone, 
			program_interested=program_interested,
		)

		return queryset

class BaseOutboundLogAjax(BaseBoundLogAjax):
	token = outbound_call_log_paging().token

	def get_queryset(self):
		queryset = super(BaseOutboundLogAjax, self).get_queryset()
		program_interested = GroupConcat(
			Case(
				When(
					Q(outboundprograminterested_bound__isnull=False),
					then=Concat(
						'outboundprograminterested_bound__data_type', 
						Value(' : '), 
						'outboundprograminterested_bound__program'
					)
				),
				default=Value(''),
				output_field=models.CharField(),
			),
			distinct=True, 
			output_field=models.CharField(),
			separator='<br />'
		)

		phone = GroupConcat(
			Case(
				When(
					Q(outboundphone_bound__isnull=False),
					then=Concat(
						'outboundphone_bound__data_type', 
						Value(' : '), 
						'outboundphone_bound__phone'
					)
				),
				default=Value(''),
				output_field=models.CharField(),
			),
			distinct=True, 
			output_field=models.CharField(),
			separator='<br />'
		)

		boundquery = GroupConcat(
			Case(
				When(
					Q(outboundquery_bound__isnull=False),
					then=Concat(
						'outboundquery_bound__data_type', 
						Value(' : '), 
						'outboundquery_bound__query'
					)
				),
				default=Value(''),
				output_field=models.CharField(),
			),
			distinct=True, 
			output_field=models.CharField(),
			separator='<br />'
		)

		voc = GroupConcat(
			Case(
				When(
					Q(outboundvoc_bound__isnull=False),
					then=Concat(
						'outboundvoc_bound__data_type', 
						Value(' : '), 
						'outboundvoc_bound__content'
					)
				),
				default=Value(''),
				output_field=models.CharField(),
			),
			distinct=True, 
			output_field=models.CharField(),
			separator='<br />'
		)

		queryset = queryset.annotate(
			voc=voc, 
			query=boundquery, 
			phone=phone, 
			program_interested=program_interested, 
		)
		return queryset

	