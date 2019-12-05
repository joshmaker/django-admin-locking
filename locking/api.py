from __future__ import absolute_import, unicode_literals, division

from collections import Iterable

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, JsonResponse
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import Lock

__all__ = ('LockAPIView', )


class LockingJsonResponse(JsonResponse):
    def __init__(self, data, encoder=DjangoJSONEncoder, safe=False, **kwargs):
        if isinstance(data, Iterable):
            data = [d.to_dict() for d in data]
        else:
            data = data.to_dict()
        super(LockingJsonResponse, self).__init__(data, encoder, safe, **kwargs)


class BaseAPIView(View):

    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def dispatch(self, request, app, model, object_id=None):
        model = model.lower()
        # if the usr can't change the object, they shouldn't be allowed to change the lock
        may_change = '%s.change_%s' % (app, model)
        if not request.user.has_perm(may_change):
            return HttpResponse(status=401)

        try:
            self.lock_ct_type = ContentType.objects.get(app_label=app, model=model)
        except ContentType.DoesNotExist:
            return HttpResponse(status=404)

        if not object_id and request.method != 'GET':
            return HttpResponse(status=405)

        return super(BaseAPIView, self).dispatch(request, app, model, object_id)


class LockAPIView(BaseAPIView):

    http_method_names = ['get', 'post', 'delete', 'put']

    def get(self, request, app, model, object_id=None):
        locks = (Lock.objects.filter(content_type=self.lock_ct_type)
                             .unexpired()
                             .select_related('locked_by'))
        if object_id:
            locks = locks.filter(object_id=object_id)
        return LockingJsonResponse(locks)

    def post(self, request, app, model, object_id):
        """Create or maintain a lock on an object if possible"""
        try:
            lock = Lock.objects.lock_for_user(content_type=self.lock_ct_type,
                                              object_id=object_id,
                                              user=request.user)
        # Another user already has a lock
        except Lock.ObjectLockedError as e:
            return LockingJsonResponse([e.lock], status=409)
        return LockingJsonResponse(lock)

    def put(self, request, app, model, object_id):
        """Create lock on an object, even if it was already locked"""
        lock = Lock.objects.force_lock_for_user(self.lock_ct_type, object_id, request.user)
        return LockingJsonResponse(lock, status=200)

    def delete(self, request, app, model, object_id):
        """
        Remove a lock from an object
        """
        try:
            Lock.objects.unlock_for_user(content_type=self.lock_ct_type,
                                         object_id=object_id,
                                         user=request.user)
        except Lock.ObjectLockedError:
            # If the lock belongs to another user
            return HttpResponse(status=401)
        else:
            return HttpResponse(status=204)


class DeleteBeacon(BaseAPIView):
    """
    Handle's calls to unlock an object when the user navigates away from the page

    Modern webbrowsers no longer allow blocking AJAX calls on unload events, so
    our JavaScript must use the `navigator.sendBeacon` instead. Because this
    method can only make POST requests, we can't follow our normal RESTful API
    methods used by our main API class
    """
    http_method_names = ['post']

    def post(self, request, app, model, object_id):
        """
        Remove a lock from an object
        """
        try:
            Lock.objects.unlock_for_user(content_type=self.lock_ct_type,
                                         object_id=object_id,
                                         user=request.user)
        except Lock.ObjectLockedError:
            # If the lock belongs to another user
            return HttpResponse(status=401)
        else:
            return HttpResponse(status=204)
