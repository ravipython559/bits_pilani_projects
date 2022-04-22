from django.shortcuts import render
from django.views.generic import  TemplateView
from django.db.models import F, Value, OuterRef, Subquery
from .forms import cordinator_attendence_form
from master.views import *
from master.models import *
from .permissions import *
from .tables import *


class Home(EMAUserPermissionMixin, TemplateView):
	template_name = 'coordinator/home.html'

class CourseExamSceduleView(EMAUserPermissionMixin, BaseCourseExamScheduleView):
	ajax_url = 'coordinator:coordinator_ajax:course-exam-schedule-ajax'

class AttendanceDataView(EMAUserPermissionMixin, BaseAttendanceDataView):

	def get_form_class(self):
		return cordinator_attendence_form(self.request.user)

class StudentRegistrationView(EMAUserPermissionMixin,BaseStudentRegistrationView):
	template_name = 'coordinator/stud-reg-view.html'
	ajax_url = 'coordinator:coordinator_ajax:stud-reg-view-ajax'

class CoordinatorHallTicketAttendanceView(EMAUserPermissionMixin, BaseHallTicketAttendanceView):
	template_name = 'coordinator/halltick-attend-view.html'
	ajax_url = 'coordinator:coordinator_ajax:halltick-attend-view-ajax'

	def get_table(self,**kwargs):
		return get_hallticket_issue_status_table_coordinator(**kwargs)(get_attenlist_halltcktissue(**kwargs))

class CoordinatorStudentAttendenceView(EMAUserPermissionMixin, BaseStudentAttendenceView):
	template_name = 'coordinator/student-attend-view.html'

class CoordinatorHallTicketPDF(EMAUserPermissionMixin,BaseHallTicketPDF):
	pass

class CoordinatorStudentPhotoView(EMAUserPermissionMixin,BaseStudentPhotoView):
	pass

class CoordinatorStudentCountByVenueBySlotView(EMAUserPermissionMixin,BaseStudentCountByVenueBySlotView):
	pass

class CoordinatorStudentAttendanceCountByCourseByVenueView(EMAUserPermissionMixin,BaseStudentAttendanceCountByCourseByVenueView):
	pass

class CoordinatorSessionWiseAbsenseDataView(EMAUserPermissionMixin, BaseSessionWiseAbsenseDataView):
	pass