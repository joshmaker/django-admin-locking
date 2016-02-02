# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Lock',
            fields=[
                ('id', models.CharField(max_length=15, serialize=False, primary_key=True)),
                ('date_expires', models.DateTimeField()),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('locked_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': getattr(settings, 'LOCKING_DB_TABLE', 'locking_lock'),
                'permissions': (('can_unlock', "Can remove other user's locks"),),
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='lock',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
