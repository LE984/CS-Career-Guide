"""成员四的纯内存测试；所有题目均为虚构，不是正式题库或评估集。"""

import inspect
import re
import sys
import unittest
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from career_platform.contracts import RankedQuestion, RetrievalStrategy
from career_platform.rag.retrieval import TextRetrievalStrategy


def question(number=1, **changes):
    """字段沿用 InterviewQuestion；来源明确标注为本地测试自编。"""
    row = {
        'id': UUID(int=number), 'category': '技术基础', 'role': 'Java 后端',
        'topic': '集合', 'difficulty': 'easy',
        'question': '如何选择 Java 集合中的 List 和 Set？',
        'key_points': ['List 保留顺序', 'Set 不保存重复元素'],
        'reference_answer': '根据是否需要顺序和去重选择容器。',
        'tags': ['Java', '集合'],
        'source': '本地离线测试自编虚构题目，不作为正式题库',
        'source_url': '', 'permission_status': 'allowed',
        'collected_at': None, 'dedupe_key': f'fictional-test-{number}', 'is_demo': True,
    }
    row.update(changes)
    return row


def retrieve(strategy, **changes):
    conditions = dict(query='集合', role='Java 后端', topic='集合', difficulty='easy', top_k=5)
    conditions.update(changes)
    return strategy.retrieve(**conditions)


