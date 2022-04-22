from django.urls import path, include
from . import views

app_name = 'master'
urlpatterns = [
path('ajax/', include('master.ajax.urls')),
path('unauthorised/', views.unauthorised.as_view(),name='unauthorised'),
]
