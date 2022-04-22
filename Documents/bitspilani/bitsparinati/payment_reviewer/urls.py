from django.conf.urls import url, include
from . import views
from bits_admin import views as admin_views

urlpatterns = [
	url(r'^$', views.payment_reviewer_home,name='payments-reviewer'),

	url(r'^upload-manual-payments/$', views.upload_manual_payments,
		name='upload-manual-payments-home'),
	url(r'^upload-gateway-payments/$', views.upload_gateway_payments,
		name='upload-gateway-payments-home'),

	url(r'^upload-manual-payments/(?P<alert_status>\w+)/$', views.upload_manual_payments,
		name='upload-manual-payments'),
	url(r'^upload-gateway-payments/(?P<alert_status>\w+)/$', views.upload_gateway_payments,
		name='upload-gateway-payments'),

	url(r'^preview-manual-payments/(?P<file_name>\w+)/(?P<csv_file_name>[\w\.\-\W]+)/$',
	 	views.preview_manual_payments,
		name='preview-manual-payments'),
	url(r'^preview-gateway-payments/(?P<file_name>\w+)/(?P<csv_file_name>[\w\.\-\W]+)/$', 
		views.preview_gateway_payments,
		name='preview-gateway-payments'),

	url(r'^reconcile-manual-payments/$', views.reconcile_manual_payments,
		name='reconcile-manual-payments'),
	url(r'^reconcile-gateway-payments/$', views.reconcile_gateway_payments,
		name='reconcile-gateway-payments'),

	url(r'^reconcile-manual-payments-ajax/(?P<file_name>\w+)/$',
		views.RMPView.as_view(),name='rec-manual-payments-ajax'),
	url(r'^reconcile-gateway-payments-ajax/(?P<file_name>\w+)/$',
		views.RGPView.as_view(),name='rec-gateway-payments-ajax'),

	url(r'^hist-manual-payments-ajax/(?P<st>[\w\-\s\.\,]+)/(?P<fm_dt>[\d\-\:\s]+)/(?P<to_dt>[\d\-\:\s]+)/$',
		views.HMPView.as_view(),name='hist-manual-payments-ajax'),
	url(r'^hist-gateway-payments-ajax/(?P<st>[\w\-\s\.\,]+)/(?P<fm_dt>[\d\-\:\s]+)/(?P<to_dt>[\d\-\:\s]+)/$',
		views.HGPView.as_view(),name='hist-gateway-payments-ajax'),

	url(r'^hist-manual-payments/$', views.hist_manual_payments,
		name='hist-manual-payments-home'),
	url(r'^hist-gateway-payments/$', views.hist_gateway_payments,
		name='hist-gateway-payments-home'),

	url(r'^hist-manual-payments/(?P<alert_status>[a-z]+)/$', views.hist_manual_payments,
		name='hist-manual-payments'),
	url(r'^hist-gateway-payments/(?P<alert_status>\w+)/$', views.hist_gateway_payments,
		name='hist-gateway-payments'),

	url(r'^hist-manual-payments-csv/$', views.csv_hist_manual_payments,
		name='hmp-csv'),
	url(r'^hist-gateway-payments-csv/$', views.csv_hist_gateway_payments,
		name='hgp-csv'),

	url(r'^paymentData/$', views.paymentDataView, name='paymentData'),
    url(r'^createpaymentcsv/$',views.csv_payment_view, name='createpaymentCSV'),
    url(r'^date-refresh-payment/$',views.date_refresh_payment, name='dateFormat1'),
    url(r'^payment_ajax_data/(?P<fm_dt>[\d\-\:\s]+)/(?P<to_dt>[\d\-\:\s]+)/(?P<bank>[\w\-\s\.\,]+)$',
    	views.PaymentAppDataView.as_view(), name='pay_app_table_data'),

    url(r'^adminapplicationViews/(?P<id>\d+)/$', 
        admin_views.ApplicationAdminView,
        name="admin-application-views"),

    url(r'^program-admissions-report/$',
		views.ProgramAdmissionsReport.as_view(), name='program-admissions-report'),
	
	url(r'^program-admissions-report-ajax/(?P<pg>\d+)/(?P<pg_type>[\w\-\s\.\,]+)/(?P<adm_btc>[\w\-\s]+)$',
		views.ProgramAdmissionsReportAjax.as_view(), name='program-admissions-report-ajax'
	 ),
]