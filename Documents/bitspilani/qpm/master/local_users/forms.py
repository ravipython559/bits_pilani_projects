from django import forms
from master.models import RemoteUserRole, RemoteUser
from django.contrib.auth import get_user_model
import uuid

class LoginOrRegisterForm(forms.ModelForm):
	remote_user_type = forms.ModelChoiceField(
		queryset=RemoteUserRole.objects.exclude(user_role='ADM'),
		empty_label='--Choose Remote User Type--',required=True
	)

	def save(self, commit=True):
		
		instance = super(LoginOrRegisterForm, self).save(commit=False)
		email = self.cleaned_data['email']
		remote_user_type = self.cleaned_data['remote_user_type']

		if commit:
			
			user, created = get_user_model().objects.get_or_create(email=email, 
					defaults={'username':email,
					})
			if created:
				user.set_unusable_password()
				user.is_active = True
				user.save()
			create_user = RemoteUser.objects.update_or_create(
				login_user=user, 
				defaults={'user_type':remote_user_type},
			)

		return user

	class Meta(object):
		model = get_user_model()
		fields =  ('email', )