from __future__ import absolute_import, unicode_literals, division

import json

from django import test
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from .models import BlogArticle
from .utils import LockingClient, user_factory
from ..models import Lock
from ..settings import DEFAULT_EXPIRATION_SECONDS

__all__ = ('TestAPI', )


class TestAPI(test.TestCase):

    def setUp(self):
        self.blog_article = BlogArticle.objects.create(title="title", content="content")
        self.blog_article_2 = BlogArticle.objects.create(title="title 2", content="content 2")
        self.article_content_type = ContentType.objects.get_for_model(BlogArticle)

    def test_login_required(self):
        """Locking API should require login for all methods"""
        client = LockingClient(self.blog_article)
        for method in ['get', 'post', 'put', 'delete']:
            # Redirect to login page
            self.assertEqual(getattr(client, method)().status_code, 302)

    def test_permission_required(self):
        """Locking API should require correct permissions for all methods"""
        client = LockingClient(self.blog_article)
        client.login_new_user(has_perm=False)
        for method in ['get', 'post', 'put', 'delete']:
            self.assertEqual(getattr(client, method)().status_code, 401)

    def test_get(self):
        """GET requests to API should return locks correctly"""
        client = LockingClient(self.blog_article)
        client.login_new_user()
        rsp = client.get()
        self.assertEqual(rsp.status_code, 200)
        self.assertEqual(Lock.objects.count(), 0)
        self.assertEqual(json.loads(rsp.content.decode()), [])
        user, _ = user_factory(self.blog_article)
        Lock.objects.create(locked_by=user,
                            content_type=self.article_content_type,
                            object_id=self.blog_article.pk)
        rsp = client.get()
        result = json.loads(rsp.content.decode())

        self.assertEqual(len(result), 1)
        locked_by = result[0]['locked_by']
        self.assertEqual(locked_by, {'username': user.username, 'first_name': user.first_name,
            'last_name': user.last_name, 'email': user.email})
        date_expires = timezone.datetime.strptime(result[0]['date_expires'], "%Y-%m-%dT%H:%M:%S.%fz")
        date_expires = timezone.make_aware(date_expires, timezone.get_default_timezone())
        self.assertAlmostEqual(date_expires,
                               timezone.now() + timezone.timedelta(seconds=DEFAULT_EXPIRATION_SECONDS),
                               delta=timezone.timedelta(seconds=30))

    def test_post_creates_lock(self):
        """POST requests to API should create a lock if it does already not exist"""
        client = LockingClient(self.blog_article)
        client.login_new_user()
        self.assertEqual(client.post().status_code, 200)
        self.assertEqual(Lock.objects.count(), 1)
        self.assertEqual(
            Lock.objects.values_list('content_type', 'object_id', 'locked_by')[0],
            (self.article_content_type.pk, self.blog_article.pk, client.user.pk))

    def test_post_extends_lock(self):
        """POST request to API should extend expiration date of existing lock by that user"""
        client = LockingClient(self.blog_article)
        client.login_new_user()
        Lock.objects.create(locked_by=client.user,
                            content_type=self.article_content_type,
                            object_id=self.blog_article.pk)

        date_expires_1 = Lock.objects.first().date_expires
        self.assertEqual(client.post().status_code, 200)
        self.assertEqual(Lock.objects.count(), 1)
        date_expires_2 = Lock.objects.first().date_expires
        self.assertGreater(date_expires_2, date_expires_1)

    def test_post_from_non_owner_doesnt_overwrite_lock(self):
        """POST from 2nd user to existing endpoint should not overwrite existing users lock"""
        user, _ = user_factory(self.blog_article)
        Lock.objects.create(locked_by=user,
                            content_type=self.article_content_type,
                            object_id=self.blog_article.pk)
        client = LockingClient(self.blog_article)
        client.login_new_user()

        self.assertEqual(client.post().status_code, 409)
        self.assertEqual(Lock.objects.count(), 1)
        locked_by = Lock.objects.values_list('locked_by', flat=True)[0]
        self.assertEqual(locked_by, user.pk)

    def test_put_new_lock(self):
        """PUT requests should always update lock, even if someone else owned it"""
        client = LockingClient(self.blog_article)
        client.login_new_user()
        self.assertEqual(client.put().status_code, 200)
        self.assertEqual(Lock.objects.filter(object_id=self.blog_article.id).count(), 1)

    def test_put_existing_lock(self):
        """PUT requests should always update lock, even if someone else owned it"""
        client = LockingClient(self.blog_article)
        client.login_new_user()
        user, _ = user_factory(self.blog_article)
        lock = Lock.objects.create(locked_by=user,
                                   content_type=self.article_content_type,
                                   object_id=self.blog_article.pk)
        self.assertEqual(client.put().status_code, 200)
        self.assertEqual(Lock.objects.get(id=lock.pk).locked_by.pk, client.user.pk)

    def test_delete(self):
        """DELETE request to API should remove locks made by that user"""
        client = LockingClient(self.blog_article)
        client.login_new_user()
        Lock.objects.create(locked_by=client.user,
                            content_type=self.article_content_type,
                            object_id=self.blog_article.pk)
        self.assertEqual(client.delete().status_code, 204)
        self.assertEqual(Lock.objects.count(), 0)

    def test_delete_nonexistent_lock(self):
        """Calling delete on an already delete lock should not raise an exception"""
        client = LockingClient(self.blog_article)
        client.login_new_user()
        self.assertEqual(client.delete().status_code, 204)

    def test_delete_for_other_user(self):
        """DELETE request to API should not remove lock made by other users"""
        client = LockingClient(self.blog_article)
        client.login_new_user()
        other_user, _ = user_factory(self.blog_article)
        Lock.objects.create(locked_by=other_user,
                            content_type=self.article_content_type,
                            object_id=self.blog_article.pk)
        self.assertEqual(client.delete().status_code, 401)
        self.assertEqual(Lock.objects.count(), 1)

    @test.override_settings(LOCKING_DELETE_TIMEOUT_SECONDS=5)
    def test_delete_with_DELETE_TIMEOUT_SECONDS_settings(self):
        """If `LOCKING_DELETE_TIMEOUT_SECONDS` is specified, locks are expired not deleted"""
        client = LockingClient(self.blog_article)
        client.login_new_user()
        lock = Lock.objects.create(locked_by=client.user,
                                   content_type=self.article_content_type,
                                   object_id=self.blog_article.pk)
        self.assertEqual(client.delete().status_code, 204)
        lock_expiration = Lock.objects.filter(pk=lock.pk).values_list('date_expires', flat=True)[0]
        expected_expiration = timezone.now() + timezone.timedelta(seconds=5)     
        self.assertAlmostEqual(lock_expiration, expected_expiration, delta=timezone.timedelta(seconds=0.5))
