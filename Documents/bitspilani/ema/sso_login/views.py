from django.shortcuts import render
from django.views.generic import View, RedirectView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied

# Create your views here.

@method_decorator([login_required(login_url=settings.LOGIN_URL),], name='dispatch')
class EMARemoteRedirectView(RedirectView):
	def get_redirect_url(self, *args, **kwargs):
		if self.request.user.is_superuser:
			return reverse_lazy('admin:index')
		elif self.request.user.remoteuser.user_type.user_role in ['STUDENT', 'RE-SCHL', 'CERT-SCHL']:
			return reverse_lazy('student:index')
		elif self.request.user.remoteuser.user_type.user_role == 'FACULTY':
			return reverse_lazy('faculty:index')
		elif self.request.user.remoteuser.user_type.user_role == 'CO-ORDINATOR':
			return reverse_lazy('coordinator:index')
		else:
			raise PermissionDenied