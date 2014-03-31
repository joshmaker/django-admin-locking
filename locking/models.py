from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .settings import EXPIRATION_SECONDS


__all__ = ('Lock', )


class LockingManager(models.Manager):
    def delete_expired(self):
        """Delete all expired locks from the database"""
        self.filter(expiration__lt=datetime.now()).delete()

    def lock_for_user(self, ct_type, obj_id, user):
        """
        Try to create a lock on a given instance to a user.

        If a lock does not exist (or has expired) the current user gains a lock
        on this object. If another user already has a valid lock on this object,
        then Lock.ObjectLockedError is raised.

        """

        try:
            lock = self.get(content_type=ct_type, object_id=obj_id)
        except Lock.DoesNotExist:
            lock = Lock(content_type=ct_type, object_id=obj_id, user=user)
        else:
            if lock.has_expired:
                lock.locked_by = user
            elif lock.locked_by.id != user.id:
                raise Lock.ObjectLockedError('This object is already locked by another user')

        lock.save()
        return lock


class Lock(models.Model):
    locked_by = models.ForeignKey(settings.AUTH_USER_MODEL)
    date_expires = models.DateTimeField()
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    objects = LockingManager()

    class Meta:
        unique_together = ('content_type', 'object_id', )
        permissions = (("can_unlock", "Can remove other user's locks"), )

    class ObjectLockedError(Exception):
        pass

    def save(self, *args, **kwargs):
        "Save lock and renew expiration date"
        self.date_expires = datetime.now() + timedelta(seconds=EXPIRATION_SECONDS)
        super(Lock, self).save(*args, **kwargs)

    @property
    def has_expired(self):
        return self.date_expires < datetime.now()
