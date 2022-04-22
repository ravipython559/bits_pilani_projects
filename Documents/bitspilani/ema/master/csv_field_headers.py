from django.utils import timezone

STUDENT_REGISTRATION_SEARCH_FIELDS = [
	'student__student_id',
	'student__student_name',
	'course_code',
	'course_name',
	'semester__semester_name',
]

STUDENT_REGISTRATION_FIELD = ('student__student_id',
	'student__student_name',
	'course_code',
	'course_name',
	'semester__semester_name',
)

STUDENT_REGISTRATION_HEADERS = {
	'student__student_id':'Student ID',
	'student__student_name':'Student Name',
	'course_code':'Course Code',
	'course_name':'Course Name',
	'semester__semester_name':'Semester',
}