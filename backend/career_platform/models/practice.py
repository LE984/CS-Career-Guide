from django.db import models
from .base import OwnedRun, Timestamped

class PracticeSession(OwnedRun):
    job = models.ForeignKey('company_reviews.Job', on_delete=models.SET_NULL, null=True, blank=True)
    job_snapshot = models.JSONField(default=dict)
    resume_snapshot = models.JSONField(default=dict)
    filters = models.JSONField(default=dict)
    presented_questions = models.JSONField(default=list)
    finish_request_id = models.UUIDField(null=True, blank=True)
    summary_request_id = models.UUIDField(null=True, blank=True)
    summary = models.JSONField(default=dict)
    ended_at = models.DateTimeField(null=True, blank=True)

class AnswerRecord(Timestamped):
    session = models.ForeignKey(PracticeSession, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey('career_platform.InterviewQuestion', on_delete=models.SET_NULL, null=True, blank=True)
    question_snapshot = models.JSONField(default=dict)
    request_id = models.UUIDField()
    answer = models.TextField()
    feedback = models.JSONField(default=dict)
    status = models.CharField(max_length=32, default='received')
    failure_code = models.CharField(max_length=80, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['session','request_id'], name='platform_answer_request_unique')]
