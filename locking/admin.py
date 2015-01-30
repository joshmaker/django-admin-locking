from __future__ import absolute_import, unicode_literals, division

import json

from django import forms
from django.conf.urls import patterns, url
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.shortcuts import render

from .models import Lock
from .settings import PING_SECONDS


class LockingAdminMixin(object):

    def __init__(self, *args, **kwargs):
        """Appends the "is_locked" column to this admin's list_display"""
        super(LockingAdminMixin, self).__init__(*args, **kwargs)
        if hasattr(self.list_display, 'append'):
            self.list_display.append('is_locked', )
        else:
            self.list_display = self.list_display + ('is_locked', )

            opts = self.model._meta
            # opts.model_name introduced in Django 1.6
            model_name = getattr(opts, 'model_name', None) or opts.module_name.lower()
        self._model_info = (opts.app_label, model_name)

    @property
    def media(self):
        return super(LockingAdminMixin, self).media + forms.Media(
            js=('locking/js/locking.js', self.locking_admin_changelist_js_url()),
            css={'all': ('locking/css/changelist.css', )}
        )

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
        """List Display column to show lock status"""
        return '<a id="locking-{obj_id}" data-object-id="{obj_id}" class="locking-status"></a>'.format(obj_id=obj.pk)

    is_locked.allow_tags = True
    is_locked.short_description = 'Lock'

    @property
    def locking_admin_form_js_url_name(self):
        return 'admin_form_%s_%s_js' % self._model_info

    @property
    def locking_admin_changelist_js_url_name(self):
        return 'admin_changelist_%s_%s_js' % self._model_info

    def get_urls(self):
        """Adds 'locking_admin_form_js' script to the available URLs"""
        urls = super(LockingAdminMixin, self).get_urls()
        locking_urls = patterns('',
            # URL For Locking admin form JavaScript
            url(r'^locking_form.%s_%s_(?P<object_id>[0-9]+).js$' % self._model_info,
                self.admin_site.admin_view(self.locking_admin_form_js),
                name=self.locking_admin_form_js_url_name),

            # URL For Locking admin changelist JavaScript
            url(r'^locking_changelist.%s_%s.js$' % self._model_info,
                self.admin_site.admin_view(self.locking_admin_changelist_js),
                name=self.locking_admin_changelist_js_url_name),
        )
        return locking_urls + urls

    def get_json_options(self, object_id=None):
        app_label, model_name = self._model_info
        return json.dumps({
            'appLabel': app_label,
            'modelName': model_name,
            'ping': PING_SECONDS,
            'objectID': object_id,
        })

    def locking_admin_form_js(self, request, object_id):
        """Render out JS code for locking a form for a given object_id on this admin"""
        return render(request, 'locking/admin_form.js',
            {'options': self.get_json_options(object_id)}, content_type="application/json")

    def locking_admin_form_js_url(self, object_id):
        """Get the URL for the locking admin form js for a given object_id on this admin"""
        return reverse('admin:' + self.locking_admin_form_js_url_name,
            kwargs={'object_id': object_id})

    def locking_admin_changelist_js(self, request):
        """Render out JS code for locking a form for a given object_id on this admin"""
        return render(request, 'locking/admin_changelist.js',
            {'options': self.get_json_options()}, content_type="application/json")

    def locking_admin_changelist_js_url(self):
        """Get the URL for the locking admin form js for a given object_id on this admin"""
        return reverse('admin:' + self.locking_admin_changelist_js_url_name)

    def render_change_form(self, request, context, add=False, obj=None, **kwargs):
        """If editing an existing object, add form locking media to the media context"""
        if not add and getattr(obj, 'pk', False):
            locking_media = forms.Media(js=(self.locking_admin_form_js_url(obj.pk), ))
            try:
                str_type = basestring
            except NameError:  # basestring does not exist in Python3
                str_type = str
            if isinstance(context['media'], str_type):
                locking_media = unicode(locking_media)
            context['media'] += locking_media
        return super(LockingAdminMixin, self).render_change_form(
                request, context, add=add, obj=obj, **kwargs)
