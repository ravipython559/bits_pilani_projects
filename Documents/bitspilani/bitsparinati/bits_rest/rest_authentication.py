from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions

class ACAuthentication(authentication.BaseAuthentication):
	def authenticate(self, request):
		email = request.META.get('AC_EMAIL')
		if not email:
			return None

		try:
			user = User.objects.get(email=email)
		except User.DoesNotExist:
			raise exceptions.AuthenticationFailed('No such user in Application Center.')
		if not user.is_superuser:
			raise exceptions.AuthenticationFailed('You dont have superuser permission in Application Center.')

		return (user, None)