from rest_framework import viewsets, permissions, authentication, exceptions
from rest_framework.permissions import AllowAny
from .models import Agent
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
from django.core.signing import TimestampSigner, SignatureExpired

authentication_classes = (authentication.TokenAuthentication,)
permission_classes = (permissions.IsAuthenticated,)

class BoundTokenAuthentication(authentication.TokenAuthentication):
	model = Agent

	def authenticate_credentials(self, token):
		model = self.get_model()
		key = token.split(':')[0]

		try:
			agent = model.objects.get(key=key)
			signer = TimestampSigner()
			value = signer.unsign(token, max_age=agent.timeout)

		except model.DoesNotExist:
			raise exceptions.AuthenticationFailed('Invalid token.')

		except SignatureExpired:
			raise exceptions.AuthenticationFailed('token Expired')

		if value != agent.key:
			raise exceptions.AuthenticationFailed('Invalid user token')

		return (AnonymousUser(), agent)

try:
	from .local_rest_utils import authentication_classes, permission_classes
except :
	print("ignore for production")

