from django.urls import path, include
from master.csv import views

app_name = 'csv'
urlpatterns = [
	path('hall-ticket-attendance/<int:pg>/<int:venue>/<int:loc>/<int:miss>/', 
		views.CSVHallTicketAttendanceAjaxView.as_view(), name='hall-ticket-attendance'),
]