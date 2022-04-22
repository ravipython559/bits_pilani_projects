"""Django Custom User Model with Email."""
from django.contrib.auth.hashers import check_password
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class UserModelEmailBackend(ModelBackend):
	"""Custom user model class with email id as the user name."""

	def authenticate(self, username="", password="", **kwargs):
		"""Authenticate a user with user name as email id and password."""
		try:
			user = get_user_model().objects.get(email__iexact=username)
			if check_password(password, user.password):
				return user
			else:
				return None
		except get_user_model().DoesNotExist:
			# No user was found, return None - triggers default login failed
			return None


class UserModelEmailApiBackend(ModelBackend):
	def authenticate(self, email):
		try:
			user = get_user_model().objects.get(email=email,)
			return user
		except get_user_model().DoesNotExist:
			return None

class UserModelEmailBackendLocal(ModelBackend):

	def authenticate(self, username="", password="", **kwargs):
		try:
			user = get_user_model().objects.get(email=username)
			return user
		except get_user_model().DoesNotExist:
			return None
		return user
