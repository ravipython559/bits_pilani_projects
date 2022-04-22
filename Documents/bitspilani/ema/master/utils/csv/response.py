import csv
from django.http import StreamingHttpResponse
from master.models import *

class Echo:
	def write(self, value):
		return value

def hall_ticket_issue_status(students_queryset):
	yield ('STUDENT ID', 'STUDENT NAME', 'EXAM TYPE', 'COURSE CODE', 'EXAM SLOT', 'EXAM VENUE', 'PHOTO', 'HALLTICKET')
	for student in students_queryset.iterator():
		ht_queryset = HallTicket.objects.filter(student=student, exam_type__pk=student.e_type_id, is_cancel=False)
		if ht_queryset.exists():
			for ht in ht_queryset.iterator():
				yield (student.student_id, student.student_name, student.e_type, 
					ht.course.course_code, ht.exam_slot, ht.exam_venue, student.photo and 'Yes', 'Yes')
		else:
			for reg in StudentRegistration.objects.filter(student=student).iterator():
				yield (student.student_id, student.student_name, student.e_type, 
					reg.course_code, '-', '-', student.photo and 'Yes', '-')


def hall_ticket_csv_streaming_csv_response(students_queryset):
	writer = csv.writer(Echo())
	response = StreamingHttpResponse((writer.writerow(row) for row in hall_ticket_issue_status(students_queryset)), 
		content_type="text/csv")
	response['Content-Disposition'] = 'attachment; filename="hall_ticket_issue_status.csv"'
	return response
