from django.conf.urls import url, include
from django.contrib import admin
from . import views,tables_ajax

urlpatterns = [
	url(r'^salesforce-data-retry/$',
        views.FailedTaskView.as_view(),
        name='salesforce-data-retry'),
	url(r'^applicant-data-transfer-log/$',
		views.ApplicantDataTransferLogView.as_view(),
		name='applicant-data-transfer-log'),
	url(r'^salesforce-data-ajax/(?P<status>[\w\-]+)/$',tables_ajax.SFDataLogAjaxView.as_view(),
		name='salesforce-data-ajax'),
	url(ur'^filedownload/(?P<pk>\d+)/(?P<reference_id>.*)/$', views.file_download, name='file_download'),
	url(r'^specific-program-summary-data/$', views.SpecificProgramReportView.as_view(), name='specific_report'),
	url(r'^specific-program-data-ajax/(?P<program>[\w\ \-]+)/$', tables_ajax.SpecificSummaryDataAjaxView.as_view(), name='specific_report_ajax'),
	url(r'^salesforce-log-del-report/$',views.SaleForceLogReport.as_view(),name='salesforce-log-del-report'),
]