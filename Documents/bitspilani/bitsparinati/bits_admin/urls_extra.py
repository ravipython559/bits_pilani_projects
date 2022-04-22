from django.conf.urls import url, include
from . import views_admin, views_app_exp,views_extra,dynamic_views

urlpatterns = [
    url(r'^get-program-ajax', views_extra.get_program1,name='get-prog'),

	url(r'^upload-manual-payments/$', views_admin.upload_manual_payments,
		name='upload-manual-payments-home'),
	url(r'^upload-gateway-payments/$', views_admin.upload_gateway_payments,
		name='upload-gateway-payments-home'),

	url(r'^upload-manual-payments/(?P<alert_status>\w+)/$', views_admin.upload_manual_payments,
		name='upload-manual-payments'),
	url(r'^upload-gateway-payments/(?P<alert_status>\w+)/$', views_admin.upload_gateway_payments,
		name='upload-gateway-payments'),

	url(r'^preview-manual-payments/(?P<file_name>\w+)/(?P<csv_file_name>[\w\.\-\W]+)/$',
	 	views_admin.preview_manual_payments,
		name='preview-manual-payments'),
	url(r'^preview-gateway-payments/(?P<file_name>\w+)/(?P<csv_file_name>[\w\.\-\W]+)/$', 
		views_admin.preview_gateway_payments,
		name='preview-gateway-payments'),

	url(r'^hist-manual-payments-ajax/(?P<st>[\w\-\s\.\,]+)/(?P<fm_dt>[\d\-\:\s]+)/(?P<to_dt>[\d\-\:\s]+)/$',
		views_admin.HMPView.as_view(),name='hist-manual-payments-ajax'),
	url(r'^hist-gateway-payments-ajax/(?P<st>[\w\-\s\.\,]+)/(?P<fm_dt>[\d\-\:\s]+)/(?P<to_dt>[\d\-\:\s]+)/$',
		views_admin.HGPView.as_view(),name='hist-gateway-payments-ajax'),

	url(r'^hist-manual-payments/$', views_admin.hist_manual_payments,
		name='hist-manual-payments-home'),
	url(r'^hist-gateway-payments/$', views_admin.hist_gateway_payments,
		name='hist-gateway-payments-home'),

	url(r'^hist-manual-payments/(?P<alert_status>[a-z]+)/$', views_admin.hist_manual_payments,
		name='hist-manual-payments'),
	url(r'^hist-gateway-payments/(?P<alert_status>\w+)/$', views_admin.hist_gateway_payments,
		name='hist-gateway-payments'),

	url(r'^hist-manual-payments-csv/$', views_admin.csv_hist_manual_payments,
		name='hmp-csv'),
	url(r'^hist-gateway-payments-csv/$', views_admin.csv_hist_gateway_payments,
		name='hgp-csv'),

	url(r'^application-exception/$', views_app_exp.ApplicationExceptionView.as_view(),
		name='app-exp'),
	url(r'^application-exception-ajax/$',
		views_app_exp.AEView.as_view(),name='app-exp-ajax'),

	url(r'^deferred-docs-app/$',
		views_extra.DefDocsAppData.as_view(),name='deferred-docs-app'),
	url(r'^deferred-docs-app-ajax/(?P<pg>\d+)/(?P<st>[\w\-\s\.\,]+)/(?P<adm_bat>[\w\-\s]+)$',
		views_extra.DefDocsAppAjaxData.as_view(), name='def-doc-ajax'),

	url(r'^view-elective-selections/$',
		views_extra.ElectiveSelectionsAppData.as_view(),name='view-elective-selections'),
	url(r'^view-elective-selections-ajax/(?P<pg>\d+)$',
		views_extra.ElectiveSelectionsAppAjaxData.as_view(), name='view-elective-selections-ajax'),

	url(r'^emi-report/$',
		views_extra.EMIReportAppData.as_view(),name='emi-report'),
	url(r'^emi-report-ajax/(?P<pg>\d+)/(?P<b_id>[\d\-\s]+)/(?P<st>[\w\-\s\.\,]+)/(?P<p_type>[\w\-\s\.\,]+)/$',
		views_extra.EMIReportAppAjaxData.as_view(), name='emi-report-ajax'),

	url(r'^deferred-docs-sub/$',
		views_extra.DefDocsSubData.as_view(),name='deferred-docs-sub'),
	url(r'^deferred-docs-sub-ajax/(?P<pg>\d+)/(?P<st>[\w\-\s\.\,]+)/(?P<adm_bat>[\w\-\s]+)$',
		views_extra.DefDocsSubAjaxData.as_view(), name='def-doc-sub-ajax'),

	url(r'^adhoc-report/$',
		views_extra.AdhocReportAppData.as_view(),name='adhoc-report'),
	url(r'^adhoc-report-ajax/$',
		views_extra.AjaxAdhocReport.as_view(), name='adhoc-report-ajax'),

	url(r'^pre-sel-rej-app/$',
		views_extra.PreSelAppData.as_view(),name='pre-sel-rej-app'),
	url(r'^pre-sel-rej-app-ajax/(?P<pg>\d+)/(?P<loc>\d+)$',
		views_extra.PreSelAppAjaxData.as_view(), name='pre-sel-rej-app-ajax'),
	url(r'^program-admissions-report/$',
		views_extra.ProgramAdmissionsReport.as_view(), name='program-admissions-report'),
	url(r'^program-admissions-report-ajax/(?P<pg>\d+)/(?P<pg_type>[\w\-\s\.\,]+)/(?P<adm_btc>[\w\-\s]+)$',
		views_extra.ProgramAdmissionsReportAjax.as_view(), name='program-admissions-report-ajax'
	 ),
	url(r'^get-prog-arch-ajax', views_extra.get_program_arch,name='get-prog-arch'),
	url(r'^emi-report-eduv/$',
		views_extra.EMIReportEduvAppData.as_view(),name='emi-report-eduv'),
	url(r'^emi-report-eduv-ajax/(?P<pg>\d+)/(?P<b_id>[\d\-\s]+)/(?P<st>[\w\-\s\.\,]+)/(?P<p_type>[\w\-\s\.\,]+)/$',
		views_extra.EMIReportEduvAppAjaxData.as_view(), name='emi-report-eduv-ajax'),

	url(r'^adhoc-eduv-report/$',
		views_extra.AdhocReportEduvAppData.as_view(),name='adhoc-eduv-report'),
	url(r'^adhoc-eduv-report-ajax/$',
		views_extra.AjaxAdhocReportEduv.as_view(), name='adhoc-eduv-report-ajax'),
	url(r'^emi-report-ezcred/$',
		views_extra.EMIReportEzcredAppData.as_view(),name='emi-report-ezcred'),
	url(r'^emi-report-ezcred-ajax/(?P<pg>\d+)/(?P<b_id>[\d\-\s]+)/(?P<st>[\w\-\s\.\,]+)/(?P<p_type>[\w\-\s\.\,]+)/$',
		views_extra.EMIReportEzcredAppAjaxData.as_view(), name='emi-report-ezcred-ajax'),

	url(r'^emi-report-propelld/$',
		views_extra.EMIReportPropelldAppData.as_view(),name='emi-report-propelld'),
	url(r'^emi-report-propelld-ajax/(?P<pg>\d+)/(?P<b_id>[\d\-\s]+)/(?P<st>[\w\-\s\.\,]+)/(?P<p_type>[\w\-\s\.\,]+)/$',
		views_extra.EMIReportPropelldAppAjaxData.as_view(), name='emi-report-propelld-ajax'),

	url(r'^adhoc-propelld-report/$',
		views_extra.AdhocReportPropelldAppData.as_view(),name='adhoc-propelld-report'),
	url(r'^adhoc-propelld-report-ajax/$',
		views_extra.AjaxAdhocReportPropelld.as_view(), name='adhoc-propelld-report-ajax'),

]