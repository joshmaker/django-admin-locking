from django import VERSION
from django.contrib import admin
from django.db import models

from ..admin import LockingAdminMixin


class BlogArticle(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()

    class Meta:
        app_label = 'locking'


class BlogArticleAdmin(LockingAdminMixin, admin.ModelAdmin):

    # Django < 1.5 have too old a version of jquery in the admin
    if VERSION[0] == 1 and VERSION[1] < 5:
        @property
        def media(self):
            from django import forms
            return forms.Media(
                js=('locking/js/locking.jquery-1.11.2.min.js', ),
            ) + super(BlogArticleAdmin, self).media

admin.site.register(BlogArticle, BlogArticleAdmin)
