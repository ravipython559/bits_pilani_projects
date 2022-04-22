from table import Table
from table.columns import Column, CheckboxColumn, DatetimeColumn, LinkColumn, Link
from table.utils import Accessor
from table.utils import A, mark_safe
from django.utils.html import escape
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse_lazy
from master.models import HallTicket, StudentRegistration, CurrentExam, Program
from django.template.loader import render_to_string
from django.db.models import OuterRef, Subquery, Value
from master.utils.extra_models.querysets import *
from ema import default_settings as S
from django.db.models.functions import Concat, Substr 
import functools, operator

class PlannedColumn(Column):
	def render(self, obj):
		ce = CurrentExam.objects.filter(is_active=True)
		ht = HallTicket.filter_hallticket.annotate(
			pg_code=Substr('student__student_id', 5, 4),).filter(is_cancel=False,)
		ht = ht.filter(
			functools.reduce(
				operator.or_,
				(
					Q(
						pg_code=q.program.program_code, 
						exam_type=q.exam_type, 
						semester=q.semester
					) for q in ce.iterator()
				)
			),
			semester=obj.courseexamshedule.semester,
			course=obj.courseexamshedule,
			exam_type=obj.courseexamshedule.exam_type,
			exam_slot=obj.courseexamshedule.exam_slot,
			exam_venue=obj.examvenueslotmap.exam_venue,
		)
		return mark_safe(str(ht.count()))

class HTMLColumn(Column):
	def render(self, value):
		return format_html(Accessor(self.field).resolve(value))

class PhotoLink(Link):
	def render(self, obj):
		if not obj.photo:
			return escape('-')
		return super().render(obj)

class HallTicketLink(Link):
	def render(self, obj):
		check_for_current_exam = CurrentExam.objects.filter(is_active=True,
													semester_id=obj.semester_id,
													program__program_code=obj.program_code).values_list('exam_type_id',flat=True)

		if obj.exam_type_id in check_for_current_exam and obj.venue_short_name != '-':
			return super().render(obj)
		else:
			return escape('-')
		return super().render(obj)

class FilterColumn( Column ):
	''' Display input and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)			
		return escape(data if data else '')

class ExamSlotColumn( Column ):
	''' Display input and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)
		if value.exam_slot.slot_name == S.EXAM_SLOT_NAME:
			return escape('-')
		return escape(data if data else '')

class PGColumn( Column ):
	''' Display input and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)			
		return escape(data if data else 'all')

class DTColumn( DatetimeColumn ):
	''' Display Date and blank instead of None '''
	def render(self, value):
		date = Accessor(self.field).resolve(value)
		text = timezone.localtime(date).strftime("%d/%m/%Y") if date else ''
		return escape(text)

class DColumn( DatetimeColumn ):
	''' Display Date and blank instead of None '''
	def render(self, value):
		date = Accessor(self.field).resolve(value)
		text = date.strftime("%d/%m/%Y") if date else ''
		return escape(text)

class TemplateColumn(Column):
	template_name = None

	def get_context_data(self, **kwargs):
		context = kwargs.copy()
		return context

	def render(self, value):
		context = self.get_context_data(value=value)
		msg_plain = render_to_string(self.template_name, context)
		# msg_plain = mark_safe_curly(msg_plain) 
		return format_html(msg_plain)

class HallTicketColumn(TemplateColumn):

	template_name = 'master/table_column/hallticket_model.html'

	def get_context_data(self, **kwargs):
		value = kwargs['value']
		context = super().get_context_data(**kwargs)
		ht = HallTicket.objects.filter(student=value, is_cancel=False)
		if ht.exists():
			context['ht'] = ht 
		else:

			ces = CourseExamShedule.objects.filter(
				course_code__in=Subquery(value.studentregistration_stud.values('course_code')),
				semester__in=Subquery(value.studentregistration_stud.values('semester')),
			)

			context['ce'] = CurrentExam.objects.filter(
				exam_type__in=Subquery(ces.values('exam_type')),
				semester__in=Subquery(value.studentregistration_stud.values('semester')),
				batch=value.batch,
				program__in=Subquery(Program.objects.filter(program_code=value.student_id[4:8]).values('pk')),
				is_active=True
				)
			context['sr'] = value.studentregistration_stud.all()

		return context

class IntegerColumn(TemplateColumn):
	
	template_name = 'master/table_column/integer_field.html'

	def __init__(self, global_js_variable, bulk_prefix, field=None, header=None, **kwargs):
		self.global_js_variable = global_js_variable
		self.bulk_prefix = bulk_prefix
		kwargs["safe"] = False
		kwargs["sortable"] = False
		kwargs["searchable"] = False
		super().__init__(field=field, header=header, **kwargs)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['obj'] = kwargs['obj']
		context['field'] = self.field
		context['global_js_variable'] = self.global_js_variable
		context['bulk_prefix'] = self.bulk_prefix
		return context

	def render(self, obj):

		context = self.get_context_data(obj=obj)
		msg_plain = render_to_string(self.template_name, context)
		return mark_safe(str(msg_plain))