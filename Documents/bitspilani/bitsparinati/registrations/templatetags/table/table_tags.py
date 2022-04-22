#!/usr/bin/env python
# coding: utf-8
from django import template
from django.template import Context
from table.templatetags.table_tags import TableNode

register = template.Library()

class BitsTableNode(TableNode):
	template_name = "registrations/table/table.html"


@register.tag
def render_bits_table(parser, token):
	try:
		tag, table = token.split_contents()
	except ValueError:
		msg = '%r tag requires a single arguments' % token.split_contents()[0]
		raise template.TemplateSyntaxError(msg)
	return BitsTableNode(table)