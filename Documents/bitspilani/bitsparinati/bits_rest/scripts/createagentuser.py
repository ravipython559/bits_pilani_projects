from bits_rest.models import Agent
from django.contrib.auth.hashers import make_password

def run(*args):
	username = raw_input('username:')
	password = raw_input('password:')
	Agent.objects.create(username=username, password=make_password(password))
	print('successfully created:')
	print('username:', username)
	print('password:', password)
