from __future__ import absolute_import, unicode_literals, division

from django.conf.urls import url

from .api import LockAPIView

__all__ = ('urlpatterns', )

urlpatterns = [
    url(r'api/lock/(?P<app>[\w-]+)/(?P<model>[\w-]+)/$',
        LockAPIView.as_view(), name='locking-api'),

    url(r'api/lock/(?P<app>[\w-]+)/(?P<model>[\w-]+)/(?P<object_id>\d+)/$',
        LockAPIView.as_view(), name='locking-api'),
]
