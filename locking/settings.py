from django.conf import settings

EXPIRATION_SECONDS = getattr(settings, 'LOCKING_EXPIRATION_SECONDS', 300)
PING_SECONDS = getattr(settings, 'LOCKING_PING_SECONDS', 15)
