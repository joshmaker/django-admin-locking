test:
	DJANGO_SETTINGS_MODULE=locking.tests.settings django-admin.py collectstatic --link --noinput
	DJANGO_SETTINGS_MODULE=locking.tests.settings django-admin.py test locking
