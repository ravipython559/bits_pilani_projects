from django.conf.urls import include, url
from bits_rest.viewsets.propelld import views


urlpatterns = [
	url(r'^propelld-application/', views.ApplicationCreateView.as_view(), name='application'),
	url(r'^propelld-api/(?P<pk>\d+)/', views.Propelld.as_view(), name='api'),
	url(r'^propelld-api_call/', views.apicall, name='apicall'),
	url(r'^propelld-callback/', views.CallBackView.as_view(), name='callback'),
	url(r'^propelld-landing-page/', views.PropelldRedirectView.as_view(), name='landing'),
	# url(r'^ezcred-cancell/', views.ezcredcancell, name='ezcred-cancell'),

]
