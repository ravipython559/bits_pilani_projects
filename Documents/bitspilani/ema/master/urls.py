from django.urls import path, include
from . import views

app_name = 'master'
urlpatterns = [
	path('ajax/', include('master.ajax.urls')),
	path('csv/', include('master.csv.urls')),
	
]