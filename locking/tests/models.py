from django import forms
from django.contrib import admin
from django.db import models

from ..admin import LockingAdminMixin

__all__ = ('BlogArticle', 'BlogArticleAdmin')


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
