from rest_framework import serializers


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({key: '不支持的字段' for key in sorted(unknown)})
        return super().to_internal_value(data)


class Query(StrictSerializer):
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20)
    q = serializers.CharField(max_length=500, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False)
    role = serializers.CharField(max_length=100, required=False)
    topic = serializers.CharField(max_length=100, required=False)
    difficulty = serializers.ChoiceField(choices=['easy', 'medium', 'hard'], required=False)


class ImportBatch(StrictSerializer):
    kind = serializers.ChoiceField(choices=['companies', 'jobs', 'questions'])
    records = serializers.ListField(child=serializers.DictField(), min_length=1, max_length=1000)
    dry_run = serializers.BooleanField(default=True)


class AnalyzeResume(StrictSerializer):
    jd_text = serializers.CharField(max_length=20000)
    job_id = serializers.IntegerField(min_value=1, required=False)
    resume_revision = serializers.IntegerField(min_value=0)
    request_id = serializers.UUIDField()


class ApplySuggestions(StrictSerializer):
    base_revision = serializers.IntegerField(min_value=0)
    accepted_suggestion_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1)
    # UUID suggestion IDs -> edited text. Service validates ownership and factual evidence.
    suggestion_edits = serializers.DictField(child=serializers.CharField(max_length=20000), default=dict)
    request_id = serializers.UUIDField()


class StartPractice(StrictSerializer):
    job_id = serializers.IntegerField(min_value=1, required=False)
    jd_text = serializers.CharField(max_length=20000, required=False, allow_blank=True)
    role = serializers.CharField(max_length=100)
    topic = serializers.CharField(max_length=100, required=False, allow_blank=True)
    difficulty = serializers.ChoiceField(choices=['easy', 'medium', 'hard'], default='easy')
    request_id = serializers.UUIDField()
    question_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1, max_length=20, required=False)


class RetrieveQuestions(StartPractice):
    top_k = serializers.IntegerField(min_value=1, max_value=20, default=5)


class SubmitAnswer(StrictSerializer):
    question_id = serializers.UUIDField()
    answer = serializers.CharField(max_length=20000)
    request_id = serializers.UUIDField()


class FinishPractice(StrictSerializer):
    request_id = serializers.UUIDField()
    retry_summary = serializers.BooleanField(default=False)


class RunEvaluation(StrictSerializer):
    dataset_version = serializers.CharField(max_length=100)
    task = serializers.ChoiceField(choices=['job', 'resume', 'question'])
    strategy = serializers.CharField(max_length=100)
    parameters = serializers.DictField(default=dict)
    request_id = serializers.UUIDField()
