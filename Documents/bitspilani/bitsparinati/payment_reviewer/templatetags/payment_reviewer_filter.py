from django import template
from django.template import Context

register = template.Library()


class BitsTableNode(template.Node):
	template_name = "payment_table/table.html"

	def __init__(self, table):
		self.table = template.Variable(table)

	def render(self, context):
		table = self.table.resolve(context)
		context = Context({'table': table})
		t = template.loader.get_template(self.template_name)
		return t.render(context)


@register.tag
def bits_render_table(parser, token):
	try:
		tag, table = token.split_contents()
	except ValueError:
		msg = '%r tag requires a single arguments' % token.split_contents()[0]
		raise template.TemplateSyntaxError(msg)
	return BitsTableNode(table)
