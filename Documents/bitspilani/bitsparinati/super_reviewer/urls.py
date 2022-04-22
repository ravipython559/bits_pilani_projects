from django.conf.urls import url, include
from django.contrib import admin
from . import views

urlpatterns = [
	url(r'^home/$',views.sr_home,name='sr-home'),
	url(r'sr-program-change/$',views.sr_program_change,name='sr-program-change'),
	url(r'sr-offer-change/$',views.sr_offer_change,name='sr-offer-change'),
	url(r'sr-review-application-details/(?P<application_id>\d+)/$',
		views.ApplicantDetail.as_view(),
		name='sr-review-application-details'),
]