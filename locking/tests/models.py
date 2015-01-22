from django.db import models


class BlogArticle(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()

    class Meta:
        app_label = 'locking'
