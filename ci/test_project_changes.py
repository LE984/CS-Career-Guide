import unittest
from check_project_changes import evaluate, validate_record
import json


class ProjectGateTests(unittest.TestCase):
    def test_missing_document_fails(self):
        r=evaluate(['backend/career_platform/rag/service.py'])
        self.assertEqual(r['missing_documents'],['docs/implementation/04-interview-rag.md'])
        self.assertEqual(r['complete_tests'],['rag'])

    def test_bootstrap_does_not_claim_complete(self):
        r=evaluate(['backend/career_platform/rag/service.py','docs/implementation/04-interview-rag.md'],True)
        self.assertEqual(r['complete_tests'],[])
        self.assertEqual(r['missing_documents'],[])

    def test_shared_contract_requires_all_six_documents(self):
        r=evaluate(['backend/career_platform/contracts.py'])
        self.assertEqual(len(r['missing_documents']),6)
        self.assertEqual(len(r['complete_tests']),5)
        self.assertTrue(r['integration_test'])

    def test_test_file_does_not_exempt_implementation(self):
        r=evaluate(['backend/career_platform/records/service.py','some-status.json','docs/implementation/05-practice-records.md'])
        self.assertEqual(r['complete_tests'],['records'])

    def test_unknown_backend_code_fails_closed(self):
        r=evaluate(['backend/career_platform/new_bypass.py'])
        self.assertTrue(r['shared_changed'])
        self.assertEqual(len(r['missing_documents']),6)

    def test_docs_only_do_not_select_business_tests(self):
        self.assertEqual(evaluate(['docs/implementation/04-interview-rag.md'])['complete_tests'],[])

    def test_record_requires_all_fields_and_real_result(self):
        record=dict(commit='d12128b + dirty',command='python ci/project_acceptance.py',result='passed',environment='sqlite',scope='offline',limitations='no live model',evidence='output/result.json')
        def block(value): return '```acceptance-record\n'+json.dumps(value)+'\n```'
        self.assertIsNone(validate_record(block(record)))
        self.assertIsNotNone(validate_record(block(record),block(record)+'  '))
        for field in record:
            broken=dict(record);broken.pop(field)
            self.assertIsNotNone(validate_record(block(broken)))
        record['result']='scaffold-passed'
        self.assertIsNotNone(validate_record(block(record)))
        self.assertIsNone(validate_record(block(record),bootstrap=True))
