DJANGO_SETTINGS_MODULE := healthpoints.settings_local

all:
	echo "nothing to be done"

run:
	python manage.py runserver_plus

test:
	python manage.py test
	
clean_pyc:
	find . -name \*.pyc -delete
	find . -name \*.pyo -delete

collect_static:
	python manage.py collectstatic -l --noinput

compilemessages:
	python manage.py compilemessages

makemessages:
	python manage.py makemessages -a

makemessagesjs:
	python manage.py makemessages -d djangojs -a

migrate:
	python manage.py migrate
