"""反馈证据校验的离线对抗用例，材料全部虚构。"""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from career_platform.rag.feedback import InvalidFeedback, validate_feedback


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.answer = 'List 保留顺序，但我还不清楚 Set。'
        self.evidence = {'source_id': 'fictional-question', 'field_path': 'key_points[0]', 'quote': 'List 保留顺序'}
        self.snapshot = {'question_id': 'fictional-question', 'key_points': ['List 保留顺序', 'Set 去重'], 'evidence': [self.evidence]}
        self.feedback = {'answer_quote': 'List 保留顺序', 'key_points_covered': ['List 保留顺序'], 'missing_points': [], 'evidence': [self.evidence], 'follow_up': None}

    def validate(self):
        return validate_feedback(answer=self.answer, snapshot=self.snapshot, feedback=self.feedback)

    def test_valid_and_deep_copy(self):
        original = deepcopy(self.feedback)
        result = self.validate()
        self.assertEqual(result, original)
        result['evidence'][0]['quote'] = 'changed'
        self.assertEqual(self.feedback, original)
        self.assertEqual(self.snapshot['evidence'][0]['quote'], 'List 保留顺序')

    def test_quote_must_be_actual_nonblank_substring(self):
        for quote in ('模型虚构回答', '', ' ', None, 5):
            with self.subTest(quote=quote):
                self.feedback['answer_quote'] = quote
                with self.assertRaises(InvalidFeedback): self.validate()

    def test_blank_answer(self):
        self.answer = ' '
        with self.assertRaises(InvalidFeedback): self.validate()

    def test_missing_extra_and_wrong_types(self):
        original = deepcopy(self.feedback)
        for bad in (None, [], dict(original, score=100), {k: v for k, v in original.items() if k != 'follow_up'}, dict(original, key_points_covered='List 保留顺序')):
            self.feedback = bad
            with self.subTest(bad=bad), self.assertRaises(InvalidFeedback): self.validate()

    def test_fabricated_duplicate_or_conflicting_points(self):
        for changes in ({'missing_points': ['虚构要点']}, {'key_points_covered': ['List 保留顺序'] * 2}, {'missing_points': ['List 保留顺序']}):
            original = deepcopy(self.feedback)
            self.feedback.update(changes)
            with self.assertRaises(InvalidFeedback): self.validate()
            self.feedback = original

    def test_all_claimed_points_need_evidence(self):
        self.feedback['missing_points'] = ['Set 去重']
        with self.assertRaises(InvalidFeedback): self.validate()
        second = {'source_id': 'fictional-question', 'field_path': 'key_points[1]', 'quote': 'Set 去重'}
        self.snapshot['evidence'].append(second)
        self.feedback['evidence'].append(second)
        self.assertEqual(self.validate()['missing_points'], ['Set 去重'])

    def test_empty_or_forged_evidence(self):
        for evidence in ([], None, [dict(self.evidence, quote='假依据')], [dict(self.evidence, source_id='other')], [dict(self.evidence, field_path='key_points[99]')]):
            self.feedback['evidence'] = evidence
            with self.subTest(evidence=evidence), self.assertRaises(InvalidFeedback): self.validate()

    def test_source_description_not_key_point_evidence(self):
        item = dict(self.evidence, field_path='source')
        self.snapshot['evidence'] = [item]
        self.feedback['evidence'] = [item]
        with self.assertRaises(InvalidFeedback): self.validate()

    def test_snapshot_evidence_must_resolve_to_current_question(self):
        for changes in ({'source_id': 'other'}, {'field_path': 'key_points[01]'}, {'quote': '不属于该要点'}):
            item = dict(self.evidence, **changes)
            self.snapshot['evidence'] = [item]
            self.feedback['evidence'] = [item]
            with self.subTest(changes=changes), self.assertRaises(InvalidFeedback): self.validate()

    def test_follow_up_requires_future_contract_review(self):
        for follow_up in ('请举例', {'origin': 'catalog', 'question': '请举例'}, {'origin': 'generated', 'question': '请举例', 'question_id': 'fake'}, {'origin': 'generated', 'question': ' '}):
            self.feedback['follow_up'] = follow_up
            with self.subTest(follow_up=follow_up), self.assertRaises(InvalidFeedback): self.validate()

    def test_rejection_does_not_echo_private_model_output(self):
        self.feedback['answer_quote'] = 'PRIVATE-MODEL-OUTPUT'
        with self.assertRaises(InvalidFeedback) as error: self.validate()
        self.assertNotIn('PRIVATE', str(error.exception))


if __name__ == '__main__':
    unittest.main()
