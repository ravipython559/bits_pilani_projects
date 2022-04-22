"""bits URL Configuration.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from registrations.forms import (
    MyRegForm, MyAuthenticationForm, EmailValidationOnForgotPassword)
from registration.forms import RegistrationFormUniqueEmail
# from registration.backends.hmac.views import RegistrationView
from django.contrib import admin
from registrations.views import protected_serve
from django.views.static import serve
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from registrations.views import RegistrationViewUser,RegistrationView,LoginOrRegister, ActivationEmailResend
from django.views.static import serve
urlpatterns = [
    url(r'^$', RegistrationView.as_view(form_class=MyRegForm,
        template_name = 'registration/registration_form.html',
        success_url ='/accounts/login/'),
        name="registration_register_home"),
    url(r'^accounts/register/$', RegistrationView.as_view(form_class=MyRegForm,
        template_name = 'registration/registration_form.html',
        success_url ='/accounts/login/'),
        name="registration_register"),
    url(r'^admin/login/$', auth_views.login,
        {'template_name': 'registration/login.html',
            'authentication_form': MyAuthenticationForm},
        name='auth_login'),

    url(r'^admin/', admin.site.urls),                         
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    url(r'^api-auth/', include('rest_framework.urls',
        namespace='rest_framework')),
    url(r'^bits/', include("bits_rest.urls", namespace="bits_rest")),
    url(r'^accounts/password/reset/$', auth_views.password_reset,
        {'post_reset_redirect': '/accounts/password/reset/done/',
            'password_reset_form': EmailValidationOnForgotPassword,
            'html_email_template_name':
                'registration/password_reset_email.html'},
        name="auth_password_reset"),
    url(r'^accounts/login/$', auth_views.login,
        {'template_name': 'registration/login.html',
            'authentication_form': MyAuthenticationForm},
        name='auth_login'),
    url(r'^accounts/', include('registration.backends.hmac.urls')),
    url(r'^registrations/', include("registrations.urls",
        namespace="registrationForm")),


    
    url(r'^bits-admin/', include('bits_admin.urls', namespace="bits_admin")),
    url(r'^specific-applicant/', include('application_specific.urls',
        namespace='application_specific')),
    url(r'^waiver-applicant/', include('waiver.urls',
        namespace='application_waiver')),
    url(r'^super-reviewer/', include('super_reviewer.urls',
        namespace='super_reviewer')),
    url(r'^reviewer/', include("registrations.urls_extra",
        namespace="reviewer")),
    url(r'^payment-reviewer/', include("payment_reviewer.urls",
        namespace="payment_reviewer")),
    url(r'^bits-admin-payment/', include('bits_admin.urls_extra', namespace="bits_admin_payment")),
    url(r'^business-user/', include('business_dev.urls', namespace="business_user")),
    url(r'^sub-reviewer/', include('sub_reviewer.urls', namespace="sub_reviewer")),
    url(r'^certificate/', include('certificate.urls', namespace="certificate")),
    url(r'^registration-api/', include('semester_api.urls', namespace="semester_api")),
    url(r'^adhoc/', include('adhoc.urls', namespace='adhoc')),
    url(r'^table/', include('table.urls')),
    url(r'^login-or-register-local/$',LoginOrRegister.as_view(), name='login-or-register-local'),
    url(r'^resend-activation-email-74294192/$', ActivationEmailResend.as_view(), name='activation-send')
    #url(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}, 
    #    name='static_url'),

] # + static('/static', document_root=settings.STATIC_ROOT)


try:
    from .local_urls import *
    urlpatterns += local_patterns
except:
    print("No local settings found.")

