import unittest

from delivery_summary import summarize


class DeliverySummaryTests(unittest.TestCase):
    def needs(self, components=('frontend',), publish=False):
        result = {name: {'result': 'success'} for name in ('changes', 'platform-gates', 'delivery-checks')}
        result['changes']['outputs'] = {c: str(c in components).lower() for c in ('backend', 'frontend')}
        result['changes']['outputs']['publish'] = str(publish).lower()
        for c in ('backend', 'frontend'):
            for suffix in ('test', 'image'):
                result[c + '-' + suffix] = {'result': 'success' if c in components else 'skipped'}
            result['publish-' + c] = {'result': 'success' if publish and c in components else 'skipped'}
            result['deploy-' + c] = {'result': 'skipped'}
        result['integration'] = {'result': 'success' if len(components) == 2 else 'skipped'}
        return result

    def test_single_component_build_only_and_publication_are_reported_separately(self):
        for component in ('backend', 'frontend'):
            for publish in (False, True):
                lines, errors = summarize(self.needs((component,), publish), {})
                self.assertEqual(errors, [])
                self.assertIn('SKIPPED', '\n'.join(lines))

    def test_shared_integration_failure_or_skip_fails_summary(self):
        for value in ('failure', 'skipped', 'cancelled'):
            needs = self.needs(('backend', 'frontend'))
            needs['integration']['result'] = value
            self.assertTrue(summarize(needs, {})[1])

    def test_unselected_publication_is_a_failure(self):
        needs = self.needs()
        needs['publish-backend']['result'] = 'success'
        self.assertTrue(summarize(needs, {})[1])

    def test_failed_or_missing_selected_checks_cannot_pass(self):
        for name in ('changes', 'platform-gates', 'delivery-checks', 'frontend-test', 'frontend-image'):
            needs = self.needs()
            needs[name]['result'] = 'failure'
            self.assertTrue(summarize(needs, {})[1])

    def test_component_deploy_switch_is_independent(self):
        needs = self.needs(('backend', 'frontend'), True)
        env = {'SYNC_ENABLED': 'true', 'DEPLOY_BACKEND_ENABLED': 'true'}
        self.assertTrue(summarize(needs, env)[1])
        needs['deploy-backend']['result'] = 'success'
        self.assertEqual(summarize(needs, env)[1], [])


if __name__ == '__main__':
    unittest.main()
