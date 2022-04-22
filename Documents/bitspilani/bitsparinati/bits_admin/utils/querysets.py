from django.db.models.functions import *
from django.db.models import *
from bits_admin.models import EduvanzApplicationArchived
from bits_rest.models import EduvanzApplication
from django_mysql.models import GroupConcat
import operator

def get_eduv_queryset(model):

	eduv_dict = {EduvanzApplication:(lambda : Case(
					When(Q(application__candidateselection_requests_created_5550__new_application_id__isnull=False,
						application__candidateselection_requests_created_5550__application__pk=F('pk')
						), 
						then=F('application__candidateselection_requests_created_5550__new_application_id')),
					default=F('application__student_application_id'),
					output_field=CharField(),
					),
					'application__candidateselection_requests_created_5550__student_id',),
				EduvanzApplicationArchived:(lambda : Case(
			When(Q(application__candidateselectionarchived_1__new_application_id__isnull=False,
				application__candidateselectionarchived_1__application__pk=F('pk')
				), 
				then=F('application__candidateselectionarchived_1__new_application_id')),
			default=F('application__student_application_id'),
			output_field=CharField(),
			),
			'application__candidateselectionarchived_1__student_id',)} 


	app_id_str = GroupConcat(eduv_dict[model][0](),
			distinct=True, 
			output_field=CharField()
		)

	return model.objects.annotate(
			sca_id=F('application__pk'),
			app_id = app_id_str,
			student_id=F(eduv_dict[model][1]),
			full_name=F('application__full_name'),
			pg_name = Concat('application__program__program_code',Value(' - '),
					'application__program__program_name',Value(' ('),
					'application__program__program_type',Value(')')
					),
			app_status=F('application__application_status'),
			admit_batch=F('application__admit_batch'),
			status_name=Case(*[When(status_code=k, then=Value(v)) for k,v in EduvanzApplication.EDUVANZ_CHOICES],
					output_field=CharField()),
			).order_by('-created_on')


def eduv_search(query, search):
	return query.filter(
		reduce(operator.and_, 
			(
				Q(application__student_application_id__icontains = item)|
				Q(application__admit_batch__icontains = item)|
				Q(student_id__icontains = item)|
				Q(full_name__icontains = item)|
				Q(pg_name__icontains = item)|
				Q(app_status__icontains = item)|
				Q(order_id__icontains = item)|
				Q(status_name__icontains = item)|
				Q(lead_id__icontains = item)
				for item in search.split()
			)
		) 
	) if search else query



def deffered_doc_search(query, search):
	return query.filter(
		reduce(operator.and_, 
			(
				Q(student_application_id__icontains = item)|
				Q(admit_batch__icontains = item)|
				Q(candidateselection_requests_created_5550__student_id = item)|
				Q(full_name__icontains = item)|
				Q(program__program_name__icontains = item)|
				Q(current_location__location_name__icontains = item)|
				Q(application_status__icontains = item)
				for item in search.split()
			)
		) 
	) if search else query

