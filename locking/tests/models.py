from __future__ import absolute_import, unicode_literals, division

import sys

from django import forms
from django.conf import settings
from django.contrib import admin
from django.db import models

from ..admin import LockingAdminMixin

__all__ = ('BlogArticle', 'BlogArticleAdmin')

# Test only models currently incompatible with Django migrations
if 'test' in sys.argv or 'runtests.py' in sys.argv:
    class DisableMigrations(object):
        def __contains__(self, item):
            return True

        def __getitem__(self, item):
            return "notmigrations"
    settings.MIGRATION_MODULES = DisableMigrations()


class BlogArticle(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()

    class Meta:
        app_label = 'locking'


class BlogArticleAdmin(LockingAdminMixin, admin.ModelAdmin):

    @property
    def media(self):
        media = super(BlogArticleAdmin, self).media
        return forms.Media(js=('locking/js/test.js', )) + media

admin.site.register(BlogArticle, BlogArticleAdmin)
