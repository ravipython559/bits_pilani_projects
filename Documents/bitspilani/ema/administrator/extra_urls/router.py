from django.urls import path
from django.conf.urls import url
from administrator import views

app_name = 'admin_router'
urlpatterns = [	
		path('sync-lms-api/', views.ApplicationCenterSyncView.as_view(),
			name='sync-lms-api'),
		path('bulk-activate-inactivate/', views.BulkActivateInactivate.as_view(), name='bulk-activate-inactivate'),
		path('stud-reg-view/', views.StudentRegistrationView.as_view(),
			name='stud-reg-view'),
		path('attendance-data/', views.AttendenceDataView.as_view(),
			name='attendance-data'),
		path('student-attendance-data/', views.StudentAttendenceView.as_view(),
			name='student-attendance-data'),
		path('exam-attendance-summary-report-view/', views.ExamAttendenceSummaryReportView.as_view(),
			name='exam-attendance-summary-report'),
		path('student-attendance-by-venue-by-slot-view/', views.StudentCountByVenueBySlotView.as_view(),
			name='student-count-by-venue-by-slot'),
		path('student-attendance-count-by-course-by-venue-view/', views.StudentAttendanceCountByCourseByVenueView.as_view(),
			name='student-attendance-count-by-course-by-venue'),
		path('session-wise-absence-data-view/', views.SessionWiseAbsenseDataView.as_view(),
			name='session-wise-absence-data'),
		path('hall-ticket-attend',views.HallTicketAttendanceView.as_view(),
			name='hall-ticket-attend'),
		url(r'hall-ticket.pdf/(?P<student_id>\w+)/(?P<sem>\d+)/$', views.HallTicketPDF.as_view(),
			name='generate-hall-ticket-pdf'),
		url(r'student-photo-view/(?P<student_id>\w+)/$', views.StudentPhotoView.as_view(), 
			name='student-photo-view'),
		path('students-without-hall-ticket', views.StudentsWithoutHallTicket.as_view(),
			 name='students-without-hall-ticket'),
		url(r'sync-sdms-email-and-phone/', views.SyncSDMSEmailandPhone.as_view(), name='sync-sdms-email-and-phone'),
		url(r'sync-sdms-email-and-phone/$', views.SyncSDMSEmailandPhone.as_view(), name='sync-sdms-email-and-phone'),
		url(r'sync-qpm-examtype/$', views.SyncQPMExamtype.as_view(), name='sync-qpm-examtype'),
		url(r'sync-qpm-batch/$', views.SyncQPMBatch.as_view(), name='sync-qpm-batch'),
		url(r'sync-qpm-semester/$', views.SyncQPMSemester.as_view(), name='sync-qpm-semester'),
		url(r'sync-qpm-examslot/$', views.SyncQPMExamSlot.as_view(), name='sync-qpm-examslot'),
]
