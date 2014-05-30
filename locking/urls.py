from __future__ import absolute_import, unicode_literals, division

from django.conf.urls.defaults import patterns, url


url_patterns = patterns('locking.views',
    url(r'api/lock/(?P<app>[\w-]+)/(?P<model>[\w-]+)/(?P<object_id>\d+)/$', name='lock-rest-api'),
)
