from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin

class QPMUserPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):

	def test_func(self):
		if self.request.user.remoteuser.user_type.user_role =='ON-FAC':
			return self.request.user.remoteuser.user_type.user_role == 'ON-FAC'
		elif self.request.user.remoteuser.user_type.user_role =='OF-FAC':
			return self.request.user.remoteuser.user_type.user_role == 'OF-FAC'
		elif self.request.user.remoteuser.user_type.user_role =='G-FAC':
			return self.request.user.remoteuser.user_type.user_role == 'G-FAC'
		elif self.request.user.remoteuser.user_type.user_role =='STF':
			return self.request.user.remoteuser.user_type.user_role == 'STF'
		elif self.request.user.remoteuser.user_type.user_role =='CO-ORDINATOR':
			return self.request.user.remoteuser.user_type.user_role == 'CO-ORDINATOR'
		else:
			return False
