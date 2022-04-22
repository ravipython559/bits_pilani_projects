from django.urls import path,include
from . import views

app_name = 'administrator'
urlpatterns = [
		path('views/', include('administrator.extra_urls.router')),
		path('ajax/', include('administrator.extra_urls.ajax')),
		path('csv/', include('administrator.extra_urls.csv')),
]