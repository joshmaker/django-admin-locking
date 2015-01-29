from __future__ import absolute_import, unicode_literals, division

from django import test
from django.core.urlresolvers import reverse

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from .models import BlogArticle
from .utils import user_factory
from ..models import Lock

__all__ = ['TestAdmin', ]


class TestAdmin(test.LiveServerTestCase):

    def setUp(self):
        self.browsers = []
        self.blog_article = BlogArticle.objects.create(title="title", content="content")
        self.blog_article_2 = BlogArticle.objects.create(title="title 2", content="content 2")

    def get_admin_url(self, **kwargs):
        if 'instance' in kwargs:
            return self.live_server_url + reverse('admin:locking_blogarticle_change', args=(kwargs['instance'].pk, ))
        elif kwargs.get('add', False):
            return self.live_server_url + reverse('admin:locking_blogarticle_add')
        else:
            return self.live_server_url + reverse('admin:locking_blogarticle_changelist')

    def ajax_complete(self, browser):
        return browser.execute_script("if (!window.locking) return true; return !locking.ajax.has_pending();")

    def wait_for_ajax(self, browser):
        WebDriverWait(browser, 10).until(self.ajax_complete, "Timeout waiting for AJAX request")

    def assert_no_js_errors(self, browser):
        errors = browser.execute_script("return window.locking_test.errors")
        self.assertEqual(len(errors), 0, 'JavaScript Errors: "%s"' % ' '.join(errors))

    def get_browser(self, user, password):
        browser = webdriver.PhantomJS()
        browser.set_window_size(1120, 550)
        browser.get(self.get_admin_url())
        browser.find_element_by_id("id_username").send_keys(user.username)
        browser.find_element_by_id("id_password").send_keys(password)
        browser.find_element_by_xpath('//input[@value="Log in"]').click()
        self.browsers.append(browser)
        return browser

    def test_addform(self):
        user, password = user_factory(BlogArticle)
        browser = self.get_browser(user, password)
        browser.get(self.get_admin_url(add=True))
        self.assert_no_js_errors(browser)
        self.wait_for_ajax(browser)
        self.assertFalse(browser.find_element_by_id('id_title').get_attribute('disabled'))
        self.assertFalse(browser.find_element_by_id('id_content').get_attribute('disabled'))

    def test_changeform(self):
        user, password = user_factory(BlogArticle)
        user2, password2 = user_factory(BlogArticle)

        browser = self.get_browser(user, password)
        browser2 = self.get_browser(user2, password2)

        # Browser 1 and 2 both load a change form,
        # Browser 1 loads it first, so it is locked for browser 2
        browser.get(self.get_admin_url(instance=self.blog_article))
        self.assert_no_js_errors(browser)
        self.wait_for_ajax(browser)
        self.assertEqual(Lock.objects.filter(object_id=self.blog_article.pk).count(), 1)
        self.assertEqual(Lock.objects.filter(object_id=self.blog_article.pk, locked_by=user.pk).count(), 1)
        browser2.get(self.get_admin_url(instance=self.blog_article))
        self.assert_no_js_errors(browser)
        self.wait_for_ajax(browser2)
        self.assertEqual(Lock.objects.filter(object_id=self.blog_article.pk).count(), 1)
        self.assertEqual(Lock.objects.filter(object_id=self.blog_article.pk, locked_by=user.pk).count(), 1)
        self.assertFalse('Form is locked' in browser.page_source)
        self.assertTrue('Form is locked' in browser2.page_source)
        self.assertFalse(browser.find_element_by_id('id_title').get_attribute('disabled'))
        self.assertFalse(browser.find_element_by_id('id_content').get_attribute('disabled'))
        self.assertTrue(browser2.find_element_by_id('id_title').get_attribute('disabled'))
        self.assertTrue(browser2.find_element_by_id('id_content').get_attribute('disabled'))

        # Browser 1 leaves the change form, it is unlocked and
        # browser 2 is now able to get a lock on it
        browser.get(self.get_admin_url())
        self.assert_no_js_errors(browser)
        self.wait_for_ajax(browser)
        self.assertEqual(Lock.objects.filter(object_id=self.blog_article.pk, locked_by=user.pk).count(), 0)
        browser2.get(self.get_admin_url(instance=self.blog_article))
        self.assert_no_js_errors(browser)
        self.wait_for_ajax(browser2)
        self.assertEqual(Lock.objects.filter(object_id=self.blog_article.pk, locked_by=user2.pk).count(), 1)
        self.assertFalse(browser2.find_element_by_id('id_title').get_attribute('disabled'))
        self.assertFalse(browser2.find_element_by_id('id_content').get_attribute('disabled'))

    def test_changelist(self):
        """Browser loads the list view page, the correct article is listed as locked"""
        user, password = user_factory(BlogArticle)
        Lock.objects.lock_object_for_user(self.blog_article, user)
        user2, password2 = user_factory(BlogArticle)
        browser = self.get_browser(user2, password2)

        browser.get(self.get_admin_url())
        self.assert_no_js_errors(browser)
        self.wait_for_ajax(browser)

        elem_1 = browser.find_element_by_id('locking-%s' % self.blog_article.pk)
        elem_2 = browser.find_element_by_id('locking-%s' % self.blog_article_2.pk)
        self.assertTrue('locked' in elem_1.get_attribute('class'))
        self.assertFalse('locked' in elem_2.get_attribute('class'))

    def tearDown(self):
        for browser in self.browsers:
            browser.quit()
