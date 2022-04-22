from django.urls import path
from administrator import ajax_views

app_name = 'admin_ajax'
urlpatterns = [
	path('stud-reg-view-ajax/<str:pg_code>/<int:sem>/',
		ajax_views.StudentRegistrationAjaxView.as_view(),
		name='stud-reg-view-ajax'),
	path('halltick-attend-view-ajax', ajax_views.HTAttendanceAjaxView.as_view(),
		name ='halltick-attend-view-ajax'),
	path('api-calls/', ajax_views.CallApis.as_view(), name='api-calls'),
	path('student-attendance/', ajax_views.AdminStudentAttendanceAjax.as_view(), name='student-attendance'),
	path('data-sync-log-ajax/',ajax_views.AdminSyncLogDataAjaxView.as_view(), name='data-sync-log-ajax'),
	path('photo-view-admin/', ajax_views.StudentPhotoView.as_view(), name='photo-view-admin'),
]
