from rest_framework import serializers
from .models import SeniorAdvice


class SeniorAdviceSerializer(serializers.ModelSerializer):
    """学长学姐建议序列化器"""
    current_company = serializers.CharField(required=False, allow_blank=True, default='', max_length=255)
    salary_info = serializers.CharField(required=False, allow_blank=True, default='', max_length=100)
    rating = serializers.FloatField(min_value=1, max_value=5)
    graduation_year = serializers.RegexField(r'^\d{4}$', error_messages={'invalid': '请填写四位毕业年份。'})
    pros = serializers.ListField(child=serializers.CharField(max_length=500), required=False, default=list)
    cons = serializers.ListField(child=serializers.CharField(max_length=500), required=False, default=list)

    def validate_rating(self, value):
        import math
        if not math.isfinite(value):
            raise serializers.ValidationError('评分应在 1 到 5 分之间。')
        return value

    class Meta:
        model = SeniorAdvice
        fields = [
            'id', 'company', 'position', 'senior_name', 'graduation_year',
            'current_company', 'advice', 'salary_info', 'pros', 'cons',
            'rating', 'created_at', 'is_approved'
        ]
        read_only_fields = ['id', 'created_at', 'is_approved']
