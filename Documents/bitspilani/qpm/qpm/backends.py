from django.contrib.auth.hashers import check_password
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from shibboleth.backends import ShibbolethRemoteUserBackend as SRUB
from django.core.exceptions import PermissionDenied
from master.models import RemoteUserRole, RemoteUser

class ShibbolethRemoteUserBackend(SRUB):
	create_unknown_user = True

	def get_user_role(self, shib_meta):
		role = shib_meta.get('role')
		return RemoteUserRole.objects.get(user_remote_code=role.strip()) 

	def get_admin_role(self, email):
		try:
			user = get_user_model().objects.get(email=email.strip())
			if user.is_superuser:
				user_type = RemoteUserRole.objects.get(user_role='SUPERUSER')
			else:
				user_type = None
		except Exception as e:
			user_type = None
		return user_type

	def get_co_ordinator_role(self, email):
		try:
			user = get_user_model().objects.get(email=email.strip())
			if user.remoteuser.user_type.user_role in ['MASTER-CO-ORDINATOR', 'CO-ORDINATOR']:
				user_type = user.remoteuser.user_type
			else:
				user_type = None
		except Exception as e:
			user_type = None
		return user_type

	def authenticate(self, request, remote_user, shib_meta):
		if not remote_user: return None

		User = get_user_model()
		username = self.clean_username(remote_user)

		field_names = [x.name for x in User._meta.get_fields()]
		shib_user_params = dict([
			(k, shib_meta[k]) for k in field_names if k in shib_meta
		])

		email = shib_user_params.pop('email')
		shib_user_params.update({'username':shib_user_params.pop('username'),})
		user, created = User.objects.get_or_create(email=email, defaults=shib_user_params)

		if created:
			user.set_unusable_password()
			user.save()
			user = self.configure_user(request, user)

		one_to_one_user, created = RemoteUser.objects.update_or_create(
			login_user=user, 
			defaults={
				'user_type':(
					self.get_admin_role(user.email) or 
					self.get_co_ordinator_role(user.email) or 
					self.get_user_role(shib_meta)
				)
			}
		)
		user = one_to_one_user.login_user

		return user if self.user_can_authenticate(user) else None

class UserModelEmailBackend(ModelBackend):

	def authenticate(self, request, *args, **kwargs):
		user = super(UserModelEmailBackend, self).authenticate(request, *args, **kwargs)
		if user is None:
			try:
				user = get_user_model().objects.get(email=kwargs.get('user_email'))
				return user
			except get_user_model().DoesNotExist:
				return None
		return user