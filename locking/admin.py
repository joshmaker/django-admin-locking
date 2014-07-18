from __future__ import absolute_import, unicode_literals, division

import json

from django import forms
from django.conf.urls import patterns, url
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.http import HttpResponse

from .models import Lock
from .settings import PING_SECONDS


class LockingAdminMixin(object):

    class Media:
        js = ('locking/js/locking.js', )

    def __init__(self, *args, **kwargs):
        super(LockingAdminMixin, self).__init__(*args, **kwargs)
        if hasattr(self.list_display, 'append'):
            self.list_display.append('is_locked', )
        else:
            self.list_display = self.list_display + ('is_locked', )

        opts = self.model._meta
        self._model_info = (opts.app_label, opts.model_name)

    def get_form(self, request, obj=None, **kwargs):
        """Patches the clean method of the admin form to confirm lock status

        The forms clean method will now raise a validation error if the form
        is locked by someone else.
        """
        form = super(LockingAdminMixin, self).get_form(request, obj, **kwargs)
        old_clean = form.clean

        def clean(self):
            self.cleaned_data = old_clean(self)
            if self.instance.id:
                content_type = ContentType.objects.get_for_model(self.instance)
                try:
                    lock = Lock.objects.get(content_type=content_type, object_id=self.instance.id)
                except Lock.DoesNotExist:
                    pass
                else:
                    if request.user != lock.locked_by:
                        user_name = lock.locked_by.username
                        raise forms.ValidationError('You cannot save this object because'
                                                    ' it is locked by user %s' % user_name)
            return self.cleaned_data
        form.clean = clean
        return form

    def is_locked(self, obj):
        return Lock.is_locked(obj)
    is_locked.allow_tags = True
    is_locked.short_description = 'Lock'

    def get_urls(self):
        urls = super(LockingAdminMixin, self).get_urls()
        locking_urls = patterns('',
            url(r'^locking.%s_%s_(?P<object_id>[0-9]+).js$' % self._model_info,
                self.admin_site.admin_view(self.locking_js),
                name='locking_%s_%s_js' % self._model_info
            ),
        )
        return locking_urls + urls

    def locking_media(self, obj=None):
        return forms.Media(js=(
            reverse('admin:locking_%s_%s_js' % self._model_info,
                    kwargs={'object_id': obj.pk}
            ),
        ))

    def locking_js(self, request, object_id):
        app_label, model_name = self._model_info
        js_options = json.dumps({
            'appLabel': app_label,
            'modelName': model_name,
            'ping': PING_SECONDS,
            'objectID': object_id,
        })
        return render(request, 'locking/admin_form.js',
            {'options': js_options}, content_type="application/json")

    def render_change_form(self, request, context, add=False, obj=None, **kwargs):
        if not add and getattr(obj, 'pk', False):
            locking_media = self.locking_media(obj)
            if isinstance(context['media'], basestring):
                locking_media = unicode(locking_media)
            context['media'] += locking_media
        return super(LockingAdminMixin, self).render_change_form(
                request, context, add=add, obj=obj, **kwargs)
