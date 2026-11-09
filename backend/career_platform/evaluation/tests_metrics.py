"""指标纯函数与冻结评估集的边界检查；不依赖数据库、模型或网络。"""
from django.test import SimpleTestCase

from .datasets import FrozenDatasetLoader, UnknownDataset
from .metrics import METRIC_KEYS, aggregate_metrics, ranking_metrics


class RankingMetricsTests(SimpleTestCase):
    def test_first_hit_scores_full_precision_recall_and_reciprocal_rank(self):
        metrics = ranking_metrics(
            relevant_ids=['a'], predicted_ids=['a', 'x', 'y', 'z', 'w'], k=5)
        self.assertAlmostEqual(metrics['precision_at_k'], 0.2)
        self.assertAlmostEqual(metrics['recall_at_k'], 1.0)
        self.assertAlmostEqual(metrics['f1_at_k'], 1 / 3)
        self.assertEqual(metrics['hit_rate_at_k'], 1.0)
        self.assertEqual(metrics['mrr'], 1.0)

    def test_later_hit_lowers_reciprocal_rank_only(self):
        metrics = ranking_metrics(
            relevant_ids=['b'], predicted_ids=['x', 'b', 'y', 'z', 'w'], k=5)
        self.assertAlmostEqual(metrics['precision_at_k'], 0.2)
        self.assertEqual(metrics['mrr'], 0.5)

    def test_unrelated_prediction_yields_zero_scores(self):
        metrics = ranking_metrics(
            relevant_ids=['a'], predicted_ids=['u'] * 5, k=5)
        self.assertTrue(all(value == 0 for value in metrics.values()))

    def test_duplicate_predictions_are_scored_once(self):
        metrics = ranking_metrics(
            relevant_ids=['a', 'b'], predicted_ids=['a', 'a', 'b'], k=3)
        self.assertAlmostEqual(metrics['precision_at_k'], 2 / 3)
        self.assertAlmostEqual(metrics['recall_at_k'], 1.0)

    def test_missing_slots_count_as_misses(self):
        metrics = ranking_metrics(relevant_ids=['a'], predicted_ids=['a'], k=10)
        self.assertAlmostEqual(metrics['precision_at_k'], 0.1)
        self.assertEqual(metrics['recall_at_k'], 1.0)

    def test_empty_relevance_set_keeps_ranking_metrics_at_zero(self):
        metrics = ranking_metrics(
            relevant_ids=[], predicted_ids=['a', 'b'], k=2)
        self.assertEqual(metrics, {key: 0.0 for key in METRIC_KEYS})

    def test_invalid_k_is_rejected(self):
        for value in (0, -1, True, '3'):
            with self.subTest(k=value), self.assertRaises(ValueError):
                ranking_metrics(relevant_ids=['a'], predicted_ids=['a'], k=value)

    def test_macro_average_ignores_nothing_and_is_stable(self):
        samples = [dict.fromkeys(METRIC_KEYS, 1.0), dict.fromkeys(METRIC_KEYS, 0.0)]
        metrics = aggregate_metrics(samples)
        self.assertEqual(set(metrics), set(METRIC_KEYS))
        self.assertTrue(all(value == 0.5 for value in metrics.values()))
        self.assertEqual(aggregate_metrics([]), {key: 0.0 for key in METRIC_KEYS})


class FrozenDatasetTests(SimpleTestCase):
    def test_registered_versions_are_loadable_and_stable(self):
        loader = FrozenDatasetLoader()
        versions = loader.versions()
        self.assertIn('java-eval-dev-v1', versions)
        self.assertIn('java-eval-test-v1', versions)
        first = loader.load('java-eval-test-v1')
        second = loader.load('java-eval-test-v1')
        self.assertEqual(first['sha256'], second['sha256'])
        self.assertEqual(first['split'], 'test')
        self.assertTrue(first['queries'])

    def test_unknown_version_is_an_explicit_error(self):
        with self.assertRaises(UnknownDataset):
            FrozenDatasetLoader().load('missing-v9')

    def test_every_relevant_id_exists_in_the_corpus(self):
        from .datasets import load_corpus
        corpus, _summary = load_corpus()
        known = {str(item['id']) for item in corpus['questions']}
        loader = FrozenDatasetLoader()
        for version in ('java-eval-dev-v1', 'java-eval-test-v1'):
            for sample in loader.load(version)['queries']:
                with self.subTest(version=version, query=sample['id']):
                    self.assertFalse(set(sample['relevant_ids']) - known)
