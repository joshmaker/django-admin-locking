from __future__ import absolute_import, unicode_literals, division

from .forms import LockingAdminModelForm


class LockingAdminMixin(object):
    form = LockingAdminModelForm
