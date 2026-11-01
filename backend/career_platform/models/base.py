import uuid
from django.db import models
from django.conf import settings

class Timestamped(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class OwnedRun(Timestamped):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    request_id = models.UUIDField()
    status = models.CharField(max_length=32, default='pending')
    failure_code = models.CharField(max_length=80, blank=True)
    class Meta:
        abstract = True
        constraints = [models.UniqueConstraint(fields=['user', 'request_id'], name='%(app_label)s_%(class)s_request_unique')]
