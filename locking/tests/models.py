from django import VERSION
from django import forms
from django.contrib import admin
from django.db import models

from ..admin import LockingAdminMixin


class BlogArticle(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()

    class Meta:
        app_label = 'locking'


class BlogArticleAdmin(LockingAdminMixin, admin.ModelAdmin):

    @property
    def media(self):
        media = super(BlogArticleAdmin, self).media
        media = forms.Media(js=('locking/js/test.js', )) + media
        # Django < 1.5 have too old a version of jquery in the admin
        if VERSION[0] == 1 and VERSION[1] < 5:
            media = forms.Media(js=('locking/js/locking.jquery-1.11.2.min.js', )) + media
        return media
admin.site.register(BlogArticle, BlogArticleAdmin)
