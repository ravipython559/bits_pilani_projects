from django.contrib.auth import get_user_model
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.contrib.auth import authenticate, login
from master.local_users.forms import LoginOrRegisterForm

class LoginOrRegister(CreateView):
	model = get_user_model()
	template_name = 'master/local_user/login-or-register.html'
	success_url = reverse_lazy('sso_login:redirect')
	form_class = LoginOrRegisterForm

	def form_valid(self, form):
		self.object = form.save()
		user = authenticate(self.request, user_email=self.object.email)
		if user is not None:
			login(self.request, user)
		return super(LoginOrRegister, self).form_valid(form)