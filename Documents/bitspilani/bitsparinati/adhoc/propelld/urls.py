from django.conf.urls import include, url
from . import views


urlpatterns = [
	url(r'^propelld-application/(?P<pk>\d+)/', views.ApplicationCreateView.as_view(), name='application'),
	url(r'^propelld-api/(?P<pk>\d+)/', views.Propelld.as_view(), name='api'),
	url(r'^propelld-api_call/', views.apicall, name='apicall'),
	url(r'^propelld-callback/', views.CallBackView.as_view(), name='callback'),
	# url(r'^propelld-landing-page/', views.PropelldRedirectView.as_view(), name='landing'),
]