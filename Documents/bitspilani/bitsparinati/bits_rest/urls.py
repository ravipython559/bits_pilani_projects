from django.conf.urls import url, include
from . import views, views_zest, rest_views
from django.views.generic import TemplateView
from registrations.views import view_data
from rest_framework.routers import DefaultRouter
from rest_framework_bulk.routes import BulkRouter

program_router = DefaultRouter()
program_router.register(r'cs', rest_views.CandidateSelectionViewSet, base_name='cs',)
program_router.register(r'cs-arch', rest_views.CandidateSelectionArchivedViewSet,base_name='cs-arch',)

call_router = DefaultRouter()
call_router.register(r'inbound', rest_views.InboundViewSet, base_name='inbound',)
call_router.register(r'outbound', rest_views.OutboundViewSet, base_name='outbound',)

call_bulk_router = BulkRouter()
call_bulk_router.register(r'inbound', rest_views.InboundBulkViewSet, base_name='inboundbulk',)
call_bulk_router.register(r'outbound', rest_views.OutboundBulkViewSet, base_name='outboundbulk',)


urlpatterns = [
	url(r'^$', TemplateView.as_view(template_name='bits_rest/emi_home.html'), name='applicantData'),
	url(r'payreceive/$', views.bits_view, name="bits_view"),
	url(r'pay-adm-receive/$', views.bits_view_admission, name="bits-view-admission"),
	url(r'^zest-return-view/$', TemplateView.as_view(template_name='bits_rest/zest_return.html'), name='zest-return-view'),
	url(r'^zest-success-view/$', TemplateView.as_view(template_name='bits_rest/zest_success.html'), name='zest-success-view'),
	url(r'^zest-create-view/$', views_zest.ZestCreateEMI.as_view(), name='zest-create-view'),
	url(r'^zestmoney/zestpay/updateorder$', views_zest.ZestCallbackView.as_view(), name='zest-callback-view'),  
	url(r'^api/(?P<timestamp>(\d+\.\d+|\d*))/(?P<pg_code>\w*)/v1/', include(program_router.urls, namespace='ac-api-v1')),
	url(r'^api/auth/v1/$', rest_views.ACAuthToken.as_view(), name='auth-ac-api'),
	url(r'^api/v1/call/', include(call_router.urls, namespace='call-api-v1')),
	url(r'^api/v1/call/bulk/', include(call_bulk_router.urls, namespace='call-bulk-api-v1')),
	url(r'^api/v1/call/hall-ticket/(?P<student_id>\w+)/$', rest_views.HallTicketView.as_view(), name='hall-ticket-api'),
	url(r'^api/v1/call/auth/$', rest_views.AgentAuthToken.as_view(), name='call-auth-api'),
	url(r'^paytm/', include('bits_rest.routers.paytm', namespace="paytm")),
	url(r'^eduvanz/', include('bits_rest.routers.eduvanz', namespace="eduvanz")),
	url(r'^ezcred/', include('bits_rest.routers.ezcred', namespace="ezcred")),
	url(r'^propelld/', include('bits_rest.routers.propelld', namespace="propelld")),
]

