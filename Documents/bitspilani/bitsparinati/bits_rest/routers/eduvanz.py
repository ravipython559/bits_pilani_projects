from django.conf.urls import include, url
from bits_rest.viewsets.eduvanz import views

urlpatterns = [
	url(r'^eduvanz-application/', views.ApplicationCreateView.as_view(), name='application'),
	url(r'^eduvanz-api/(?P<pk>\d+)/', views.Eduvanz.as_view(), name='api'),
	url(r'^eduvanz-callback/', views.CallBackView.as_view(), name='callback'),
	url(r'^eduvanz-landing-page/(?P<pk>\d+)/', views.EduvanzRedirectView.as_view(), name='landing'),
]