test:
	DJANGO_SETTINGS_MODULE=tests.settings django-admin.py collectstatic --link --noinput
	DJANGO_SETTINGS_MODULE=tests.settings django-admin.py test tests
