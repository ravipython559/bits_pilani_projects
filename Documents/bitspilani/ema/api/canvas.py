import requests
import re
from django.db import IntegrityError, transaction
from master.models import DataSyncLogs, StudentRegistration, Semester, Student, Program, Batch
from master.utils.extra_models.querysets import get_instance_or_none
from ema import default_settings as S

class API:
	CANVAS_HEADER = {
		'Authorization':'Bearer 11693~NFAGSukRm58r4cC83yMTiMgj6SaLrxDmjTjD4IRec3BIxfDmWdP7y1S0UlN56dyI'
	}
	CANVAS_ACCOUNT_ID_URI = str('https://bits-pilani.instructure.com/api/v1/accounts/1/sub_accounts'
		'?recursive=true')
	CANVAS_COURSES_URI= str('https://bits-pilani.instructure.com/api/v1/accounts/{account_id}/courses/'
		'?per_page=10')
	CANVAS_COURSE_USERS_URI = str('https://bits-pilani.instructure.com/api/v1/courses/{course_id}/users/?enrollment_type[]=student&per_page=10')

	@staticmethod
	def canvas_get(url):
		response = requests.get(url, headers=__class__.CANVAS_HEADER)
		response.raise_for_status()
		return response

	@staticmethod
	def call_canvas_api(url):
		try:
			response = __class__.canvas_get(url)
			yield response.json()
			
			while 'next' in response.links:  
				response = __class__.canvas_get(response.links['next']['url'])
				yield response.json()

		except Exception as e:
			print('Error', e)
			pass

	@staticmethod
	def transaction(canvas_student_name, student_id, sem_name, course_code, trying_sequence):
		print('Inserted data: ',student_id, sem_name, course_code, trying_sequence)

		try:
			with transaction.atomic():

				student, created = Student.objects.get_or_create(student_id=student_id,
					defaults={'student_name':canvas_student_name, 'batch':Batch.objects.get(batch_name=S.BATCH_NAME)}
				)

				s_r = StudentRegistration.objects.update_or_create(student=student, course_code=course_code,
					semester=Semester.objects.get(canvas_sem_name=sem_name)
				)

		except Exception as e:
			raise Exception(
				'Error: %s|%s|%s|%s|%s'%(trying_sequence, student_id, sem_name, course_code, e)
				) from e

	@staticmethod
	def insert_data(canvas_student_name, canvas_student_email, sem_name, course_code):
		student_id = canvas_student_email.split('@')[0]
		program = Program.objects.get(program_code__iexact=student_id[4:8])

		if program.program_type == Program.CERTIFICATION:
			sem_name = S.SEMESTER_NAME

		try:
			__class__.transaction(canvas_student_name, student_id, sem_name, course_code, 'first try')

		except Exception as e:
			__class__.transaction(canvas_student_name, student_id, sem_name, course_code, 'Second try')

		return canvas_student_email

	@staticmethod
	def get_data(sem, ces):
		errors = []
		inserted = []
		exclude_full_name = ('courseware', 'dissertation', 'merged')

		sem_code = sem.canvas_sem_name
		courses_canvas_data = { 
			'%s_%s' %(sem_code, c.split(':')[0]): (sem_code, c.split(':')[0]) for c in ces.iterator()
		}

		try:
		
			for accounts in __class__.call_canvas_api(__class__.CANVAS_ACCOUNT_ID_URI):
				for account in accounts:
					for courses in __class__.call_canvas_api(__class__.CANVAS_COURSES_URI.format(account_id=account['id'])):
						for course in courses:
							match = (
								not any(map(lambda s: s in course['name'].lower(), exclude_full_name)) and 
								course['course_code'] in courses_canvas_data
							)
							if match:
								for students in __class__.call_canvas_api(__class__.CANVAS_COURSE_USERS_URI.format(course_id=course['id'])):
									for canvas_student in students:
										
										try:
											 # Note: canvas_student['sis_user_id'] is used instead of canvas_student['email'] as we encountered data which does not contain 
											 #       email field in data pulled or email is not the bits-wilp email
											inserted.append(
												__class__.insert_data(canvas_student['name'],canvas_student['sis_user_id'], *courses_canvas_data[course['course_code']])
											)
											
										except Exception as e:
											print('Error', e)
											errors.append('shortname:%s, student:%s, error:%s' %(course['course_code'], 
												canvas_student['email'], e))
			
		except Exception as e:
			print('Outer Error', e)
			dslogs = DataSyncLogs.objects.create(
			source='canvas', records_pulled=len(set(inserted)),
			status=DataSyncLogs.FAILED,
			parameters='<br><br>Success:<br>%s<br><br>Failed:<br>%s' %(', '.join(set(inserted)), ', '.join(set(errors)))
		)
		else:
		
			dslogs = DataSyncLogs.objects.create(
				source='canvas', records_pulled=len(set(inserted)),
				status=DataSyncLogs.SUCCESS,
				parameters='filtered on:<br>%s<br>Success:<br>%s<br>Failed:<br>%s' %(
					', '.join(courses_canvas_data.keys()),
					', '.join(set(inserted) or ['No Data Found',]), 
					', '.join(set(errors) or ['No Data Found',])
				)
			)

		return dslogs.parameters