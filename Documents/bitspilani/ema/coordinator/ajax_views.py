from .permissions import *
from master.ajax.views import *
from master.tables import *
from .tables import *


class CourseExamScheuleAjax(EMAUserPermissionMixin, BaseCourseExamScheduleAjax):
	token = couse_exam_schedule_paging(ajax_url='coordinator:coordinator_ajax:course-exam-schedule-ajax').token

class StudentRegistrationAjaxView(EMAUserPermissionMixin, BaseStudentRegistrationAjaxView):
	token = stud_reg_view(ajax_url='coordinator:coordinator_ajax:stud-reg-view-ajax').token

class CoordinatorHTAttendanceAjaxView(EMAUserPermissionMixin,HallTicketAttendanceAjaxView):
	token = get_hallticket_issue_status_table_coordinator(ajax_url='coordinator:coordinator_ajax:halltick-attend-view-ajax').token

class CoordinatorStudentAttendanceAjax(EMAUserPermissionMixin,StudentAttendanceAjax):
	template_name = 'coordinator/inclusion/loc_student_attendance.html'

	def get_form(self, *args, **kwargs):
		cordinator_location = LocationCoordinator.objects.filter(coordinator_email_id=self.request.user.email)
		form = super().get_form(*args, **kwargs)
		try:
			form.fields['exam_venue'].queryset = form.fields['exam_venue'].queryset.filter(
				examvenueslotmap_ev__exam_venue__location__in=Subquery(cordinator_location.values('location'))).distinct()

		except Exception as e:
			pass

		return form
