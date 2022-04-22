from django.conf.urls import url, include
from . import views

from django.views.generic import TemplateView
from django.core.urlresolvers import reverse_lazy
from . import zest_settings as ZEST
from django.views.generic import FormView

urlpatterns = [
	url(r'^$', TemplateView.as_view(template_name='adhoc/emi_home.html'), name='applicantData'),

	url(r'^home/$', views.AdhocTokenLogin.as_view(), name='home',),
	url(r'^registrated-home/$', views.HomeRegisteredViews.as_view(), name='registered-home'),

	url(r'^pay-adhoc-fee-view-token-user/(?P<pk>\d+)/$', 
		views.UnRegisteredAdhocFeeView.as_view(), 
		name='pay-adhoc-fee-view-token-user'
	),
	url(r'^pay-adhoc-fee-view/(?P<pk>\d+)/$', 
		views.AdhocFeeView.as_view(), 
		name='pay-adhoc-fee-view'
	),

	url(r'^zest-create-view-token/(?P<pk>\d+)/$', 
		views.UnRegisteredZestCreateEMI.as_view(), 
		name='zest-create-view-token'
	),	 	
	url(r'^zest-create-view/(?P<pk>\d+)/$', 
		views.ZestCreateEMI.as_view(), 
		name='zest-create-view'
	),
	
	url(r'^pay-adhoc-fee-return/$', views.AdhocPaymentReturn.as_view(), name='pay-adhoc-fee-return'),
	url(r'^direct-adhoc-payment/$', views.direct_adhoc_payment, name='direct-pay-adhoc-fee'),
	url(r'^fee-receipt-pdf/(?P<pk>\d+)/$', views.AdhocReceiptPdf.as_view(), name='adhoc-fee-receipt-pdf'),


	url(r'^zest-return-view/$', TemplateView.as_view(template_name='adhoc/zest_return.html'), 
		name='zest-return-view'),
	url(r'^zest-success-view/$', TemplateView.as_view(template_name='adhoc/zest_success.html'), 
		name='zest-success-view'),

	url(r'^adhoc-ajax-validation/$', views.AdhocAjax.as_view(), name='adhoc-ajax-validation'),
	url(r'^eduvanz/', include('adhoc.eduvanz.urls', namespace="eduvanz")),
	url(r'^ezcred/', include('adhoc.ezcred.urls', namespace="ezcred")),
	url(r'^propelld/', include('adhoc.propelld.urls', namespace="propelld")),

]