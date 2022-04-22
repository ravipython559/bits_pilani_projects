from .permissions import *
from master.ajax.views import *
from master.tables import *
from master.utils.storage import document_extract_file
import magic
from django.http import HttpResponse



class StudentRegistrationAjaxView(EMAUserPermissionMixin, BaseStudentRegistrationAjaxView):
	token = stud_reg_view(ajax_url='administrator:admin_ajax:stud-reg-view-ajax').token

class HTAttendanceAjaxView(EMAUserPermissionMixin,BaseHallTicketAttendanceAjaxView):
	token = get_hallticket_issue_status_table(ajax_url='adminstrator:admin_ajax:halltick-attend-view-ajax').token

class CallApis(FormView):
	pass

class AdminStudentAttendanceAjax(EMAUserPermissionMixin,StudentAttendanceAjax):
	pass

class AdminSyncLogDataAjaxView(EMAUserPermissionMixin,BaseSyncLogDataAjaxView):
	token = APPLCenterSyncLogTable().token

class StudentPhotoView(EMAUserPermissionMixin, View):
	def get(self, request, *args, **kwargs):
		student = Student.objects.get(student_id=request.GET.get("studentid"))
		if student.photo.name:
			file = document_extract_file(student)
			mime_type = magic.from_buffer(file.getvalue(), mime=True)
			return HttpResponse(file.getvalue(), content_type=mime_type)