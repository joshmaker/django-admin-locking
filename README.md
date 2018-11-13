# Django Admin Locking

[![build-status-image]][travis] [![coveralls-status-image]][coveralls]

Prevents users from overwriting each others changes in Django.

## Requirement

Django Admin Locking is tested in the following environments

* Python (2.7, 3.4, 3.5, 3.6, 3.7)
* Django (1.11, 2.0, 2.1)

## Installation

Add `'locking'` to your `INSTALLED_APPS` setting.

```python
INSTALLED_APPS = (
    ...
    'locking',
)
```

Add the required URL pattern:

```python
url(r'^locking/', include('locking.urls')),
```

## Usage

To enable locking for a `ModelAdmin`:

```python
from django.contrib import admin
from locking.admin import LockingAdminMixin
from my_project.mt_models import MyModel

class MyModelAdmin(LockingAdminMixin, admin.ModelAdmin):
     pass

admin.site.register(MyModel, MyModelAdmin)
```

The `LockingAdminMixin` will automatically add a new column that displays which rows are currently locked. To manually place this column add `is_locked` to the admin's `list_display` property.

Locking Admin offers the following variables for customization in your `settings.py`:

* `LOCKING_EXPIRATION_SECONDS` - Time in seconds that an object will stay locked for without a 'ping' from the server. Defaults to `180`.
* `LOCKING_PING_SECONDS` - Time in seconds between 'pings' to the server with a request to maintain or gain a lock on the current form. Defaults to `15`.
* `LOCKING_SHARE_ADMIN_JQUERY` - Should locking use instance of jQuery used by the admin or should it use it's own bundled version of jQuery? Useful because older versions of Django do not come with a new enough version of jQuery for admin locking. Defaults to `True`.
* `LOCKING_DB_TABLE` - Used to override the default locking table name (`locking_lock`)
* `LOCKING_DELETE_TIMEOUT_SECONDS` - If not zero, locks will not be deleted immediately when a user leaves an admin form, but will instead be set to expire in the specified number of seconds. Specifying this setting can help avoid the following situation: a user hits 'save and continue' on a form, causing the page to reload. If locks are deleted instantly, someone else might grab the lock before the form loads again. If this value is specified, it should be set to the approximate time it takes a form to save (generally a few seconds). Defaults to `0`.


## Cleaning up expired locks

Overtime, you may find it necessary to remove expired locks from the database. This can be done with the following management command

```
$ python manage.py delete_expired_locks
```

If you have a non-zero specified for `LOCKING_DELETE_TIMEOUT_SECONDS` in your settings, you should setup a reoccurring Cron or Celery task to automatically run this management command on a regular interval.


## Testing

You will need to install the [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/downloads)
necessary to interface with your version of Chrome. You must ensure that the driver
app resides somewhere on your `$PATH`.


Running the included test suite requires the following additional requirements:

* tox
* tox-venv

```
$ pip install tox tox-venv
```

Additionally, for all tests to succeed, you will need Python 2.7 and 3.4-3.7 installed.

## JavaScript plugins for advanced widgets

By default, form field widgets are disabled by adding the attribute `disabled = disabled` to all `inputs`. If you are using a custom widget, such as a WYSIWYG editor, you may need to register a locking plugin to ensure it is correctly locked and unlocked.

Plugin registration takes the following form:

```javascript
window.locking.LockingFormPlugins.register({
    'enable': function(form) {  /* Enabled my custom widget */ },
    'disable': function(form) {  /* Disable my custom widget */ }
})
```

For an example, look at the [included plugin](locking/static/locking/js/locking.ckeditor.js) for the CKEditor WYSIYG editor.

## Compatibility Notes

This app is compatible the popular admin theme [django-grappelli](https://django-grappelli.readthedocs.org/)

## License

This code is licensed under the Simplified BSD License. View the LICENSE file under the root directory for complete license and copyright information.

[build-status-image]: https://api.travis-ci.org/theatlantic/django-admin-locking.svg?branch=master
[travis]: https://travis-ci.org/theatlantic/django-admin-locking/?branch=master
[coveralls-status-image]: https://coveralls.io/repos/theatlantic/django-admin-locking/badge.svg?branch=master
[coveralls]: https://coveralls.io/r/theatlantic/django-admin-locking?branch=master
