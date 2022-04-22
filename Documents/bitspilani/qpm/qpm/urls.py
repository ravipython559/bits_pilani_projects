"""qpm URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.urls import reverse_lazy
from django.views.generic import RedirectView
from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.views.static import serve
from django.http import HttpResponseNotFound

@login_required
def protected_serve(request, path, document_root=None, show_indexes=False):
    return HttpResponseNotFound("<h5>You don't have access to this Files</h5>")
    return serve(request, path, document_root, show_indexes)

urlpatterns = [
    path('', RedirectView.as_view(url=reverse_lazy('sso_login:redirect')), name='home'),
    path('secure-login/', include('sso_login.urls')),
    path('shib/', include('shibboleth.urls')),
    path('master-admin/', admin.site.urls),
    path('master/', include('master.urls')),
    path('faculty/',include('faculty.urls')),
    path('coordinator/',include('coordinator.urls')),
    path('administrator/', include('administrator.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 
urlpatterns.append(url(r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:], protected_serve, {'document_root': settings.MEDIA_ROOT}))

