from django.urls import path
from . import views, views_ajax

app_name = 'student'
urlpatterns = [
	path('', views.Home.as_view(), name='index'),
	path('<int/semester>/', views.Home.as_view(), name='index_ajax'),
	path('hall-ticket/<int:semester>/', views.HallTicketView.as_view(), name='hall-ticket'),
	path('hall-ticket-preview/<int:semester>/', 
		views.HallTicketView.as_view(template_name='student/preview_hall_ticket_non_editable.html',), 
		name='hall-ticket-preview'),
	path('hall-ticket/location/', views_ajax.HallTicketLocationAjaxFormView.as_view(), name='hall-ticket-location'),
	path('hall-ticket/exam-venue/', views_ajax.HallTicketExamVenueAjaxFormView.as_view(), name='hall-ticket-exam-venue'),
	# path('student-hall-ticket.pdf/<int:exam_type>/', views.StudentHallTicketPDF.as_view(), name='student-hall-ticket.pdf'),
	path('student-hall-ticket.pdf/<int:sem>/', views.StudentHallTicketPDF.as_view(), name='student-hall-ticket.pdf'),
	path('photo-update/<int:pk>', views.PhotoUpdateView.as_view(), name='photo-update'),
	path('hall-ticket/exam-slot/', views_ajax.HallTicketExamSlotAjaxFormView.as_view(), name='hall-ticket-exam-slot'),
	path('photo-view/<int:pk>/', views.StudentPhotoView.as_view(), name='photo-view'),
	path('online-exam-atandance-status',views.onlineexamatandancestatus.as_view(),name='online-exam-atandance-status'),
	path('exam-schedule',views.examschedule.as_view(),name='exam-schedule')
]