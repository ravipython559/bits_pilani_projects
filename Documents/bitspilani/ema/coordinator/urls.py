from django.urls import path, include
from . import views

app_name = 'coordinator'
urlpatterns = [
	path('home/', views.Home.as_view(), name='index'),
	path('views/', include('coordinator.extra_urls.router')),
	path('ajax/', include('coordinator.extra_urls.ajax')),
	path('csv/', include('coordinator.extra_urls.csv')),
	]
