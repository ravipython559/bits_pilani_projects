from django import forms
from master.utils.extra_models.querysets import get_instance_or_none


class TextWidgetMixin(object):

	def __init__(self, db_model=None, *args, **kwargs):
		super(TextWidgetMixin, self).__init__(*args, **kwargs)
		self.db_model = db_model

	def display_values(self, value):
		return str(get_instance_or_none(self.db_model, pk=value) if value else '-')

	def render(self, name, value, attrs=None, renderer=None):
		if attrs:
			attrs['display_name'] = self.display_values(value)
		html_render = super(TextWidgetMixin, self).render(name, value, 
			attrs=attrs, renderer=renderer)
		return html_render


class ForeignTextWidget(TextWidgetMixin, forms.Widget):
	template_name = 'master/widgets/textspan.html'