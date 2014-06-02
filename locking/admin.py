from __future__ import absolute_import, unicode_literals, division

import json

from django import forms
from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from .forms import LockingModelForm
from .models import Lock
from .settings import PING_SECONDS


class LockingAdminMixin(object):
    form = LockingModelForm

    class Media:
        js = ('locking/js/locking.js',)

    def __init__(self, *args, **kwargs):
        super(LockingAdminMixin, self).__init__(*args, **kwargs)
        self.list_display = self.list_display + ('is_locked', )

        opts = self.model._meta
        self._model_info = (opts.app_label, opts.model_name)

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

        js_code = "var lockingForm = new locking.LockingForm('{form_name}', {options});".format(
            form_name=model_name + '_form', options=js_options)

        return HttpResponse(js_code, content_type="application/json")

    def render_change_form(self, request, context, add=False, obj=None, **kwargs):
        if not add and getattr(obj, 'pk', False):
            locking_media = self.locking_media(obj)
            if isinstance(context['media'], basestring):
                locking_media = unicode(locking_media)
            context['media'] += locking_media
        return super(LockingAdminMixin, self).render_change_form(
                request, context, add=add, obj=obj, **kwargs)
