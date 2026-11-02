from career_platform.evaluation.service import EvaluationService
from career_platform.models import EvaluationRun
from .accept_support import AcceptanceCase
from .helpers import request_id, PREFIX


class Dataset:
    def load(self, version):
        if version != 'fixed-java-v1':
            raise ValueError('unknown dataset')
        return dict(version=version,split='test',queries=[
            dict(id='one',query='集合',relevant_ids=['a']),
            dict(id='two',query='并发',relevant_ids=['b'])])


class Ranker:
    def rank(self, *, query, top_k):
        return (['a','x','y','z','w'] if query=='集合' else ['x','b','y','z','w'])[:top_k]


class EvaluationAcceptance(AcceptanceCase):
    def setUp(self):
        super().setUp()
        self.wire(evaluation=EvaluationService(strategies={'fixed':Ranker()},dataset_loader=Dataset()))

    def body(self):
        return dict(task='question',strategy='fixed',dataset_version='fixed-java-v1',parameters={'k':5},request_id=request_id())

    def test_metrics_reproducibility_and_export(self):
        body=self.body()
        first=self.post('evaluation-runs/',body,True)
        run=EvaluationRun.objects.get(pk=first['id'])
        for name,value in dict(precision_at_k=.2,recall_at_k=1.,f1_at_k=1/3,hit_rate_at_k=1.,mrr=.75).items():
            self.assertAlmostEqual(run.metrics[name],value)
        self.assertEqual(run.dataset_version,'fixed-java-v1')
        self.assertEqual(run.parameters['k'],5)
        self.assertTrue(run.model_version)
        self.assertEqual(len(run.results),2)
        self.assertEqual(self.post('evaluation-runs/',body,True)['id'],first['id'])
        body['request_id']=request_id()
        second=self.post('evaluation-runs/',body,True)
        self.assertEqual(EvaluationRun.objects.get(pk=second['id']).metrics,run.metrics)
        self.assertEqual(self.get(f"evaluation-runs/{run.id}/export/",True)['metrics'],run.metrics)

    def test_unknown_dataset_and_non_admin_are_rejected(self):
        body=self.body();body['dataset_version']='unknown'
        self.post('evaluation-runs/',body,True,expected=400)
        self.assertEqual(EvaluationRun.objects.count(),0)
        self.post('evaluation-runs/',self.body(),expected=403)

    def test_unrelated_predictions_are_zero_not_predefined_good_scores(self):
        class Wrong:
            def rank(self,**kwargs): return ['unrelated']*5
        self.wire(evaluation=EvaluationService(strategies={'fixed':Wrong()},dataset_loader=Dataset()))
        result=self.post('evaluation-runs/',self.body(),True)
        self.assertTrue(all(v==0 for v in EvaluationRun.objects.get(pk=result['id']).metrics.values()))
