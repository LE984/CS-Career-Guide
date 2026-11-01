import unittest
from check_project_changes import evaluate, validate_record, workflow_delivery_only, DELIVERY_WORKFLOWS
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

    def test_delivery_workflow_does_not_claim_business_complete_or_require_database_runner(self):
        r = evaluate(['.github/workflows/ci-cd.yml', 'deploy/nginx.conf',
                      'frontend/Dockerfile', 'backend/Dockerfile'], delivery_workflows=DELIVERY_WORKFLOWS)
        self.assertEqual(r['complete_tests'], [])
        self.assertFalse(r['integration_test'])
        self.assertFalse(r['acceptance_required'])

    def test_delivery_paths_never_exempt_mixed_business_or_fixed_gate_changes(self):
        for path in ('backend/career_platform/contracts.py', 'backend/career_platform/tests/test_scaffold.py',
                     'ci/project_acceptance.py', 'ci/project_ci.py', 'ci/project_modules.json',
                     'ci/check_project_changes.py', '.github/workflows/career-platform.yml',
                     '.github/unknown-workflow.yml'):
            with self.subTest(path=path):
                r = evaluate(['.github/workflows/ci-cd.yml', path], delivery_workflows=DELIVERY_WORKFLOWS)
                self.assertTrue(r['acceptance_required'])
                self.assertEqual(len(r['complete_tests']), 5)
                self.assertTrue(r['integration_test'])
        for path in ('backend/career_platform/rag/service.py',
                     'frontend/src/views/career-platform/Practice.vue'):
            r = evaluate(['.github/workflows/ci-cd.yml', path], delivery_workflows=DELIVERY_WORKFLOWS)
            self.assertEqual(r['complete_tests'], ['rag'])
            self.assertTrue(r['acceptance_required'])

    def test_frontend_static_changes_do_not_select_backend_database_acceptance(self):
        self.assertFalse(evaluate(['frontend/src/styles.css'])['acceptance_required'])
        self.assertTrue(evaluate(['backend/users/views.py'])['acceptance_required'])

    def test_workflow_test_commands_and_guards_cannot_use_delivery_exemption(self):
        import copy
        import yaml
        before = {'jobs': {c + '-test': {'runs-on': 'ubuntu-24.04', 'steps': [
            {'run': 'python -m django test' if c == 'backend' else 'node --test tests/*.test.mjs'}]}
            for c in ('backend', 'frontend')}}
        after = copy.deepcopy(before)
        after['jobs']['frontend-image'] = {'steps': [{'run': 'build frontend'}]}
        self.assertTrue(workflow_delivery_only(yaml.safe_dump(before), yaml.safe_dump(after)))
        for change in ('command', 'skip', 'continue', 'delete'):
            changed = copy.deepcopy(after)
            job = changed['jobs']['backend-test']
            if change == 'command': job['steps'][0]['run'] = 'echo bypass'
            elif change == 'skip': job['if'] = 'false'
            elif change == 'continue': job['continue-on-error'] = True
            else: del changed['jobs']['backend-test']
            with self.subTest(change=change):
                self.assertFalse(workflow_delivery_only(yaml.safe_dump(before), yaml.safe_dump(changed)))
        self.assertTrue(evaluate(['.github/workflows/ci-cd.yml'])['integration_test'])

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
