from __future__ import absolute_import, unicode_literals, division

import json
from datetime import datetime, timedelta
from selenium import webdriver

from django import test
try:
    from django.contrib.auth import get_user_model
except ImportError:
    # Django < 1.5
    from django.contrib.auth.models import User
    get_user_model = lambda: User
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

from .models import BlogArticle
from ..models import Lock
from ..settings import EXPIRATION_SECONDS

__all__ = ['TestViews', 'TestAdmin']


def user_factory(model, has_perm=True):
    content_type = ContentType.objects.get_for_model(model)
    username = 'user%d' % datetime.now().microsecond
    email = '%s@example.com' % username
    password = 'p@ssw0rd'
    user = get_user_model().objects.create_user(username, email, password)  # user will have is_staff = False
    user.is_staff = True
    user.save()
    if has_perm:
        codename = 'change_%s' % model._meta.object_name.lower()
        permission = Permission.objects.get(codename=codename, content_type=content_type)
        user.user_permissions.add(permission)
    return user, password


class LockingClient(object):

    def __init__(self, instance):
        self.instance = instance
        self.url = reverse('locking-api', kwargs={
            'app': instance._meta.app_label,
            'model': instance._meta.object_name,
            'object_id': instance.pk,
        })
        self.client = test.Client()
        self.user = None

    def login_new_user(self, *args, **kwargs):
        self.client.logout()
        user, password = user_factory(self.instance, *args, **kwargs)
        self.client.login(username=user.username, password=password)
        self.user = user

    def get(self, *args, **kwargs):
        return self.client.get(self.url, *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.client.post(self.url, *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.client.delete(self.url, *args, **kwargs)


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
        self.assertEqual(json.loads(rsp.content), [])
        user, _ = user_factory(self.blog_article)
        Lock.objects.create(locked_by=user,
                            content_type=self.article_content_type,
                            object_id=self.blog_article.pk)
        rsp = client.get()
        result = json.loads(rsp.content)

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


class TestAdmin(test.LiveServerTestCase):

    def setUp(self):
        self.browsers = []
        self.blog_article = BlogArticle.objects.create(title="title", content="content")
        self.blog_article_2 = BlogArticle.objects.create(title="title 2", content="content 2")

    def get_admin_url(self, instance=None):
        url = '%s/admin/%s/%s/' % (self.live_server_url, BlogArticle._meta.app_label, BlogArticle._meta.object_name.lower())
        if instance:
            return '%s%s/' % (url, instance.pk)
        return url

    def get_browser(self, user, password):
        browser = webdriver.Firefox()
        browser.get(self.get_admin_url())
        browser.find_element_by_id("id_username").send_keys(user.username)
        browser.find_element_by_id("id_password").send_keys(password)
        browser.find_element_by_xpath('//input[@value="Log in"]').click()
        self.browsers.append(browser)
        return browser

    def test_load_article(self):
        user, password = user_factory(BlogArticle)
        user2, password2 = user_factory(BlogArticle)

        browser = self.get_browser(user, password)
        browser2 = self.get_browser(user2, password2)

        # Browser 1 and 2 both load a blog article change form,
        # Browser 1 loads it first, so it is locked for browser 2
        browser.get(self.get_admin_url(self.blog_article))
        self.assertEqual(Lock.objects.filter(object_id=self.blog_article.pk).count(), 1)
        self.assertEqual(Lock.objects.filter(object_id=self.blog_article.pk, locked_by=user.pk).count(), 1)
        browser2.get(self.get_admin_url(self.blog_article))
        self.assertEqual(Lock.objects.filter(object_id=self.blog_article.pk).count(), 1)
        self.assertEqual(Lock.objects.filter(object_id=self.blog_article.pk, locked_by=user.pk).count(), 1)
        self.assertFalse('Form is locked' in browser.page_source)
        self.assertTrue('Form is locked' in browser2.page_source)
        self.assertFalse(browser.find_element_by_id('id_title').get_attribute('disabled'))
        self.assertFalse(browser.find_element_by_id('id_content').get_attribute('disabled'))
        self.assertTrue(browser2.find_element_by_id('id_title').get_attribute('disabled'))
        self.assertTrue(browser2.find_element_by_id('id_content').get_attribute('disabled'))

        # Browser 2 loads the list view page, the correct article is listed as locked
        browser2.get(self.get_admin_url())
        elem_1 = browser2.find_element_by_id('locking-%s' % self.blog_article.pk)
        elem_2 = browser2.find_element_by_id('locking-%s' % self.blog_article_2.pk)

        self.assertTrue('locked' in elem_1.get_attribute('class'))
        self.assertFalse('locked' in elem_2.get_attribute('class'))

        # Browser 1 leaves the blog article change form, it is unlocked and
        # browser 2 is now able to get a lock on it
        browser.get(self.get_admin_url())
        self.assertEqual(Lock.objects.filter(object_id=self.blog_article.pk, locked_by=user.pk).count(), 0)
        browser2.get(self.get_admin_url(self.blog_article))
        self.assertEqual(Lock.objects.filter(object_id=self.blog_article.pk, locked_by=user2.pk).count(), 1)
        self.assertFalse(browser2.find_element_by_id('id_title').get_attribute('disabled'))
        self.assertFalse(browser2.find_element_by_id('id_content').get_attribute('disabled'))

    def tearDown(self):
        for browser in self.browsers:
            browser.quit()
