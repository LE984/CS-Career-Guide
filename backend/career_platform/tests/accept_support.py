"""Fixed acceptance inputs. Only external dependencies are replaced, never services."""
import copy
import json
from pathlib import Path
from unittest.mock import patch
from django.test import TestCase
from career_platform import composition
from career_platform.models import PracticeSession
from .helpers import client, request_id, question, PREFIX


class Gateway:
    def __init__(self, result=None, fail=False):
        self.result, self.fail, self.calls = result or {}, fail, []

    def generate(self, *, system, payload):
        self.calls.append(copy.deepcopy(payload))
        if self.fail:
            raise TimeoutError('test-only model timeout')
        return copy.deepcopy(self.result)


class AcceptanceCase(TestCase):
    def setUp(self):
        self.user, self.client = client()
        self.admin, self.staff = client(True, 'staff')
        self.other, self.stranger = client(False, 'other')

    def wire(self, **services):
        patcher = patch.dict(composition.services, services)
        patcher.start()
        self.addCleanup(patcher.stop)

    def post(self, path, body, staff=False, expected=200):
        result = (self.staff if staff else self.client).post(PREFIX + path, body, format='json')
        self.assertEqual(result.status_code, expected, result.data)
        return result.data

    def get(self, path, staff=False, expected=200):
        result = (self.staff if staff else self.client).get(PREFIX + path)
        self.assertEqual(result.status_code, expected, result.data)
        return result.data

    def fixture_questions(self):
        return json.loads((Path(__file__).parent / 'fixtures/java_contract.json').read_text(encoding='utf-8'))['questions']

    def session(self):
        q = question()
        snapshot = dict(question_id=str(q.id), question=q.question, key_points=q.key_points,
                        source=q.source, evidence=[dict(source_id=str(q.id),field_path='key_points[0]',quote=q.key_points[0])])
        session = PracticeSession.objects.create(user=self.user,request_id=request_id(),status='active',
            presented_questions=[snapshot],job_snapshot={'title':'Java后端','description':'历史JD'})
        return session, q