class TextRetrievalTests(unittest.TestCase):
    def test_java_collections_easy_only_returns_eligible_questions(self):
        rows = [
            question(1), question(2, question='集合中 Set 的基础用途是什么？'),
            question(3, role='Python 后端'), question(4, topic='并发'),
            question(5, difficulty='hard'), question(6, permission_status='pending'),
            question(7, permission_status='restricted'),
        ]
        results = retrieve(TextRetrievalStrategy(rows))
        self.assertEqual({r.question_id for r in results}, {str(rows[0]['id']), str(rows[1]['id'])})
        self.assertTrue(all(isinstance(r, RankedQuestion) for r in results))

    def test_unknown_topic_and_unrelated_query_return_empty(self):
        strategy = TextRetrievalStrategy([question()])
        self.assertEqual(retrieve(strategy, topic='不存在的知识点'), [])
        self.assertEqual(retrieve(strategy, query='火星地质'), [])

    def test_permissions_fail_closed_even_with_exact_text_match(self):
        for status in ('pending', 'restricted', '', 'unknown', None):
            with self.subTest(status=status):
                self.assertEqual(retrieve(TextRetrievalStrategy([question(permission_status=status)])), [])
        row = question()
        del row['permission_status']
        self.assertEqual(retrieve(TextRetrievalStrategy([row])), [])

    def test_weighted_matches_in_question_tags_key_points_and_answer(self):
        common = dict(question='基础问题', tags=[], key_points=[], reference_answer='基础答案')
        rows = [
            question(4, **(common | {'reference_answer': '迭代器'})),
            question(3, **(common | {'key_points': ['迭代器']})),
            question(2, **(common | {'tags': ['迭代器']})),
            question(1, **(common | {'question': '迭代器'})),
        ]
        results = retrieve(TextRetrievalStrategy(rows), query='迭代器')
        self.assertEqual([r.question_id for r in results], [str(UUID(int=i)) for i in (1, 2, 3, 4)])
        for result, expected in zip(results, (.4, .3, .2, .1)):
            self.assertAlmostEqual(result.score, expected)

    def test_query_coverage_rewards_more_matching_terms(self):
        rows = [question(1, question='ArrayList'), question(2, question='ArrayList Iterator')]
        results = retrieve(TextRetrievalStrategy(rows), query='ArrayList Iterator')
        self.assertEqual([r.question_id for r in results], [str(rows[1]['id']), str(rows[0]['id'])])

    def test_normalization_handles_case_full_width_and_outer_whitespace(self):
        results = retrieve(
            TextRetrievalStrategy([question(question='ArrayList 的用途')]),
            query=' ＡＲＲＡＹＬＩＳＴ ', role=' ＪＡＶＡ 后端 ', topic=' 集合 ', difficulty=' EASY ',
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].question, 'ArrayList 的用途')

    def test_chinese_bigrams_match_inside_longer_sentences(self):
        self.assertEqual(len(retrieve(TextRetrievalStrategy([question()]), query='如何选择集合')), 1)

    def test_latin_words_do_not_match_unrelated_substrings(self):
        row = question(question='asset', key_points=[], tags=[], reference_answer='')
        self.assertEqual(retrieve(TextRetrievalStrategy([row]), query='set'), [])

    def test_stable_ties_and_top_k_do_not_depend_on_input_order(self):
        rows = [question(i) for i in (3, 1, 2)]
        strategy = TextRetrievalStrategy(iter(rows))
        expected = [str(UUID(int=i)) for i in (1, 2)]
        first = retrieve(strategy, top_k=2)
        self.assertEqual([r.question_id for r in first], expected)
        self.assertEqual(first, retrieve(strategy, top_k=2))
        self.assertEqual(first, retrieve(TextRetrievalStrategy(reversed(rows)), top_k=2))

    def test_empty_query_filters_without_inventing_relevance(self):
        results = retrieve(TextRetrievalStrategy([question()]), query='  ')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 0)
        self.assertEqual(retrieve(TextRetrievalStrategy([question()]), query='!?'), [])

    def test_empty_conditions_are_unconstrained_but_nonempty_conditions_are_exact(self):
        strategy = TextRetrievalStrategy([question()])
        self.assertEqual(len(retrieve(strategy, role='', topic='', difficulty='')), 1)
        for field, value in [('role', 'Java'), ('topic', '集'), ('difficulty', 'medium')]:
            with self.subTest(field=field):
                self.assertEqual(retrieve(strategy, **{field: value}), [])

    def test_threshold_and_weights_are_configurable(self):
        row = question(question='迭代器', tags=[], key_points=[], reference_answer='')
        self.assertEqual(len(retrieve(TextRetrievalStrategy([row], min_score=.4), query='迭代器')), 1)
        self.assertEqual(retrieve(TextRetrievalStrategy([row], min_score=.41), query='迭代器'), [])
        results = retrieve(TextRetrievalStrategy([row], field_weights={'question': 1}), query='迭代器')
        self.assertEqual(results[0].score, 1)

    def test_invalid_parameters_raise_instead_of_looking_like_no_match(self):
        strategy = TextRetrievalStrategy([])
        for value in (0, -1, 21, True, 1.5, '5', None):
            with self.subTest(top_k=value), self.assertRaises(ValueError):
                retrieve(strategy, top_k=value)
        for value in (-.1, 1.1, float('nan'), float('inf')):
            with self.subTest(min_score=value), self.assertRaises(ValueError):
                TextRetrievalStrategy([], min_score=value)
        for weights in ({}, {'role': 1}, {'question': -1}, {'question': 0}, {'tags': float('nan')}):
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                TextRetrievalStrategy([], field_weights=weights)

    def test_evidence_resolves_to_original_fields_without_fabricated_url(self):
        row = question(source_url='https://example.invalid/fictional-test-only')
        result = retrieve(TextRetrievalStrategy([row]))[0]
        self.assertEqual(result.origin, 'catalog')
        self.assertEqual(result.key_points, tuple(row['key_points']))
        self.assertEqual(result.question_id, str(row['id']))
        paths = {e.field_path for e in result.evidence}
        self.assertTrue({'source', 'source_url', 'question', 'key_points[0]', 'tags[0]', 'reference_answer'} <= paths)
        for evidence in result.evidence:
            self.assertEqual(evidence.source_id, str(row['id']))
            match = re.fullmatch(r'(\w+)\[(\d+)\]', evidence.field_path)
            original = row[match[1]][int(match[2])] if match else row[evidence.field_path]
            self.assertEqual(evidence.quote, original)
        no_url = retrieve(TextRetrievalStrategy([question()]))[0]
        self.assertNotIn('source_url', {e.field_path for e in no_url.evidence})

    def test_missing_provenance_id_or_question_is_not_returned(self):
        for changes in ({'source': ''}, {'source': ' '}, {'id': None}, {'question': ''}):
            with self.subTest(changes=changes):
                self.assertEqual(retrieve(TextRetrievalStrategy([question(**changes)])), [])

    def test_empty_candidates_and_snapshot_isolation(self):
        self.assertEqual(retrieve(TextRetrievalStrategy([])), [])
        row = question()
        strategy = TextRetrievalStrategy([row])
        row['key_points'].append('后来变更')
        row['permission_status'] = 'restricted'
        self.assertEqual(retrieve(strategy)[0].key_points, ('List 保留顺序', 'Set 不保存重复元素'))
        self.assertEqual(retrieve(TextRetrievalStrategy([row])), [])

    def test_retrieve_signature_preserves_shared_contract(self):
        self.assertEqual(
            inspect.signature(TextRetrievalStrategy.retrieve),
            inspect.signature(RetrievalStrategy.retrieve),
        )


if __name__ == '__main__':
    unittest.main()
