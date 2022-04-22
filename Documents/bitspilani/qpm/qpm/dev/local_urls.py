from django.conf import settings
from django.conf.urls.static import static
from qpm.urls import urlpatterns as URLS
from django.urls import include, path
from django.conf.urls import url
from master.local_users import views
from django.contrib.auth.decorators import login_required
from django.views.static import serve
from django.http import HttpResponseNotFound

#accessing media files through URL id disabled.
@login_required
def protected_serve(request, path, document_root=None, show_indexes=False):
	return HttpResponseNotFound("<h5>You don't have access to this Files</h5>")
	return serve(request, path, document_root, show_indexes)

urlpatterns = URLS
local_patterns = [
	path('login-or-register-local/', views.LoginOrRegister.as_view(), 
		name='login-or-register-local'),
]

urlpatterns += local_patterns
if settings.DEBUG:
	urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 
	urlpatterns.append(url(r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:], protected_serve, {'document_root': settings.MEDIA_ROOT}))
