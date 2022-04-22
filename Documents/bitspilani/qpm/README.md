Requirement:
	- Python 3.7
	- Mysql Database.



Git Configuration:
	# contact admin for git private key. 
	- git config --global user.name "<username>"
	- git config --global user.email "<email>"



Getting git repositories:
	- git clone git@gitlab.com:bits-pilani/qpm.git




Execution:	
	- cd qpm/qp
	- source/bin/activate 
	- pipenv update
	- python manage.py collectstatic
	- python manage.py runserver
