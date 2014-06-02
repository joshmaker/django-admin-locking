from __future__ import absolute_import, unicode_literals, division

from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from .settings import EXPIRATION_SECONDS


__all__ = ('Lock', )


class LockingManager(models.Manager):
    def delete_expired(self):
        """Delete all expired locks from the database"""
        self.filter(date_expires__lt=timezone.now()).delete()

    def lock_for_user(self, content_type, object_id, user):
        """
        Try to create a lock on a given instance to a user.

        If a lock does not exist (or has expired) the current user gains a lock
        on this object. If another user already has a valid lock on this object,
        then Lock.ObjectLockedError is raised.

        """

        try:
            lock = self.get(content_type=content_type, object_id=object_id)
        except Lock.DoesNotExist:
            lock = Lock(content_type=content_type, object_id=object_id, locked_by=user)
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
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    objects = LockingManager()

    class Meta:
        unique_together = ('content_type', 'object_id', )
        permissions = (("can_unlock", "Can remove other user's locks"), )

    class ObjectLockedError(Exception):
        pass

    def save(self, *args, **kwargs):
        "Save lock and renew expiration date"
        self.date_expires = timezone.now() + timedelta(seconds=EXPIRATION_SECONDS)
        super(Lock, self).save(*args, **kwargs)

    @property
    def has_expired(self):
        return self.date_expires < timezone.now()

    @classmethod
    def is_locked(cls, instance):
        ct_type = ContentType.objects.get_for_model(instance)
        return cls.objects.filter(content_type=ct_type,
                                  object_id=instance.id,
                                  date_expires__gte=timezone.now()).exists()
