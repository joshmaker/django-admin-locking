from django.contrib import admin
from django.db import models

from ..admin import LockingAdminMixin


class BlogArticle(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()

    class Meta:
        app_label = 'locking'


class BlogArticleAdmin(LockingAdminMixin, admin.ModelAdmin):
    pass

admin.site.register(BlogArticle, BlogArticleAdmin)
