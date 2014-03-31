from django import forms
from django.contrib.contenttypes.models import ContentType

from .models import Lock


class LockingFormMixin(object):

    def clean(self):
        self.cleaned_data = super(LockingFormMixin, self).clean()
        if self.obj.id:
            content_type = ContentType.objects.get_for_model(self.obj)
            try:
                lock = Lock.objects.get(content_type=content_type, object_id=self.obj.id)
            except self.obj.DoesNotExist:
                pass
            else:
                if self.request.user != lock.locked_by:
                    raise forms.ValidationError('You cannot save this object because'
                        ' it is locked by user %s' % lock.locked_by.username)
        return self.cleaned_data
