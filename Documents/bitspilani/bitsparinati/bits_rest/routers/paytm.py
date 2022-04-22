from django.conf.urls import include, url
from bits_rest.viewsets.paytm import views

urlpatterns = [
	url(r'^$', views.Home.as_view(), name='home'),
	url(r'^app-payment/', views.ApplicationPaymentView.as_view(), name='app_payment'),
	url(r'^adm-payment/', views.AdmissionPaymentView.as_view(), name='adm_payment'),
	url(r'^app-response/', views.ApplicationCallBack.as_view(), name='app-response'),
	url(r'^adm-response/', views.AdmissionCallBack.as_view(), name='adm-response'),

]