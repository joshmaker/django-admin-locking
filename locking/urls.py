from __future__ import absolute_import, unicode_literals, division

from django.conf.urls import patterns, url

from .views import LockAPIView


urlpatterns = patterns('',
    url(r'api/lock/(?P<app>[\w-]+)/(?P<model>[\w-]+)(/(?P<object_id>\d+))?/$',
        LockAPIView.as_view(),
        name='locking-api'),
)
