from django.urls import path
from coordinator import ajax_views

app_name = 'coordinator_ajax'
urlpatterns = [
	path('course-exam-schedule-ajax/<int:semester>/<int:exam_slot>/<int:exam_type>/',
		ajax_views.CourseExamScheuleAjax.as_view(),
		name = 'course-exam-schedule-ajax'),
	path('stud-reg-view-ajax/<str:pg_code>/<int:sem>/',
		ajax_views.StudentRegistrationAjaxView.as_view(),
		name='stud-reg-view-ajax'),
	path('halltick-attend-view-ajax/<int:pg>/<int:venue>/<int:loc>/<int:miss>/', ajax_views.CoordinatorHTAttendanceAjaxView.as_view(),
		name ='halltick-attend-view-ajax'),
	path('student-attendance/', ajax_views.CoordinatorStudentAttendanceAjax.as_view(), name='student-attendance'),

]