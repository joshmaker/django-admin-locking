# Django Admin Locking

[![build-status-image]][travis] [![coveralls-status-image]][coveralls]

Prevents users from overwriting each others changes in Django.

## Requirement

Django Admin Locking is tested in the following environments

* Python (2.7, 3.4)
* Django (1.4, 1.5, 1.6, 1.7)

## Installation

Add `'locking'` to your `INSTALLED_APPS` setting.

```python
INSTALLED_APPS = (
    ...
    'locking',
)
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

Locking Admin offers the following variables for customization in your `settings.py`:

* `LOCKING_EXPIRATION_SECONDS` - Time in seconds that an object will stay locked for without a 'ping' from the server. Defaults to 180.
* `LOCKING_PING_SECONDS` - Time in seconds between 'pings' to the server with a request to maintain or gain a lock on the current form. Defaults to 15.
* `LOCKING_SHARE_ADMIN_JQUERY` - Should locking use instance of jQuery used by the admin or should it use it's own bundled version of jQuery? Useful because older versions of Django do not come with a new enough version of jQuery for admin locking. Defaults to True for Django 1.6 and later, and False for older versions of Django.


## Testing

Running the included test suite requires the following additional requirements:

* Selenium
* PhantomJS


[build-status-image]: https://api.travis-ci.org/joshmaker/django-admin-locking.svg?branch=master
[travis]: https://travis-ci.org/joshmaker/django-admin-locking/?branch=master
[coveralls-status-image]: https://coveralls.io/repos/joshmaker/django-admin-locking/badge.svg?branch=master
[coveralls]: https://coveralls.io/r/joshmaker/django-admin-locking?branch=master
