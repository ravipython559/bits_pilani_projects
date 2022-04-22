from django.conf.urls import url
from . import views

urlpatterns = [
	url(r"studentapplication/(?P<pg_code>\w+)/$",
		views.ApplicationForm.as_view(), name="student-application"),
	url(r"studentapplicationEdit/$", views.ApplicationEditForm.as_view(),
		name="student-application-edit"),
	url(r"progress/$", views.ViewData.as_view(),name="progress"),
	url(r"student-application-view/$", 
		views.ApplicationFormView.as_view(),name="student-application-view"),
	url(r"rev-or-adm-application-view/(?P<pk>\d+)/$", 
		views.ApplicationAdminView.as_view(),name="student-rev-or-adm-application-view"),
	url(r"rev-or-adm-application-view/(?P<alert_status>\w+)/(?P<pk>\d+)/$", 
		views.ApplicationAdminView.as_view(),name="student-alert-rev-or-adm-application-view"),

]