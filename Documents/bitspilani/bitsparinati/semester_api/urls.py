from django.conf.urls import url, include
from . import views
from django.views.generic import RedirectView, TemplateView
from semester_api import zest_settings as ZEST

urlpatterns = [
	url(r'^$', TemplateView.as_view(template_name='semester_api/emi_home.html'), 
		name='applicantData'),
	url(r'^zestmoney/zestpay/updateorder$', views.ZestCallbackView.as_view(), name='zest-callback-view'),
	url(r'^zest-create-view/$', views.ZestCreateEMI.as_view(), name='zest-create-view'),
	url(r'^zest-return-view/$', RedirectView.as_view(url=ZEST.REG_RETURN_URL), 
		name='zest-return-view'),
	url(r'^zest-success-view/$', RedirectView.as_view(url=ZEST.REG_SUCCESS_URL), 
		name='zest-success-view'),
	url(r'^emi-report/$',
		views.EMIReportAppData.as_view(),name='emi-report'),
	url(r'^emi-status/$',
		views.ZestStatusEMI.as_view(), name='sync_status'),
	url(r'^emi-report-ajax/$',
		views.AjaxEMIReport.as_view(), name='emi-report-ajax'),
	url(r'^emi-status-ajax/$',
		views.ZestEMIStatus.as_view(), name='emi-status-ajax'), 
	url(r'^emi-delete/$',
		views.ZestDeleteEMI.as_view(), name='emi-delete'),
	url(r'^test-api/$',
		TemplateView.as_view(template_name='semester_api/test_api.html'),name='test-api'),
	url(r'^paytm_create_view/$', views.PaytmCreateView.as_view(), name='paytm-create-view'),
	url(r'^paytm-integration/$', views.paytmIntegration.as_view(), name='paytm-integration'),
	url(r'^paytm-callback/$', views.paytmCallback.as_view(), name='paytm-callback'),
	url(r'^paytm-status/$', views.paytmStatus.as_view(), name='paytm-status'),
]
