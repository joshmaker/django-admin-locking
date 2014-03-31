from __future__ import absolute_import, unicode_literals

from django.conf.urls.defaults import patterns, url


url_patterns = patterns('locking.views',
    url(r'api/(?P<app>[\w-]+)/(?P<model>[\w-]+)/(?P<object_id>\d+)/lock/$', name='lock'),
    url(r'api/(?P<app>[\w-]+)/(?P<model>[\w-]+)/(?P<object_id>\d+)/unlock/$', name='unlock'),
)
