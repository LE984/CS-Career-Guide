import uuid
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

PREFIX = '/api/career-platform/'

def client(staff=False, suffix='one'):
    user = get_user_model().objects.create_user(username='contract-'+suffix, password='test-only', is_staff=staff)
    c = APIClient()
    c.force_authenticate(user)
    return user, c

def request_id():
    return str(uuid.uuid4())

def company():
    from company_reviews.models import Company
    return Company.objects.create(name='契约测试企业', city='测试城市', description='仅用于测试', is_demo=True)

def question():
    from career_platform.models import InterviewQuestion
    return InterviewQuestion.objects.create(role='Java后端',topic='集合',category='Java',difficulty='easy',question='解释集合接口',key_points=['语义'],reference_answer='测试参考',source='synthetic_fixture',permission_status='allowed',is_demo=True)
