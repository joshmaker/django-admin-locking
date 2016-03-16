from __future__ import absolute_import, unicode_literals, division

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import staleness_of

from .models import BlogArticle
from .utils import user_factory
from ..models import Lock

__all__ = ('TestAdmin', 'TestLiveAdmin')


class TestAdmin(TestCase):

    def setUp(self):
        self.blog_article = BlogArticle.objects.create(title="title", content="content")
        user, password = user_factory(BlogArticle)
        self.client.login(username=user.username, password=password)
        self.user = user

    def test_changelist_loads(self):
        """The change list view for a lockable object should load with status 200"""
        url = reverse('admin:locking_blogarticle_changelist')
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_addform_loads(self):
        """The add form view for a lockable object should load with status 200"""
        url = reverse('admin:locking_blogarticle_add')
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_changeform_loads(self):
        """The change form view for a lockable object should load with status 200"""
        url = reverse('admin:locking_blogarticle_change', args=(self.blog_article.pk, ))
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_save_unlocked(self):
        """Unlocked objects should update correctly when saved"""
        url = reverse('admin:locking_blogarticle_change', args=(self.blog_article.pk, ))
        self.client.post(url, {'title': 'updated title', 'content': 'updated content'})
        article = BlogArticle.objects.get(pk=self.blog_article.pk)
        self.assertEqual(article.title, 'updated title')
        self.assertEqual(article.content, 'updated content')

    def test_save_locked_by_user(self):
        """Locked objects should update correctly for the user who locks them"""
        Lock.objects.lock_object_for_user(self.blog_article, self.user)
        url = reverse('admin:locking_blogarticle_change', args=(self.blog_article.pk, ))
        self.client.post(url, {'title': 'updated title', 'content': 'updated content'})
        article = BlogArticle.objects.get(pk=self.blog_article.pk)
        self.assertEqual(article.title, 'updated title')
        self.assertEqual(article.content, 'updated content')

    def test_save_locked_by_other_user(self):
        """Locked objects should *not* update when another user saves them"""
        other_user, _ = user_factory()
        Lock.objects.lock_object_for_user(self.blog_article, other_user)
        url = reverse('admin:locking_blogarticle_change', args=(self.blog_article.pk, ))
        article = BlogArticle.objects.get(pk=self.blog_article.pk)
        self.client.post(url, {'title': 'updated title', 'content': 'updated content'})
        self.assertEqual(article.title, 'title')
        self.assertEqual(article.content, 'content')

    def test_delete_unlocked(self):
        """Unlocked objects should delete correctly"""
        url = reverse('admin:locking_blogarticle_delete', args=(self.blog_article.pk, ))
        self.client.post(url, {'post': 'yes'})
        self.assertEqual(BlogArticle.objects.count(), 0)

    def test_delete_locked_by_user(self):
        """Locked objects should delete correctly for the user who locked them"""
        Lock.objects.lock_object_for_user(self.blog_article, self.user)
        url = reverse('admin:locking_blogarticle_delete', args=(self.blog_article.pk, ))
        self.client.post(url, {'post': 'yes'})
        self.assertEqual(BlogArticle.objects.count(), 0)

    def test_delete_locked_by_other_user(self):
        """Locked objects should *not* be deleted by other users"""
        other_user, _ = user_factory()
        Lock.objects.lock_object_for_user(self.blog_article, other_user)
        url = reverse('admin:locking_blogarticle_delete', args=(self.blog_article.pk, ))
        self.client.post(url, {'post': 'yes'})
        self.assertEqual(BlogArticle.objects.count(), 1)


