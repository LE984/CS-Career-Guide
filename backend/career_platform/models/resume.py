from django.db import models
from .base import OwnedRun

class ResumeAnalysisRun(OwnedRun):
    resume = models.ForeignKey('resumes.Resume', on_delete=models.SET_NULL, null=True)
    base_revision = models.PositiveBigIntegerField()
    resume_snapshot = models.JSONField(default=dict)
    jd_text = models.TextField()
    job_snapshot = models.JSONField(default=dict)
    result = models.JSONField(default=dict)
    model_version = models.CharField(max_length=100, blank=True)
    prompt_version = models.CharField(max_length=100, default='v1')

class ResumeApplyReceipt(OwnedRun):
    analysis = models.ForeignKey(ResumeAnalysisRun, on_delete=models.CASCADE, related_name='applications')
    accepted_suggestion_ids = models.JSONField(default=list)
    applied_revision = models.PositiveBigIntegerField()
