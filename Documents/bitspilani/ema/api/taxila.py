import requests
import re
from django.db import IntegrityError, transaction
from master.models import DataSyncLogs, StudentRegistration, Semester, Student, Batch
from ema import default_settings as S


class API:
	TAXILA_COURSES_URI = str('https://taxila-aws.bits-pilani.ac.in/webservice/rest/server.php?'
		'wsfunction=core_course_get_courses'
		'&wstoken=e64c820b30f2ac13f173374c01ebcd06&moodlewsrestformat=json'
	)

	TAXILA_COURSE_USERS_URI = str('https://taxila-aws.bits-pilani.ac.in/webservice/rest/server.php?'
		'wsfunction=core_enrol_get_enrolled_users&courseid={course_id}'
		'&wstoken=e64c820b30f2ac13f173374c01ebcd06&moodlewsrestformat=json'
	)

	@staticmethod
	def taxila_get(url, **kwargs):
		print(url)
		response = requests.get(url)
		response.raise_for_status()
		return response

	@staticmethod
	def call_taxila_api(url):

		try:
			response = __class__.taxila_get(url)
			yield response.json()
			
			while 'next' in response.links:  
				response = __class__.taxila_get(response.links['next']['url'])
				yield response.json()
		
		except Exception as e:
			print('Error', e)
			pass

	@staticmethod
	def transaction(tax_student_name, tax_student_email, sem_name, course_code, trying_sequence):
		print('Inserted data: ',tax_student_name,tax_student_email, sem_name, course_code, trying_sequence)
		try:
			with transaction.atomic():

				student, created = Student.objects.get_or_create(
					student_id=tax_student_email.split('@')[0],
					defaults={'student_name':tax_student_name,'batch':Batch.objects.get(batch_name=S.BATCH_NAME)}
				)

				s_r = StudentRegistration.objects.update_or_create(
					student=student,
					course_code=course_code,
					semester=Semester.objects.get(taxila_sem_name=sem_name)
				)
		except Exception as e:
			raise Exception(
				'Error: %s|%s|%s|%s|%s'%(trying_sequence, tax_student_email, sem_name, course_code, e)
				) from e


	@staticmethod
	def insert_data(tax_student_name, tax_student_email, sem_name, course_code):

		try:
			__class__.transaction(tax_student_name, tax_student_email, sem_name, course_code, 'first try')
		except Exception as e:
			__class__.transaction(tax_student_name, tax_student_email, sem_name, course_code, 'Second try')

		return tax_student_email

	@staticmethod
	def get_data(sem, ces):
		errors = []
		inserted = []
		courses_tax_data = {}
		courses_shortname = {}

		sem_code = sem.taxila_sem_name
		exclude_full_name = ('courseware', 'dissertation', 'merged')

		for c in ces.iterator():
			courses_tax_data[str('%s_%s' %(sem_code, c.split(':')[0]))] = False
			courses_shortname[str('%s_%s' %(sem_code, c.split(':')[0]))] = (sem_code, c.split(':')[0])
 
		try:
			for courses in __class__.call_taxila_api(__class__.TAXILA_COURSES_URI):
				if all(courses_tax_data.values()):
					break

				for course in courses:

					if course['shortname'] in courses_tax_data:
						courses_tax_data[course['shortname']] = True
						print(course['shortname'], ':', course['fullname'].lower())
						
						if not any(map(lambda s: s in course['fullname'].lower(), exclude_full_name)):
							print('\n\n\n\t\t\t\tI Got You Student....\n\n\n')
							
							for tax_students in __class__.call_taxila_api(__class__.TAXILA_COURSE_USERS_URI.format(course_id=course['id'])):
								
								for tax_student in tax_students:
									if 10 in ( role['roleid'] for role in tax_student['roles']):
										try:
											inserted.append(
												__class__.insert_data(tax_student['fullname'], tax_student['email'], *courses_shortname[course['shortname']])
											)
											
										except Exception as e:
											print('Error', e)
											errors.append('shortname:%s, student:%s, error:%s' %(course['shortname'], 
												tax_student['email'], e))

					if all(courses_tax_data.values()):
						break

		except Exception as e:
			print('Outer Error', e)
			dslogs = DataSyncLogs.objects.create(
			source='taxila', records_pulled=len(inserted),
			status=DataSyncLogs.FAILED,
			parameters='<br><br>Success:<br>%s<br><br>Failed:<br>%s' %(', '.join(inserted), ', '.join(errors))
		)
		else:
		
			dslogs = DataSyncLogs.objects.create(
				source='taxila', records_pulled=len(inserted),
				status=DataSyncLogs.SUCCESS,
				parameters='filtered on:<br>%s<br>Success:<br>%s<br>Failed:<br>%s' %(
					', '.join(courses_shortname.keys()),
					', '.join(inserted or ['No Data Found',]), 
					', '.join(errors or ['No Data Found',])
				)
			)
		return dslogs.parameters

# vishal = APITaxila()
# vishal_data = vishal.get_taxila_data()
# Accionl@bs2143


