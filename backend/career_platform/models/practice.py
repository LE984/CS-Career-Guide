from django.db import models
from .base import OwnedRun, Timestamped

class PracticeSession(OwnedRun):
    job = models.ForeignKey('company_reviews.Job', on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=100, blank=True)
    topic = models.CharField(max_length=100, blank=True)
    difficulty = models.CharField(max_length=10, blank=True)
    job_title = models.CharField(max_length=255, blank=True)
    job_snapshot = models.JSONField(default=dict)
    resume_snapshot = models.JSONField(default=dict)
    filters = models.JSONField(default=dict)
    presented_questions = models.JSONField(default=list)
    finish_request_id = models.UUIDField(null=True, blank=True)
    summary_request_id = models.UUIDField(null=True, blank=True)
    summary_started_at = models.DateTimeField(null=True, blank=True)
    summary_attempt_log = models.JSONField(default=list)
    summary = models.JSONField(default=dict)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'request_id'], name='career_platform_practicesession_request_unique')]
        indexes = [
            models.Index(fields=['user', 'created_at'], name='platform_practice_user_created'),
            models.Index(fields=['user', 'role', 'topic', 'difficulty'], name='platform_practice_filters'),
        ]

class AnswerRecord(Timestamped):
    session = models.ForeignKey(PracticeSession, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey('career_platform.InterviewQuestion', on_delete=models.SET_NULL, null=True, blank=True)
    question_key = models.CharField(max_length=64)
    question_snapshot = models.JSONField(default=dict)
    request_id = models.UUIDField()
    answer = models.TextField()
    feedback = models.JSONField(default=dict)
    status = models.CharField(max_length=32, default='received')
    failure_code = models.CharField(max_length=80, blank=True)
    feedback_request_id = models.UUIDField(null=True, blank=True)
    feedback_started_at = models.DateTimeField(null=True, blank=True)
    feedback_attempt_log = models.JSONField(default=list)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['session','request_id'], name='platform_answer_request_unique'),
            models.UniqueConstraint(fields=['session','question_key'], name='platform_answer_question_unique'),
        ]
        indexes = [models.Index(fields=['session', 'created_at'], name='plat_ans_session_created')]
