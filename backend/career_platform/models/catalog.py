from django.db import models
from .base import Timestamped

class InterviewQuestion(Timestamped):
    category = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    topic = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=10, choices=[('easy','easy'),('medium','medium'),('hard','hard')])
    question = models.TextField()
    key_points = models.JSONField(default=list)
    reference_answer = models.TextField()
    source = models.CharField(max_length=255)
    source_url = models.URLField(max_length=1000, blank=True)
    permission_status = models.CharField(max_length=20, default='pending', choices=[('pending','pending'),('allowed','allowed'),('restricted','restricted')])
    collected_at = models.DateTimeField(null=True, blank=True)
    tags = models.JSONField(default=list)
    dedupe_key = models.CharField(max_length=128, unique=True, null=True, blank=True)
    is_demo = models.BooleanField(default=False)
