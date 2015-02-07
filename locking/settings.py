from __future__ import absolute_import, unicode_literals, division

from django import VERSION
from django.conf import settings

EXPIRATION_SECONDS = getattr(settings, 'LOCKING_EXPIRATION_SECONDS', 180)
PING_SECONDS = getattr(settings, 'LOCKING_PING_SECONDS', 15)
SHARE_ADMIN_JQUERY = getattr(settings, 'LOCKING_SHARE_ADMIN_JQUERY', VERSION > (1, 6))
