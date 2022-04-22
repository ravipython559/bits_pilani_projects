from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin

class EMAUserPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):

	def test_func(self):
		return self.request.user.remoteuser.user_type.user_role == 'CO-ORDINATOR'
