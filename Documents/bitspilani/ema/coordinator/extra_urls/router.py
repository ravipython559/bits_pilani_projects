from django.urls import path
from coordinator import views
from django.conf.urls import url

app_name = 'coordinator_router'
urlpatterns = [
		path('course-exam-schedule', views.CourseExamSceduleView.as_view(),
			name = 'course-exam-schedule'),
		path('attendance-data', views.AttendanceDataView.as_view(),
			name = 'attendance-data'),
		path('stud-reg-view', views.StudentRegistrationView.as_view(),
			name='stud-reg-view'),
		path('hall-ticket-attend',views.CoordinatorHallTicketAttendanceView.as_view(),
			name='hall-ticket-attend'),
		path('student-attendance-data/', views.CoordinatorStudentAttendenceView.as_view(),
			name='student-attendance-data'),
		path('student-attendance-by-venue-by-slot-view/', views.CoordinatorStudentCountByVenueBySlotView.as_view(),
			name='student-count-by-venue-by-slot'),
		path('student-attendance-count-by-course-by-venue-view/', views.CoordinatorStudentAttendanceCountByCourseByVenueView.as_view(),
			name='student-attendance-count-by-course-by-venue'),
		path('session-wise-absence-data-view/', views.CoordinatorSessionWiseAbsenseDataView.as_view(),
			name='session-wise-absence-data'),
		url(r'hall-ticket.pdf/(?P<student_id>\w+)/(?P<sem>\d+)/$', views.CoordinatorHallTicketPDF.as_view(), 
			name='generate-hall-ticket-pdf'),
		url(r'student-photo-view/(?P<student_id>\w+)/$', views.CoordinatorStudentPhotoView.as_view(), 
			name='student-photo-view'),
]
