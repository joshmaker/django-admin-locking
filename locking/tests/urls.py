from __future__ import absolute_import, unicode_literals, division

from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin

__all__ = ('urlpatterns', )

admin.autodiscover()
urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^locking/', include('locking.urls'))
)
if settings.GRAPPELLI_INSTALLED:
    urlpatterns = patterns('', (r'^grappelli/', include('grappelli.urls'))) + urlpatterns
