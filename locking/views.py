from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse

from .models import Lock


@login_required
def lock_view(request, app, model, object_id):

    # if the usr can't change the object, they shouldn't be allowed to lock it
    may_change = '%s.change_%s' % (app, model)
    if not request.user.has_perm(may_change):
        return HttpResponse(status=401)

    ct_type = ContentType.objects.get(app_label=app, model=model)
    try:
        Lock.objects.lock_for_user(content_type=ct_type,
            object_id=object_id, user=request.user)

    # Another user already has a lock
    except Lock.ObjectLockedError:
        return HttpResponse(status=403)

    return HttpResponse(status=200)


@permission_required('locking.can_unlock')
def unlock(request, app, model, object_id):
    ct_type = ContentType.objects.get(app_label=app, model=model)
    Lock.objects.filter(content_type=ct_type, object_id=object_id,
        user=request.user).delete()
    return HttpResponse(status=200)
