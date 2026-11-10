from django.db import migrations, models


def backfill_practice_fields(apps, schema_editor):
    PracticeSession = apps.get_model('career_platform', 'PracticeSession')
    AnswerRecord = apps.get_model('career_platform', 'AnswerRecord')

    for session in PracticeSession.objects.all().iterator():
        filters = session.filters or {}
        job_snapshot = session.job_snapshot or {}
        session.role = str(filters.get('role') or '')[:100]
        session.topic = str(filters.get('topic') or '')[:100]
        session.difficulty = str(filters.get('difficulty') or '')[:10]
        session.job_title = str(job_snapshot.get('title') or session.role or '')[:255]
        session.save(update_fields=['role', 'topic', 'difficulty', 'job_title'])

    for answer in AnswerRecord.objects.all().iterator():
        snapshot = answer.question_snapshot or {}
        key = snapshot.get('question_id') or answer.question_id or f'legacy:{answer.id}'
        answer.question_key = str(key)[:64]
        answer.save(update_fields=['question_key'])

    duplicates = (
        AnswerRecord.objects.values('session_id', 'question_key')
        .annotate(total=models.Count('id')).filter(total__gt=1)
    )
    if duplicates.exists():
        raise RuntimeError('Duplicate practice answers must be reviewed before adding the unique constraint')


class Migration(migrations.Migration):
    dependencies = [('career_platform', '0002_practicesession_finish_request_id_and_more')]

    operations = [
        migrations.AddField(
            model_name='practicesession', name='role',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='practicesession', name='topic',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='practicesession', name='difficulty',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='practicesession', name='job_title',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='practicesession', name='summary_attempt_log',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='practicesession', name='summary_started_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='answerrecord', name='question_key',
            field=models.CharField(max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='answerrecord', name='feedback_attempt_log',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='answerrecord', name='feedback_request_id',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='answerrecord', name='feedback_started_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_practice_fields, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='answerrecord', name='question_key',
            field=models.CharField(max_length=64),
        ),
        migrations.AddConstraint(
            model_name='answerrecord',
            constraint=models.UniqueConstraint(
                fields=('session', 'question_key'), name='platform_answer_question_unique'
            ),
        ),
        migrations.AddIndex(
            model_name='answerrecord',
            index=models.Index(fields=['session', 'created_at'], name='plat_ans_session_created'),
        ),
        migrations.AddIndex(
            model_name='practicesession',
            index=models.Index(fields=['user', 'created_at'], name='platform_practice_user_created'),
        ),
        migrations.AddIndex(
            model_name='practicesession',
            index=models.Index(fields=['user', 'role', 'topic', 'difficulty'], name='platform_practice_filters'),
        ),
    ]
