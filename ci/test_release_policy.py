import unittest

from release_policy import outputs, publication_allowed


class ReleasePolicyTests(unittest.TestCase):
    def environment(self, **changes):
        return dict(GITHUB_REF='refs/heads/master',
                    GITHUB_REPOSITORY='vacontinuejatotired/CS-Career-Guide',
                    GITHUB_EVENT_NAME='push', RELEASE_ENABLED='true', **changes)

    def test_first_merge_cannot_publish_with_an_absent_or_disabled_switch(self):
        environment = self.environment()
        for value in (None, '', 'false', 'True'):
            with self.subTest(value=value):
                environment['RELEASE_ENABLED'] = value
                self.assertFalse(publication_allowed(environment))

    def test_enabled_publication_still_requires_fork_master_and_release_event(self):
        for event in ('push', 'workflow_dispatch'):
            environment = self.environment()
            environment['GITHUB_EVENT_NAME'] = event
            self.assertTrue(publication_allowed(environment))
        for key, value in (('GITHUB_REF', 'refs/heads/codex/split-delivery'),
                           ('GITHUB_REPOSITORY', 'other/CS-Career-Guide'),
                           ('GITHUB_EVENT_NAME', 'pull_request')):
            environment = self.environment()
            environment[key] = value
            self.assertFalse(publication_allowed(environment))

    def test_output_and_invalid_tag_cannot_inject_another_output(self):
        self.assertEqual(outputs(self.environment(EXTRA_TAG='first-split')), 'publish=true\nextra_tag=first-split\n')
        for tag in ('invalid tag', 'tag\npublish=true', '$(command)'):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                outputs(self.environment(EXTRA_TAG=tag))


if __name__ == '__main__':
    unittest.main()
