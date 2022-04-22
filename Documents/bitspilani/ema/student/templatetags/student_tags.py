
from django import template
from master.models import *
from master.utils.extra_models.querysets import *
from datetime import datetime

register = template.Library()

@register.inclusion_tag('student/inclusion/inclusion_hall_ticket_form_display.html')
def inclusion_hall_ticket_form_display(form, exam_type, exam_slot, location, exam_venue):

	return {
		'form':form,
		'exam_type':get_instance_or_none(ExamType,pk=exam_type),
		'exam_slot':get_instance_or_none(ExamSlot, pk=exam_slot),
		'location':get_instance_or_none(Location, pk=location),
		'exam_venue':get_instance_or_none(ExamVenue, pk=exam_venue),
	}


@register.filter(name='grouping_ordered_dates')
def grouping_ordered_dates(queryset):
	dates_group=set()
	string_dates=''

	for Ticket_Info in queryset:
		dates_group.add(Ticket_Info.exam_slot.slot_date)

	dates_dict={}
	for x in dates_group:
		dates_dict.setdefault(int(str(x.year)+datetime.strftime(x,'%m')), []).append(x) 

	for x,date_list in sorted(dates_dict.items()):  
		string_dates=" {} {}".format(string_dates,date_list[0].strftime("%B")) 
		for date_val in date_list:
			string_dates="{} {},".format(string_dates,date_val.strftime("%d")) 
		if x==list(sorted(dates_dict.keys()))[-1]: 
			year_str="{} {}." 
		elif x==list(sorted(dates_dict.keys()))[-2]: 
			year_str= "{} {} and" 
		else: 
			year_str= "{} {},"  
		string_dates=year_str.format(string_dates,date_list[0].strftime("%Y")) 
	return string_dates


@register.simple_tag
def check_to_disable_filed(student,course_code,exam_type,semester):
	exam_id = get_instance_or_none(ExamType,pk=exam_type)
	OEA = get_filter_queryset(OnlineExamAttendance, **{"student_id":student})
	stu_batch = Student.objects.filter(student_id=student)[0]

	if OEA and exam_id:
		exam_attendence  = OEA.filter(course_code=course_code,exam_type__exam_type=exam_id.exam_type,
						exam_type__evaluation_type=exam_id.evaluation_type,
						semester__semester_name=semester,makeup_allowed=False,).values()

		cur_exam = CurrentExam.objects.filter(exam_type__exam_type=exam_id.exam_type,is_active=True,
												exam_type__evaluation_type=exam_id.evaluation_type,
												semester__semester_name=semester,
												program__program_code = student[4:8],
												batch =stu_batch.batch)

		if exam_attendence:
			eval_type = ExamType.objects.get(id=exam_attendence[0]['exam_type_id'])
			cur_exam = cur_exam.filter(exam_type__evaluation_type=eval_type.evaluation_type).exists()


			if cur_exam:
				return "grayy"
			else:
				return " "
		else:
			return " "

