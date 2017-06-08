from __future__ import absolute_import, unicode_literals, division

import json
import types

from django import forms
from django.conf import settings
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.shortcuts import render

from .models import Lock
from .settings import DEFAULT_PING_SECONDS, DEFAULT_SHARE_ADMIN_JQUERY

__all__ = ('LockingValidationError', 'LockingAdminMixin')


class LockingValidationError(forms.ValidationError):
    msg = 'You cannot {action} this object because it is locked by {name} ({email})'

    def __init__(self, lock, action):
        locked_by = lock.locked_by
        if locked_by.first_name and locked_by.last_name:
            locked_by_name = '%s %s' % (locked_by.first_name, locked_by.last_name)
        else:
            locked_by_name = locked_by.username
        super(LockingValidationError, self).__init__(
            self.msg.format(action=action, name=locked_by_name, email=locked_by.email))


class LockingAdminMixin(object):

    def __init__(self, *args, **kwargs):
        """Appends the "is_locked" column to this admin's list_display"""
        super(LockingAdminMixin, self).__init__(*args, **kwargs)
        if 'is_locked' not in self.list_display:
            if hasattr(self.list_display, 'append'):
                self.list_display.append('is_locked', )
            else:
                self.list_display = self.list_display + ('is_locked', )

        opts = self.model._meta
        self._model_info = (opts.app_label, opts.model_name)

    @property
    def media(self):
        media = super(LockingAdminMixin, self).media + forms.Media(
            js=('locking/js/locking.js',
                'locking/js/locking.admin.js',
                self.locking_admin_changelist_js_url()),
            css={'all': ('locking/css/changelist.css', )}
        )
        if not getattr(settings, 'LOCKING_SHARE_ADMIN_JQUERY', DEFAULT_SHARE_ADMIN_JQUERY):
            media = forms.Media(js=('locking/js/locking.jquery-1.11.2.min.js', )) + media
        return media

    def get_list_display_links(self, *args, **kwargs):
        links = super(LockingAdminMixin, self).get_list_display_links(*args, **kwargs)
        if not links:
            return ('is_locked', )
        elif isinstance(links, list):
            links.append('is_locked')
        elif isinstance(links, tuple):
            links = links + ('is_locked', )
        return links

    def get_form(self, request, obj=None, **kwargs):
        """Patches the clean method of the admin form to confirm lock status
        The forms clean method will now raise a validation error if the form
        is locked by someone else.
        """
        form = super(LockingAdminMixin, self).get_form(request, obj, **kwargs)
        if request.method == 'POST' and obj and Lock.is_locked(obj, for_user=request.user):
            lock = Lock.objects.for_object(obj)[0]

            def clean(self, *args, **kwargs):
                raise LockingValidationError(lock, 'save')
            form.clean = types.MethodType(clean, form)
        return form

    def has_delete_permission(self, request, obj=None):
        if obj and Lock.is_locked(obj, for_user=request.user):
            return False
        return super(LockingAdminMixin, self).has_delete_permission(request, obj)

    def is_locked(self, obj):
        """List Display column to show lock status"""
        html = ('<span id="locking-{obj_id}" data-object-id="{obj_id}" class="locking-status">'
                '</span>')
        return html.format(obj_id=obj.pk)

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
        locking_urls = [
            # URL For Locking admin form JavaScript
            url(r'^locking_form.%s_%s_(?P<object_id>[0-9]+).js$' % self._model_info,
                self.admin_site.admin_view(self.locking_admin_form_js),
                name=self.locking_admin_form_js_url_name),

            # URL For Locking admin changelist JavaScript
            url(r'^locking_changelist.%s_%s.js$' % self._model_info,
                self.admin_site.admin_view(self.locking_admin_changelist_js),
                name=self.locking_admin_changelist_js_url_name),
        ]
        return locking_urls + urls

    def get_json_options(self, request, object_id=None):
        app_label, model_name = self._model_info
        return json.dumps({
            'currentUser': request.user.username,
            'appLabel': app_label,
            'modelName': model_name,
            'ping': getattr(settings, 'LOCKING_PING_SECONDS', DEFAULT_PING_SECONDS),
            'objectID': object_id,
        })

    def locking_admin_form_js(self, request, object_id):
        """Render out JS code for locking a form for a given object_id on this admin"""
        return render(request,
                      'locking/admin_form.js',
                      {'options': self.get_json_options(request, object_id)},
                      content_type="application/javascript")

    def locking_admin_form_js_url(self, object_id):
        """Get the URL for the locking admin form js for a given object_id on this admin"""
        return reverse('admin:' + self.locking_admin_form_js_url_name,
                       kwargs={'object_id': object_id})

    def locking_admin_changelist_js(self, request):
        """Render out JS code for locking a form for a given object_id on this admin"""
        return render(request, 'locking/admin_changelist.js',
                      {'options': self.get_json_options(request)},
                      content_type="application/javascript")

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
