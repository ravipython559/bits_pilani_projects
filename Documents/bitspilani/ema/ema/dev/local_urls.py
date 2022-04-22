from django.conf import settings
from django.conf.urls.static import static
from ema.urls import urlpatterns as URLS
from django.urls import include, path
from master.local_users import views

urlpatterns = URLS

local_patterns = [
	path('login-or-register-local/', views.LoginOrRegister.as_view(), 
		name='login-or-register-local'),
]

urlpatterns += local_patterns

if settings.DEBUG:
	urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
