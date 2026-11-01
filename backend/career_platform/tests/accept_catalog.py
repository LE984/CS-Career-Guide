"""Member 1 must satisfy these against real isolated ORM and production catalog service."""
from career_platform.models import InterviewQuestion
from .accept_support import AcceptanceCase


class CatalogAcceptance(AcceptanceCase):
    def load(self, rows, dry_run=False, expected=200):
        return self.post('catalog/imports/',dict(kind='questions',records=rows,dry_run=dry_run),staff=True,expected=expected)

    def test_import_is_idempotent_and_dry_run_has_no_writes(self):
        rows=self.fixture_questions()
        self.load(rows,True)
        self.assertEqual(InterviewQuestion.objects.count(),0)
        first=self.load(rows)
        ids=set(InterviewQuestion.objects.values_list('id',flat=True))
        self.assertEqual(len(ids),6)
        self.load(rows)
        self.assertEqual(set(InterviewQuestion.objects.values_list('id',flat=True)),ids)

    def test_invalid_row_rolls_back_entire_batch_with_location(self):
        rows=self.fixture_questions()[:2]
        rows[1]['difficulty']='impossible'
        result=self.load(rows,expected=400)
        self.assertIn('1',str(result['details']))
        self.assertIn('difficulty',str(result['details']))
        self.assertEqual(InterviewQuestion.objects.count(),0)

    def test_filters_permissions_and_pagination(self):
        rows=self.fixture_questions()
        rows[0]['permission_status']='pending'
        rows[1]['permission_status']='restricted'
        self.load(rows)
        result=self.get('catalog/questions/?role=Java后端&difficulty=easy&page_size=2')
        self.assertEqual(result['count'],4)
        self.assertEqual(len(result['results']),2)
        self.assertTrue(all(row['permission_status']=='allowed' for row in result['results']))
        for row in result['results']:
            self.assertTrue(row['source'])
        result=self.get('catalog/questions/?role=Python后端')
        self.assertEqual(result['results'],[])
        self.post('catalog/imports/',dict(kind='questions',records=rows),expected=403)

    def test_company_job_sources_and_city_filter(self):
        from company_reviews.models import Company,Job
        c=Company.objects.create(name='演示企业',city='测试市',description='演示',source='team',permission_status='allowed',is_demo=True)
        Job.objects.create(company=c,title='Java后端',city='测试市',requirements='Java',description='Java JD',skills=['Java'],source='team',permission_status='allowed',is_demo=True)
        Job.objects.create(company=c,title='不可检索',city='其他市',requirements='Java',permission_status='pending')
        rows=self.get('catalog/jobs/?city=测试市&q=Java')['results']
        self.assertEqual([r['title'] for r in rows],['Java后端'])
        self.assertTrue(rows[0]['is_demo'])
        self.assertEqual(rows[0]['source'],'team')
