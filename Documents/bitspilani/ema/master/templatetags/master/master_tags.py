from django import template
from master.models import *
from master.utils.extra_models.querysets import *
from textwrap import wrap

register = template.Library()


@register.filter
def get_location(pk):
	return ExamAttendance.objects.get(pk=pk).exam_venue.location

@register.filter
def get_ev(pk):
	return ExamAttendance.objects.get(pk=pk).exam_venue

@register.filter
def get_course_code(pk):
	return ExamAttendance.objects.get(pk=pk).course.course_code

@register.filter
def get_course_name(pk):
	return ExamAttendance.objects.get(pk=pk).course.course_name

@register.filter
def get_student_planned(pk):
	obj = ExamAttendance.objects.get(pk=pk)
	return get_student_planned_count(obj,obj.exam_venue)

@register.filter(name='is_image')
def is_image(path):
	return True if path else False

@register.inclusion_tag("master/inclusion/hallticket_multiple_exam_types.html")
def display_hallticket_exam_types(ht_tuple):
	return {
		"evaluation_type":ht_tuple[0][0] if len(ht_tuple) else "",
		"examtype_tuple":set(ht_tuple),
		"examtype_tuple_len":len(set(ht_tuple)),
	}

@register.simple_tag
def get_student_count(dictionary, course_id, venue_id):
	if course_id in dictionary:
		return dictionary[course_id].get(venue_id, '')
	return ''

@register.simple_tag
def get_students_attendace_count(dictionary, course_id, venue_id):
	if course_id in dictionary:
		return dictionary[course_id].get(venue_id, 0)
	return 0


@register.simple_tag
def get_student_count_by_venue_by_slot(dictionary, venue_id, slot_id):
	if venue_id in dictionary:
		return dictionary[venue_id].get(slot_id, 0)
	return 0

from django.utils.safestring import mark_safe
@register.simple_tag
def get_student_hall(course):
	# http://hallticket.x.codeargo.com/administrator/views/hall-ticket.pdf/2019ab04070/4/
	if "student_reg" in course.keys():
		if course['student_reg'] != '-':
					return '-'
		else:
			href = "/administrator/views/hall-ticket.pdf/{}/{}/".format(course['s_id'],int(course['sem_id']))
			return mark_safe("""<a href={} target="_blank" rel="noopener noreferrer">HallTicket</a>""".format(href))
	else:
		href = "/administrator/views/hall-ticket.pdf/{}/{}/".format(course['s_id'],int(course['sem_id']))
		return mark_safe("""<a href={} target="_blank" rel="noopener noreferrer">HallTicket</a>""".format(href))

@register.simple_tag

def get_course_hal(course):
	
	
	if CourseExamShedule.objects.filter(course_code=course['course_code']):
		course = CourseExamShedule.objects.filter(course_code=course['course_code'])[0]
	else:
		course = course['course_code']	
		
	return course

#Template tags for hall-ticket issue status without hall-ticket
@register.simple_tag
def get_course_student_registration(course):
	if CourseExamShedule.objects.filter(course_code=course):
		course = CourseExamShedule.objects.filter(course_code=course)[0]	
	return course

@register.simple_tag
def get_course_name_long_text(course_name):
	a = wrap(course_name.upper(), 13)
	return mark_safe('<br>'.join(a))


@register.simple_tag
def get_exam_type_student_registration(data,exam_slots):
	check = dict(exam_slots)
	if 'exam_slot' in check:
		if exam_slots['exam_slot'] !='undefined':
			ce = CurrentExam.objects.filter(is_active=True,program__program_code=data["program_code"]).values_list('exam_type',flat=True)
			data = CourseExamShedule.objects.filter(course_code=data["course_code"],
											semester=data["semester_id"],
											batch__batch_name=data["b_name"],
											exam_type__in=ce,
											exam_slot__in = list(map(int,exam_slots.getlist('exam_slot') )))
			exam = ExamVenueSlotMap.objects.filter(exam_slot__in = list(map(int,exam_slots.getlist('exam_slot') )))
			e_type = []
			for i in data:
				e_type.append(i.exam_type)
			return ' - '.join(map(str, e_type))
		else:
			return ' - '
	else:
		return ' - '

@register.simple_tag
def get_exam_slot_student_registration(data,exam_slots):
	check = dict(exam_slots)
	if 'exam_slot' in check:
		if exam_slots['exam_slot'] !='undefined':
			ce = CurrentExam.objects.filter(is_active=True,program__program_code=data["program_code"]).values_list('exam_type',flat=True)
			data = CourseExamShedule.objects.filter(course_code=data["course_code"],
											semester=data["semester_id"],
											batch__batch_name=data["b_name"],
											exam_type__in=ce,
											exam_slot__in = list(map(int,exam_slots.getlist('exam_slot') )))
			ex_slot = []
			for i in data:
				ex_slot.append(str(i.exam_slot.slot_day)+' '+str(i.exam_slot.slot_date)+ ' '+str(i.exam_slot.slot_name))
			return ' - '.join(map(str, ex_slot))
		else:
			return ' - '
	else:
		return ' - '