class TestLiveAdmin(StaticLiveServerTestCase):

    def _load(self, url_name, *args, **kwargs):
        url = self.live_server_url + reverse(url_name, args=args, kwargs=kwargs)
        self.browser.get(url)
        self._wait_until_page_loaded()

    def _login(self, *args, **kwargs):
        self._load(*args, **kwargs)
        self.browser.find_element_by_id("id_username").send_keys(self.user.username)
        self.browser.find_element_by_id("id_password").send_keys(self.password)
        self.browser.find_element_by_xpath('//input[@value="Log in"]').click()

    def _wait_until(self, callback, msg=None):
        WebDriverWait(self.browser, 10).until(callback, msg)

    def _wait_until_page_loaded(self):
        self._wait_until(lambda b: b.find_element_by_tag_name('body'))

    def _wait_for_ajax(self):
        self._wait_until(
            lambda b: b.execute_script("return !!window.locking"),
            "Timeout waiting for window.locking")
        self._wait_until(
            lambda b: b.execute_script("return !locking.ajax.has_pending()"),
            "Timeout waiting for AJAX request")

    def _wait_for_el(self, selector):
        self._wait_until(
            lambda b: b.execute_script("return document.querySelector('%s')" % selector))

    def assert_no_js_errors(self):
        errors = self.browser.execute_script("return window.locking_test.errors")
        self.assertEqual(len(errors), 0, 'JavaScript Errors: "%s"' % '. '.join(errors))

    def setUp(self):
        # Create test models
        self.blog_article = BlogArticle.objects.create(title="title", content="content")
        self.blog_article_2 = BlogArticle.objects.create(title="title 2", content="content 2")

        # Instantiate and login Selenium browser
        self.browser = webdriver.PhantomJS()
        self.browser.set_window_size(1120, 550)
        self.browser.set_page_load_timeout(10)
        self.user, self.password = user_factory(BlogArticle)

    def tearDown(self):
        self.browser.quit()

    def test_addform(self):
        """Add forms should not have disabled inputs or JavaScript errors"""
        self._login('admin:locking_blogarticle_add')
        self._wait_for_ajax()
        self.assert_no_js_errors()
        self.assertFalse(self.browser.find_element_by_id('id_title').get_attribute('disabled'))
        self.assertFalse(self.browser.find_element_by_id('id_content').get_attribute('disabled'))

    def test_changeform_locks_for_user(self):
        """When visiting an unlocked page, a new lock should be created and the form should be editable"""
        self._login('admin:locking_blogarticle_change', self.blog_article.pk)
        self._wait_for_ajax()
        self.assert_no_js_errors()

        # Form should be editable
        self.assertFalse(self.browser.find_element_by_id('id_title').get_attribute('disabled'))
        self.assertFalse(self.browser.find_element_by_id('id_content').get_attribute('disabled'))

        # Check that lock was created
        locks = Lock.objects.for_object(self.blog_article)
        self.assertEqual(len(locks), 1)
        self.assertEqual(locks[0].locked_by.pk, self.user.pk)

    def test_changeform_unlocks_for_user(self):
        self._login('admin:locking_blogarticle_change', self.blog_article.pk)
        self._wait_for_ajax()
        self.assert_no_js_errors()
        self._load('admin:locking_blogarticle_changelist')

        # Check that lock was deleted
        locks = Lock.objects.for_object(self.blog_article)
        self.assertEqual(len(locks), 0)

    def test_changeform_locked_by_other_user(self):
        other_user, _ = user_factory(model=BlogArticle)
        Lock.objects.force_lock_object_for_user(self.blog_article, other_user)

        self._login('admin:locking_blogarticle_change', self.blog_article.pk)
        self._wait_for_ajax()
        self._wait_for_el('#locking-warning')
        self.assert_no_js_errors()

        # Should display who has locked the form
        self.assertTrue(other_user.username in self.browser.find_element_by_id('locking-warning').text)

        # Form should not be editable
        self.assertTrue(self.browser.find_element_by_id('id_title').get_attribute('disabled'))
        self.assertTrue(self.browser.find_element_by_id('id_content').get_attribute('disabled'))

        # Check that lock was not overwritten
        locks = Lock.objects.for_object(self.blog_article)
        self.assertEqual(len(locks), 1)
        self.assertEqual(locks[0].locked_by.pk, other_user.pk)

    def test_changeform_does_not_unlock_for_user(self):
        """Leaving a page locked by another user should not unlock it"""
        other_user, _ = user_factory(model=BlogArticle)
        Lock.objects.force_lock_object_for_user(self.blog_article, other_user)

        self._login('admin:locking_blogarticle_change', self.blog_article.pk)
        self._wait_for_ajax()
        self.assert_no_js_errors()
        self._load('admin:locking_blogarticle_changelist')

        # Check that lock was not deleted
        locks = Lock.objects.for_object(self.blog_article)
        self.assertEqual(len(locks), 1)
        self.assertEqual(locks[0].locked_by.pk, other_user.pk)

    def test_changeform_does_unlock_for_user(self):
        """Clicking the 'remove lock' button should take over the lock"""
        other_user, _ = user_factory(model=BlogArticle)
        Lock.objects.force_lock_object_for_user(self.blog_article, other_user)
        self._login('admin:locking_blogarticle_change', self.blog_article.pk)
        self._wait_for_el('#locking-take-lock')
        self.assert_no_js_errors()

        self.browser.execute_script('window.locking.lockingFormInstance.hasHadLock = true')
        self.browser.find_element_by_id('locking-take-lock').click()
        self._wait_until(
            lambda b: b.execute_script("return (window.locking_test.confirmations > 0)"))
        lock = Lock.objects.for_object(self.blog_article)[0]
        self.assertEqual(lock.locked_by.pk, self.user.pk)

    def test_changeform_does_reload_and_unlock_for_user(self):
        """Clicking the 'remove lock' button should take over the lock"""
        other_user, _ = user_factory(model=BlogArticle)
        Lock.objects.force_lock_object_for_user(self.blog_article, other_user)
        self._login('admin:locking_blogarticle_change', self.blog_article.pk)
        self._wait_for_el('#locking-take-lock')
        self.assert_no_js_errors()

        body_el = self.browser.find_element_by_tag_name('body')
        self.browser.find_element_by_id('locking-take-lock').click()

        # ensure the page has reloaded
        WebDriverWait(self.browser, 10).until(staleness_of(body_el))
        self._wait_until_page_loaded()

        lock = Lock.objects.for_object(self.blog_article)[0]
        self.assertEqual(lock.locked_by.pk, self.user.pk)

    def test_save_locked_form(self):
        """Users should not be able to get around saving locked forms"""
        other_user, _ = user_factory(BlogArticle)
        Lock.objects.force_lock_object_for_user(user=other_user, obj=self.blog_article)
        old_title = BlogArticle.objects.filter(pk=self.blog_article.pk).values_list('title', flat=True)[0]

        self._login('admin:locking_blogarticle_change', self.blog_article.pk)
        old_page_id = self.browser.find_element_by_tag_name('html').id
        self.browser.execute_script("document.getElementsByName('csrfmiddlewaretoken')[0].removeAttribute('disabled')")
        self.browser.execute_script("document.getElementById('id_title').value = 'Edited Title'")
        self.browser.execute_script("document.getElementById('blogarticle_form').submit()")

        # Wait for the page to reload
        self._wait_until(lambda b: b.find_element_by_tag_name('html').id != old_page_id)
        self._wait_until_page_loaded()
        self.assertTrue('locked by' in self.browser.page_source)
        new_title = BlogArticle.objects.filter(pk=self.blog_article.pk).values_list('title', flat=True)[0]

        # The title should not have changed
        self.assertEqual(old_title, new_title)

    def test_locked_form_loses_lock(self):
        self._login('admin:locking_blogarticle_change', self.blog_article.pk)
        self._wait_for_ajax()

        other_user, _ = user_factory(BlogArticle)
        Lock.objects.force_lock_object_for_user(user=other_user, obj=self.blog_article)

        self._wait_until(
            lambda b: b.execute_script("return (window.locking_test.alerts > 0)"),
            "Lock lost alert never triggered")
        self.assertTrue(self.browser.find_element_by_id('id_title').get_attribute('disabled'))
        self.assertTrue(self.browser.find_element_by_id('id_content').get_attribute('disabled'))

    def test_changelist_shows_lock(self):
        """The correct article should be listed as locked on the changelist view"""
        other_user, _ = user_factory(model=BlogArticle)
        Lock.objects.force_lock_object_for_user(self.blog_article, other_user)

        self._login('admin:locking_blogarticle_changelist')
        self.assert_no_js_errors()
        elem_1 = self.browser.find_element_by_id('locking-%s' % self.blog_article.pk)
        elem_2 = self.browser.find_element_by_id('locking-%s' % self.blog_article_2.pk)
        self.assertTrue('locked' in elem_1.get_attribute('class'))
        self.assertFalse('locked' in elem_2.get_attribute('class'))

    def test_unlock_from_changelist(self):
        other_user, _ = user_factory(model=BlogArticle)
        Lock.objects.force_lock_object_for_user(self.blog_article, other_user)
        self._login('admin:locking_blogarticle_changelist')
        lock_icon = self.browser.find_element_by_id('locking-%s' % self.blog_article.pk)
        old_page_id = self.browser.find_element_by_tag_name('html').id
        lock_icon.click()
        self._wait_until(
            lambda b: b.find_element_by_tag_name('html').id != old_page_id,
            "Wait for page to reload")
        self._wait_until_page_loaded()
        self._wait_until(
            lambda b: b.execute_script("return (window.locking_test.confirmations > 0)"),
            "Wait for confirmation modal window")
        self._wait_for_ajax()

        lock = Lock.objects.for_object(self.blog_article)[0]
        self.assertEqual(lock.locked_by.pk, self.user.pk)
