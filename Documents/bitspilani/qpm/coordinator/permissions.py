from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from master.models import StaffUserAccessList

class QPMUserPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):

	def test_func(self):
		if StaffUserAccessList.objects.filter(user_id=self.request.user.email,coordinator_flag=True).first():
			if self.request.user.remoteuser.user_type.user_role in ['FACULTY','ON-FAC','OF-FAC', 'G-FAC']:
				return True
		return self.request.user.remoteuser.user_type.user_role == 'CO-ORDINATOR'
