from django import test
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
try:
    from django.contrib.auth import get_user_model
except ImportError:
    # Django < 1.5
    from django.contrib.auth.models import User
    get_user_model = lambda: User
from django.contrib.auth.models import Permission


def user_factory(model, has_perm=True):
def user_factory(model=None):
    username = 'user%d' % timezone.now().microsecond
    email = '%s@example.com' % username
    password = 'p@ssw0rd'
    user = get_user_model().objects.create_user(username, email, password)  # user will have is_staff = False
    user.is_staff = True
    user.save()
    if has_perm:
        for perm in ['add', 'change']:
            codename = '%s_%s' % (perm, model._meta.object_name.lower())
            permission = Permission.objects.get(codename=codename, content_type=content_type)
            user.user_permissions.add(permission)
    return user, password


class LockingClient(object):

    def __init__(self, instance):
        self.instance = instance
        self.url = reverse('locking-api', kwargs={
            'app': instance._meta.app_label,
            'model': instance._meta.object_name,
            'object_id': instance.pk,
        })
        self.client = test.Client()
        self.user = None

    def login_new_user(self, *args, **kwargs):
        self.client.logout()
        user, password = user_factory(self.instance, *args, **kwargs)
        self.client.login(username=user.username, password=password)
        self.user = user

    def get(self, *args, **kwargs):
        return self.client.get(self.url, *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.client.post(self.url, *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.client.delete(self.url, *args, **kwargs)
