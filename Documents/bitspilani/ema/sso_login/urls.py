from django.urls import path
from . import views

app_name = 'sso_login'
urlpatterns = [
	path('', views.EMARemoteRedirectView.as_view(), name='redirect'),
]