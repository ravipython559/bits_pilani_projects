from django.conf.urls import include, url
from bits_rest.viewsets.ezcred import views


urlpatterns = [
	url(r'^ezcred-application/', views.ApplicationCreateView.as_view(), name='application'),
	url(r'^ezcred-api/(?P<pk>\d+)/', views.Ezcred.as_view(), name='api'),
	url(r'^ezcred-api_call/', views.apicall, name='apicall'),
	url(r'^ezcred-callback/', views.CallBackView.as_view(), name='callback'),
	url(r'^ezcred-landing-page/(?P<pk>\d+)/', views.EzcredRedirectView.as_view(), name='landing'),
	url(r'^ezcred-cancell/', views.ezcredcancell, name='ezcred-cancell'),

]
