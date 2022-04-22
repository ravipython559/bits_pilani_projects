from django.views.generic import View,FormView,TemplateView,UpdateView
from faculty.views import Base_fac_Home,Base_fac_qp_update,Base_fac_qp_submision_status
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.db.models import (Max, Q, Case, When, F, Value, TextField, CharField, IntegerField, BooleanField)
from django.db.models.functions import Concat
from table.views import FeedDataView
from administrator.tasks import *
from .permissions import *
from .forms import *
from .tables import *
import ast
from master.views import UserFileViewDownload

@method_decorator([never_cache], name='dispatch')
class QPSubmissionStatusView(QPMUserPermissionMixin, FormView):
	template_name = 'coordinator/view_qp_submission_status.html'
	form_class = QPSubmissionCoordinatorForm

	def get_initial(self):
		self.initial['semester_name'] = self.request.GET.get('semester_name')
		self.initial['submission_status'] = self.request.GET.get('submission_status')
		self.initial['exam_type_name'] = self.request.GET.get('exam_type_name')
		self.initial['exam_slot'] = self.request.GET.get('exam_slot')
		return self.initial

	def get_form_kwargs(self):
		kwargs = super(QPSubmissionStatusView, self).get_form_kwargs()
		kwargs['request'] = self.request
		return kwargs

	def get_coord_submission_list(self, data):
		qpsub = QpSubmission.objects.filter(active_flag=1).order_by('-last_submitted_datetime')
		qpsubmissions = qpsub.filter(Q(coordinator_email_id_1 = self.request.user.email) | 
									Q(coordinator_email_id_2 = self.request.user.email)).annotate(semester_name=F('semester__semester_name'),
																								  batch_name=F('batch__batch_name'),
																								  exam_slot_name= F('exam_slot__slot_name'),
																								  course_info=Concat('course_code', Value(' - '), 'course_name'),
																								  exam_type_info=F('exam_type__exam_type'))
		if data.get('semester_name'):
			qpsubmissions = qpsubmissions.filter(semester__semester_name=data.get('semester_name'))
		if data.get('submission_status'):
			if data.get('submission_status') == 'pendingreview':
				qpsubmissions = qpsubmissions.filter(Q(Q(qp_path__isnull=False,last_submitted_datetime__isnull=False)|
														Q(alternate_qp_path__isnull=False,alternate_qp_submit_datetime__isnull=False)) & 
														Q(acceptance_flag=False) & Q(acceptance_flag=False) & Q(rejected_flag=False))
			if data.get('submission_status') == 'sentforresubmission':
				qpsubmissions = qpsubmissions.filter(Q(Q(qp_path__isnull=False,last_submitted_datetime__isnull=False)|
														Q(alternate_qp_path__isnull=False,alternate_qp_submit_datetime__isnull=False)) & Q(rejected_flag=True))
			if data.get('submission_status') == 'accepted':
				qpsubmissions = qpsubmissions.filter(Q(Q(qp_path__isnull=False,last_submitted_datetime__isnull=False)|
														Q(alternate_qp_path__isnull=False,alternate_qp_submit_datetime__isnull=False)) & Q(acceptance_flag=True) & Q(last_download_datetime__isnull=True))
			if data.get('submission_status') == 'acceptedanddownloaded':
				qpsubmissions = qpsubmissions.filter(Q(Q(qp_path__isnull=False,last_submitted_datetime__isnull=False)|
														Q(alternate_qp_path__isnull=False,alternate_qp_submit_datetime__isnull=False)) & Q(acceptance_flag=True) & Q(last_download_datetime__isnull=False))
			if data.get('submission_status') == 'pendingsubmission':
				qpsubmissions = qpsubmissions.filter(Q(Q(qp_path__isnull=True)| Q(qp_path__exact=''),Q(alternate_qp_path__isnull=True)| Q(alternate_qp_path__exact='')))

		if data.get('exam_type_name'):
			qpsubmissions = qpsubmissions.filter(exam_type__exam_type=data.get('exam_type_name'))
		if data.get('exam_slot'):
			qpsubmissions = qpsubmissions.filter(exam_slot=data.get('exam_slot'))
		return qpsubmissions

	def get_table(self, data):
		return get_coord_submission_status_table(data)(self.get_coord_submission_list(data))

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		table = self.get_table(self.request.GET)
		context['table'] = table
		if 'report_async' in self.request.GET:
			if 'async_email' == self.request.GET['report_async']:
				qpsub = QpSubmission.objects.filter(active_flag=1)
				qpsubmissions = qpsub.filter(Q(coordinator_email_id_1 = self.request.user.email) | 
									Q(coordinator_email_id_2 = self.request.user.email)).annotate(semester_name=F('semester__semester_name'),
																																	batch_name=F('batch__batch_name'), 
																																	exam_slot_name= F('exam_slot__slot_name'), 
																																	course_info=Concat('course_code', Value(' - '), 'course_name'), 
																																	exam_type_info=F('exam_type__exam_type'))
				data = self.request.GET
				if data.get('semester_name'):
					qpsubmissions = qpsubmissions.filter(semester__semester_name=data.get('semester_name'))
				if data.get('submission_status'):
					if data.get('submission_status') == 'pendingreview':
						qpsubmissions = qpsubmissions.filter(Q(Q(qp_path__isnull=False,last_submitted_datetime__isnull=False)|
																Q(alternate_qp_path__isnull=False,alternate_qp_submit_datetime__isnull=False)) & 
																Q(acceptance_flag=False) & Q(acceptance_flag=False) & Q(rejected_flag=False))
					if data.get('submission_status') == 'sentforresubmission':
						qpsubmissions = qpsubmissions.filter(Q(Q(qp_path__isnull=False,last_submitted_datetime__isnull=False)|
																Q(alternate_qp_path__isnull=False,alternate_qp_submit_datetime__isnull=False)) & Q(rejected_flag=True))
					if data.get('submission_status') == 'accepted':
						qpsubmissions = qpsubmissions.filter(Q(Q(qp_path__isnull=False,last_submitted_datetime__isnull=False)|
																Q(alternate_qp_path__isnull=False,alternate_qp_submit_datetime__isnull=False)) & Q(acceptance_flag=True) & Q(last_download_datetime__isnull=True))
					if data.get('submission_status') == 'acceptedanddownloaded':
						qpsubmissions = qpsubmissions.filter(Q(Q(qp_path__isnull=False,last_submitted_datetime__isnull=False)|
																Q(alternate_qp_path__isnull=False,alternate_qp_submit_datetime__isnull=False)) & Q(acceptance_flag=True) & Q(last_download_datetime__isnull=False))
					if data.get('submission_status') == 'pendingsubmission':
						qpsubmissions = qpsubmissions.filter(Q(Q(qp_path__isnull=True)| Q(qp_path__exact=''),Q(alternate_qp_path__isnull=True)| Q(alternate_qp_path__exact='')))

				if data.get('exam_type_name'):
					qpsubmissions = qpsubmissions.filter(exam_type__exam_type=data.get('exam_type_name'))
				if data.get('exam_slot'):
					qpsubmissions = qpsubmissions.filter(exam_slot=data.get('exam_slot'))

				qpsubmissions = qpsubmissions.filter(Q(Q(qp_path__isnull=True)| Q(qp_path__exact=''),Q(alternate_qp_path__isnull=True)| Q(alternate_qp_path__exact='')) | Q(rejected_flag=1))
				faculty_email_ids = qpsubmissions.values_list('faculty_email_id','email_access_id_1','email_access_id_2')
				if faculty_email_ids:
					job = qp_email_send_async.delay(faculty_email_ids, qpsubmissions)
		return context

