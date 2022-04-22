###########################  sca fields
SCA_creation_fields = (
	'Email', 'LastName', 'Gender__c', 'attributes', 'Exam_Location__c', 'Program__c', 'MailingPostalCode',
	'Phone', 'MobilePhone', 'MailingCity', 'MailingState', 'MailingCountry', 'Nationality__c',
	'Application_ID__c', 'Application_Status__c', 'Submitted_Date_time__c', 
	'Current_Employment_Status__c', 'Current_Designation__c', 'Current_Organization__c',
	'Current_Industry__c', 'Work_Location__c', 'Total_Work_Experience__c',
	'Math_Proficiency_Level__c', 'Prior_Student__c', 'Admit_Batch__c', 'Lecture_Mode__c',
	'Coding_Proficiency__c', 'Pre_Selection_Date_Time__c', 'Mentor_Consent__c',
	'Organization_Consent__c', 'Bonafide__c', 'Father_Name__c', 'Mother_Name__c',
	'Prior_Student_ID__c', 'Birthdate', 'Date_of_Joining_Current_Organization__c',
)

SCA_updation_fields = (
	'Email', 'LastName', 'Gender__c', 'attributes', 'Exam_Location__c', 'Program__c', 'MailingPostalCode',
	'Phone', 'MobilePhone', 'MailingCity', 'MailingState', 'MailingCountry', 'Nationality__c',
	'Application_ID__c', 'Application_Status__c', 'Submitted_Date_time__c', 
	'Current_Employment_Status__c', 'Current_Designation__c', 'Current_Organization__c',
	'Current_Industry__c', 'Work_Location__c', 'Total_Work_Experience__c',
	'Math_Proficiency_Level__c', 'Prior_Student__c', 'Admit_Batch__c', 'Lecture_Mode__c',
	'Coding_Proficiency__c', 'Pre_Selection_Date_Time__c', 'Mentor_Consent__c',
	'Organization_Consent__c', 'Bonafide__c', 'Father_Name__c', 'Mother_Name__c',
	'Prior_Student_ID__c', 'Birthdate', 'Date_of_Joining_Current_Organization__c',
) 
###note: SCA_updation_fields variable is example how to create update fields you can create as many fields and 
##  apply in signals.py
##      examples:
        # if creation:
        # 	fields = SCA_creation_fields
        # elif instance.application_status == 'Submitted':
        # 	fields = SCA_updation_fields




###########################   AE fields
AE_creation_fields = ('Email', 'LastName', 'Transfer_Program_Name__c', 
			'Transfer_On__c', 'attributes', 'Application_ID__c',)

###########################   AP fields
AP_creation_fields = ('Email', 'LastName', 'Fee_Amount__c', 'Fee_Paid_Date_Time__c', 
			'Admission_Fee_Payment_Date__c', 'Fee_Payment_Mode__c', 'attributes', 'Application_ID__c',)


###########################   CS fields
CS_creation_fields = ('Email', 'LastName', 'Escalation_Date_Time__c', 'Escalation_Comments__c', 
			'Shortlisted_Date_Time__c', 'Rejection_Comments__c','Shortlisted_Mail_Sent_Date_Time__c',
			'Rejection_Reason__c', 'Acceptance_Declination_Date_Time__c', 'Student_ID__c',
			'Decline_Reason__c', 'Lecture_Start_Date__c', 'Orientation_Date__c',
			'New_application_ID__c', 'attributes','Application_ID__c')

###########################   SCQ fields
SCQ_creation_fields = ('attributes', 'Degree__c', 'Discipline__c', 'College_School__c', 
			'Grade_CGPA__c', 'Application_Id__c', 'Reference_Key__c',
		)

###########################   SCWE fields
SCWE_creation_fields = ('attributes', 'Organization__c', 'Designation__c', 'From__c', 
		'To__c', 'Application_Id__c', 'Reference_Key__c',
		)

###########################   AD fields
AD_creation_fields = ('attributes', 'Name', 'Uploaded_on__c', 'Document_Status__c', 
				'Review_Datetime__c', 'Application_Id__c', 'Reference_Key__c',
				'Rejection_Reason__c',
			)