from master.utils.storage import document_extract_file
from PIL import Image
# import face_recognition
import numpy as np
import cv2
def check_valid_image(student):
	try:
		with Image.open(document_extract_file(student)) as image:
			if image.width == 150 and image.height == 150:
				return 'crop_not_required'
			else:
				return 'crop_required'
	except:
		return 'incorrect_format'


def check_for_face(image_data_as_matrix):
	test_image_gray = cv2.cvtColor(image_data_as_matrix, cv2.COLOR_BGR2GRAY)
	face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
	faces_rects = face_cascade.detectMultiScale(test_image_gray, scaleFactor=1.2, minNeighbors=5)
	if len(faces_rects)==1:
		return True
	else:
		return False
