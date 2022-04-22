from django.urls import path, include
from django.conf.urls import url
from master.ajax import views

app_name = 'ajax'
urlpatterns = [
	path('exam-venue/', views.ExamVenueAjax.as_view(), name='exam-venue'),
	path('exam-venue-address/', views.ExamVenueAddressAjax.as_view(), name='exam-venue-address'),
	path('current-exam/', views.CurrentExamAjax.as_view(), name='current-exam'),
	path('exam-slot/', views.ExamSlotAjax.as_view(), name='exam-slot'),
	path('course-exam-schedule-ajax/<int:semester>/<int:exam_type>/<int:exam_slot>/', 
		views.BaseCourseExamScheduleAjax.as_view(), name='course-exam-schedule-ajax'),
	path('exam-attendance/',views.ExamAttendanceAjax.as_view(), name='exam-attendance'),

	path('hall-ticket-attendance/<int:pg>/<int:venue>/<int:loc>/<int:miss>/', 
		views.HallTicketAttendanceAjaxView.as_view(), name='hall-ticket-attendance'),
	path('hall-ticket-issue-status/', 
		views.HallTicketAttendanceIssueAjax.as_view(), name='hall-ticket-issue-status'),
	url(r'attendance-data-view/(?P<course>[\w|:]+)/(?P<venue>\d+)/(?P<loc>\d+)/$',
		views.AttendanceDataAjaxView.as_view(), name='attendance-data-view'),
	path('exam-attendance-summary-report-course-wise/',views.ExamAttendanceSummaryReportAjax.as_view(), name='exam-attendance-summary-report-course-wise'),
	path('examtype-fetch/',views.ExamtypeFetchAjax.as_view(), name='examtype-fetch'),
	path('program-fetch/',views.ProgramFetchAjax.as_view(), name='program-fetch'),
	path('update-student-photo/', views.UpdateStudentPhotoAjax.as_view(), name='update-student-photo'),
    path('photo-already-exist/', views.PhotoAlreadyExistsAjax.as_view(), name='photo-already-exist'),
    path('handle_upload_function/', views.HandleUploadFunctionAjax.as_view(), name='handle_upload_function'),
    path('hall-ticket-exception/', views.HallticketExceptionAjaxView.as_view(), name='hall-ticket-exception'),

]