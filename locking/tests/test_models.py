from django import test
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from .models import BlogArticle
from .utils import user_factory
from ..models import Lock

__all__ = ['TestLock', ]


class TestLock(test.TestCase):

    def setUp(self):
        self.user, _ = user_factory()
        self.article1 = BlogArticle.objects.create(title="Test", content="Test")
        self.article2 = BlogArticle.objects.create(title="Test", content="Test")
        self.article_ct = ContentType.objects.get_for_model(BlogArticle)
        self.past = timezone.now() - timezone.timedelta(minutes=10)

    def test_delete_expired(self):
        Lock.objects.create(locked_by=self.user, content_type=self.article_ct,
            object_id=self.article1.pk)
        lock = Lock.objects.create(locked_by=self.user, content_type=self.article_ct,
            object_id=self.article2.pk)
        Lock.objects.filter(pk=lock.pk).update(date_expires=self.past)

        Lock.objects.delete_expired()
        try:
            Lock.objects.get(object_id=self.article1.pk)
        except Lock.DoesNotExist:
            self.fail('Lock with date in the future mistakenly deleted')
        self.assertRaises(Lock.DoesNotExist, Lock.objects.get, object_id=self.article2.pk)

    def test_is_locked_unexpired(self):
        Lock.objects.create(locked_by=self.user, content_type=self.article_ct,
            object_id=self.article1.pk)
        self.assertTrue(Lock.is_locked(self.article1))

    def test_is_locked_expired(self):
        lock = Lock.objects.create(locked_by=self.user, content_type=self.article_ct,
            object_id=self.article1.pk)
        Lock.objects.filter(pk=lock.pk).update(date_expires=self.past)
        self.assertFalse(Lock.is_locked(self.article1))

    def test_lock_unexpired(self):
        Lock.objects.create(locked_by=self.user, content_type=self.article_ct,
            object_id=self.article1.pk)
        new_user, _ = user_factory()
        self.assertRaises(Lock.ObjectLockedError, Lock.objects.lock_object_for_user,
            obj=self.article1, user=new_user)
        lock = Lock.objects.get(object_id=self.article1.pk)
        self.assertEqual(lock.locked_by.pk, self.user.pk)

    def test_lock_expired(self):
        lock = Lock.objects.create(locked_by=self.user, content_type=self.article_ct,
            object_id=self.article1.pk)
        Lock.objects.filter(pk=lock.pk).update(date_expires=self.past)
        new_user, _ = user_factory()
        Lock.objects.lock_object_for_user(obj=self.article1, user=new_user)
        lock = Lock.objects.get(object_id=self.article1.pk)
        self.assertEqual(lock.locked_by.pk, new_user.pk)

    def test_is_locked(self):
        article = self.article1
        self.assertFalse(Lock.is_locked(article))
        Lock.objects.create(locked_by=self.user, content_type=self.article_ct, object_id=article.pk)
        self.assertTrue(Lock.is_locked(article))
