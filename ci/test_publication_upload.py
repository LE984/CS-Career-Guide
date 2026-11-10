"""发布记录允许一次重试，但不能绕过最终归档失败。"""
import unittest
from pathlib import Path
import yaml


class PublicationUploadTests(unittest.TestCase):
    def test_both_publishers_retry_and_fail_closed(self):
        workflow = yaml.safe_load((Path(__file__).resolve().parents[1] / '.github/workflows/ci-cd.yml').read_text(encoding='utf-8'))
        for component in ('backend', 'frontend'):
            with self.subTest(component=component):
                job = workflow['jobs'][f'publish-{component}']
                self.assertNotIn('continue-on-error', job)
                first = next(s for s in job['steps'] if s.get('id') == 'publication-upload')
                retry = next(s for s in job['steps'] if s.get('name') == 'Retry publication record upload')
                self.assertTrue(first['continue-on-error'])
                self.assertEqual(retry['if'], "always() && steps.publication-upload.outcome == 'failure'")
                self.assertFalse(retry.get('continue-on-error', False))
                self.assertEqual(retry['uses'], 'actions/upload-artifact@v4')
                self.assertEqual(retry['with']['name'], first['with']['name'])
                self.assertEqual(retry['with']['path'], first['with']['path'])
                self.assertTrue(retry['with']['overwrite'])
                self.assertEqual(retry['with']['if-no-files-found'], 'error')
                self.assertEqual(first['timeout-minutes'], 5)
                self.assertEqual(retry['timeout-minutes'], 5)
                self.assertEqual(job['outputs']['digest'], '${{ steps.record.outputs.digest }}')
