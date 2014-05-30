from __future__ import absolute_import, unicode_literals, division

from django.conf import settings

EXPIRATION_SECONDS = getattr(settings, 'LOCKING_EXPIRATION_SECONDS', 180)
PING_SECONDS = getattr(settings, 'LOCKING_PING_SECONDS', 30)
