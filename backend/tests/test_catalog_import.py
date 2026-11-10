import json
from pathlib import Path

from career_platform.catalog.service import CatalogService
from career_platform.tests.accept_support import AcceptanceCase
from company_reviews.models import Company, Job

DATA_FILE = Path(__file__).resolve().parents[2] / 'data' / 'career-platform' / 'java-backend.json'


class CatalogImportTests(AcceptanceCase):
    def setUp(self):
        super().setUp()
        self.dataset = json.loads(DATA_FILE.read_text(encoding='utf-8'))

    def import_kind(self, kind, *, dry_run=False, expected=200, staff=True):
        return self.post('catalog/imports/', {
            'kind': kind, 'records': self.dataset[kind], 'dry_run': dry_run,
        }, staff=staff, expected=expected)

    def test_demo_dataset_imports_in_order_and_is_idempotent(self):
        first = self.import_kind('companies')
        self.assertEqual(first['created'], 2)
        self.assertEqual(first['updated'], 0)
        self.assertEqual(Company.objects.count(), 2)
        again = self.import_kind('companies')
        self.assertEqual(again['created'], 0)
        self.assertEqual(again['unchanged'], 2)
        self.assertEqual(Company.objects.count(), 2)

        jobs = self.import_kind('jobs')
        self.assertEqual(jobs['created'], 3)
        self.assertEqual(Job.objects.count(), 3)
        self.assertEqual(Job.objects.filter(company__name__contains='云帆').count(), 2)
        self.assertEqual(self.import_kind('jobs')['unchanged'], 3)
        self.assertEqual(Job.objects.count(), 3)

        questions = self.import_kind('questions')
        self.assertEqual(questions['created'], 30)
        self.assertEqual(self.import_kind('questions')['unchanged'], 30)

    def test_dry_run_writes_nothing_and_source_time_are_visible(self):
        preview = self.import_kind('companies', dry_run=True)
        self.assertEqual(preview['created'], 2)
        self.assertEqual(preview['dry_run'], True)
        self.assertEqual(Company.objects.count(), 0)

        self.import_kind('companies')
        self.import_kind('jobs')
        row = self.get('catalog/jobs/?city=杭州')['results'][0]
        self.assertTrue(row['source'])
        self.assertTrue(row['collected_at'])
        self.assertTrue(row['is_demo'])
        self.assertEqual(row['permission_status'], 'allowed')
        direction = self.get('catalog/jobs/?role=数据平台')
        self.assertEqual(direction['count'], 1)
        self.assertEqual(direction['results'][0]['title'], '数据平台开发工程师')

    def test_only_allowed_questions_are_queryable(self):
        self.import_kind('questions')
        self.assertEqual(self.get('catalog/questions/?role=Java后端')['count'], 0)

        allowed = dict(self.dataset['questions'][0], permission_status='allowed')
        self.post('catalog/imports/', {
            'kind': 'questions', 'records': [allowed], 'dry_run': False,
        }, staff=True)
        result = self.get('catalog/questions/?role=Java后端&topic=Java基础&difficulty=easy')
        self.assertEqual(result['count'], 1)
        self.assertEqual(result['results'][0]['source'], allowed['source'])
        self.assertTrue(result['results'][0]['collected_at'])

    def test_allowed_question_is_available_to_member4_retrieval(self):
        from career_platform.rag.retrieval import DjangoQuestionRetriever

        allowed = next(
            question for question in self.dataset['questions']
            if question['topic'] == '集合' and 'ArrayList' in question['question']
        )
        allowed = dict(allowed, permission_status='allowed')
        self.post('catalog/imports/', {
            'kind': 'questions', 'records': [allowed], 'dry_run': False,
        }, staff=True)
        results = DjangoQuestionRetriever().retrieve(
            query='ArrayList', role='Java后端', topic='集合', difficulty='easy', top_k=5)
        self.assertTrue(results)
        self.assertEqual(results[0].origin, 'catalog')
        self.assertIn(
            ('source', allowed['source']),
            {(item.field_path, item.quote) for item in results[0].evidence},
        )

    def test_unsupported_filter_is_rejected(self):
        self.get('catalog/questions/?city=杭州', expected=400)

    def test_index_notifier_is_scheduled_only_for_allowed_questions(self):
        calls = []

        class Notifier:
            def notify(self, *, kind, ids):
                calls.append((kind, ids))

        self.wire(catalog=CatalogService(index_notifier=Notifier()))
        allowed = dict(self.dataset['questions'][0], permission_status='allowed')
        with self.captureOnCommitCallbacks(execute=True):
            self.post('catalog/imports/', {
                'kind': 'questions', 'records': [allowed], 'dry_run': False,
            }, staff=True)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], 'questions')
        self.assertEqual(len(calls[0][1]), 1)
