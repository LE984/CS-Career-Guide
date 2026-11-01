from django.db import models
from .base import OwnedRun

class EvaluationRun(OwnedRun):
    task = models.CharField(max_length=20)
    dataset_version = models.CharField(max_length=100)
    strategy = models.CharField(max_length=100)
    parameters = models.JSONField(default=dict)
    metrics = models.JSONField(default=dict)
    results = models.JSONField(default=list)
    model_version = models.CharField(max_length=100, blank=True)
