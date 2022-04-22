from django.urls import path
from administrator import csv_views

app_name = 'admin_csv'
urlpatterns = [
	path('stud-reg-list-csv/',csv_views.StudentRegExportCSV.as_view(), 
		name='stud-reg-list-csv'),
]