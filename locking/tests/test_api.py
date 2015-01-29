from __future__ import absolute_import, unicode_literals, division

import json
from datetime import datetime, timedelta

from django import test
from django.contrib.contenttypes.models import ContentType

from .models import BlogArticle
from .utils import LockingClient, user_factory
from ..models import Lock
from ..settings import EXPIRATION_SECONDS

__all__ = ['TestViews', ]


class TestViews(test.TestCase):

    def setUp(self):
        self.blog_article = BlogArticle.objects.create(title="title", content="content")
        self.blog_article_2 = BlogArticle.objects.create(title="title 2", content="content 2")
        self.article_content_type = ContentType.objects.get_for_model(BlogArticle)

    def test_dispatch_permissions(self):
        client = LockingClient(self.blog_article)
        self.assertEqual(client.get().status_code, 302)
        client.login_new_user(has_perm=False)
        self.assertEqual(client.get().status_code, 401)

    def test_get(self):
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
        self.assertEqual(locked_by, user.pk)
        date_expires = datetime.strptime(result[0]['date_expires'], "%Y-%m-%dT%H:%M:%S.%fz")
        self.assertAlmostEqual(date_expires,
                               datetime.now() + timedelta(seconds=EXPIRATION_SECONDS),
                               delta=timedelta(seconds=30))

    def test_post(self):

        # POST request should create lock, additional POSTs from that
        # same client should maintain the lock by increasing it's expiration
        client = LockingClient(self.blog_article)
        self.assertEqual(Lock.objects.all().count(), 0)
        client.login_new_user()
        self.assertEqual(client.post().status_code, 200)
        self.assertEqual(Lock.objects.count(), 1)
        date_expires_1 = Lock.objects.first().date_expires
        self.assertEqual(client.post().status_code, 200)
        self.assertEqual(Lock.objects.count(), 1)
        date_expires_2 = Lock.objects.first().date_expires
        self.assertGreater(date_expires_2, date_expires_1)

        # POST from 2nd client to same endpoint should not overwrite existing lock
        client_2 = LockingClient(self.blog_article)
        client_2.login_new_user()
        self.assertEqual(client_2.post().status_code, 401)
        self.assertEqual(Lock.objects.count(), 1)
        locked_by = Lock.objects.values_list('locked_by', flat=True)[0]
        self.assertEqual(locked_by, client.user.pk)

        # POST from 3rd client to new endpoint creates a new lock
        client_3 = LockingClient(self.blog_article_2)
        client_3.login_new_user()
        self.assertEqual(client_3.post().status_code, 200)
        self.assertEqual(Lock.objects.count(), 2)
        locked_by_3 = Lock.objects.filter(object_id=self.blog_article_2.pk).values_list(
            'locked_by', flat=True)[0]
        self.assertEqual(locked_by_3, client_3.user.pk)

    def test_delete(self):
        client = LockingClient(self.blog_article)
        client.login_new_user()
        self.assertEqual(client.delete().status_code, 200)
        Lock.objects.create(locked_by=client.user,
                            content_type=self.article_content_type,
                            object_id=self.blog_article.pk)
        self.assertEqual(client.delete().status_code, 200)
        self.assertEqual(Lock.objects.count(), 0)