class QPSubmissionStatusAjaxView(QPMUserPermissionMixin,FeedDataView):
	token = get_coord_submission_status_table().token

	def get_queryset(self):
		qpsub = QpSubmission.objects.filter(active_flag=1).order_by('-last_submitted_datetime')
		qpsubmissions = qpsub.filter(Q(coordinator_email_id_1 = self.request.user.email) | 
									Q(coordinator_email_id_2 = self.request.user.email)).annotate(semester_name=F('semester__semester_name'),
																																	batch_name=F('batch__batch_name'), 
																																	exam_slot_name= F('exam_slot__slot_name'), 
																																	course_info=Concat('course_code', Value(' - '), 'course_name'), 
																																	exam_type_info=F('exam_type__exam_type'))
		if self.kwargs.get('data') != 'n':
			data = ast.literal_eval(self.kwargs.get('data'))
			if data.get('semester_name'):
				qpsubmissions = qpsubmissions.filter(semester__semester_name=data.get('semester_name'))
			if data.get('submission_status'):
				if data.get('submission_status') == 'pendingreview':
					qpsubmissions = qpsubmissions.filter(Q(Q(qp_path__isnull=False,last_submitted_datetime__isnull=False)|
															Q(alternate_qp_path__isnull=False,alternate_qp_submit_datetime__isnull=False)) & 
															Q(acceptance_flag=False) & Q(acceptance_flag=False) & Q(rejected_flag=False))
				if data.get('submission_status') == 'sentforresubmission':
					qpsubmissions = qpsubmissions.filter(Q(Q(qp_path__isnull=False,last_submitted_datetime__isnull=False)|
															Q(alternate_qp_path__isnull=False,alternate_qp_submit_datetime__isnull=False)) & Q(rejected_flag=True))
				if data.get('submission_status') == 'accepted':
					qpsubmissions = qpsubmissions.filter(Q(Q(qp_path__isnull=False,last_submitted_datetime__isnull=False)|
															Q(alternate_qp_path__isnull=False,alternate_qp_submit_datetime__isnull=False)) & Q(acceptance_flag=True) & Q(last_download_datetime__isnull=True))
				if data.get('submission_status') == 'acceptedanddownloaded':
					qpsubmissions = qpsubmissions.filter(Q(Q(qp_path__isnull=False,last_submitted_datetime__isnull=False)|
															Q(alternate_qp_path__isnull=False,alternate_qp_submit_datetime__isnull=False)) & Q(acceptance_flag=True) & Q(last_download_datetime__isnull=False))
				if data.get('submission_status') == 'pendingsubmission':
					qpsubmissions = qpsubmissions.filter(Q(Q(qp_path__isnull=True)| Q(qp_path__exact=''),Q(alternate_qp_path__isnull=True)| Q(alternate_qp_path__exact='')))

			if data.get('exam_type_name'):
				qpsubmissions = qpsubmissions.filter(exam_type__exam_type=data.get('exam_type_name'))
			if data.get('exam_slot'):
				qpsubmissions = qpsubmissions.filter(exam_slot=data.get('exam_slot'))
		return qpsubmissions


class Home(QPMUserPermissionMixin,Base_fac_Home):
	# template_name = 'coordinator/cor_home.html'
	pass

class qp_update(QPMUserPermissionMixin,Base_fac_qp_update):
	#template_name = 'coordinator/cor_Update_QP.html'
	pass

class qp_submision_status(QPMUserPermissionMixin,Base_fac_qp_submision_status):
	# template_name = 'coordinator/cor_view_qp_submission_status.html'
	pass

class coordinatorUserFileViewDownload(UserFileViewDownload):
	def get_application_document(self, request, pk):
		file = QpSubmission.objects.get(pk=pk)
		if self.request.user.remoteuser.user_type.user_role in ['CO-ORDINATOR','FACULTY','ON-FAC','OF-FAC', 'G-FAC']:
			if file:
				return file
			else:
				return None
