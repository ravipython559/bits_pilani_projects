from django.shortcuts import render
from django.views.generic import View, RedirectView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from master.models import StaffUserAccessList
# Create your views here.

@method_decorator([login_required(login_url=settings.LOGIN_URL),], name='dispatch')
class RegistrationRemoteRedirectView(RedirectView):
	def get_redirect_url(self, *args, **kwargs):
		if self.request.user.is_superuser:
			return reverse_lazy('administrator:qp_submission_status_view')
		elif self.request.user.remoteuser.user_type.user_role in ['FACULTY','ON-FAC','OF-FAC', 'G-FAC']:
			if StaffUserAccessList.objects.filter(user_id=self.request.user.email,coordinator_flag=True).first():
				return reverse_lazy('coordinator:qp_submission_status_view')
			return reverse_lazy('faculty:index')

		elif self.request.user.remoteuser.user_type.user_role in ['STF']:
			if StaffUserAccessList.objects.filter(user_id=self.request.user.email).first():
				return reverse_lazy('faculty:index')
			else:
				return reverse_lazy('master:unauthorised')
		elif self.request.user.remoteuser.user_type.user_role == 'CO-ORDINATOR':
			if StaffUserAccessList.objects.filter(user_id=self.request.user.email,coordinator_flag=True).first():
				return reverse_lazy('coordinator:qp_submission_status_view')
			else:
				return reverse_lazy('master:unauthorised')
		else:
			raise PermissionDenied