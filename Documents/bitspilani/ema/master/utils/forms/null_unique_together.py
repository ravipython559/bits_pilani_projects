from django import forms

class UniqueValidateMixin(object):
	def get_filters(self):
		unique_fields = self._meta.model._meta.unique_together[0]	
		return [ (field, getattr(self.instance, field)) for field in unique_fields ]

	def validate_unique(self, *args, **kwargs):

		query = self._meta.model.objects.all()
		query = query.exclude(pk=self.instance.pk) if self.instance.pk else query	
		filter_attr = self.get_filters()
		try:
			if query.filter(**dict(filter_attr)).exists():
				raise forms.ValidationError("duplicate entry exists")
		except forms.ValidationError as e:
			self._update_errors(e)

		super(UniqueValidateMixin, self).validate_unique(*args, **kwargs)