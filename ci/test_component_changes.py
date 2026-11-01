"""Offline path selection checks for independent component delivery."""

import unittest

from component_changes import classify


class ComponentChangesTests(unittest.TestCase):
    def test_component_changes_and_reverts_select_only_the_owner(self):
        for component in ('frontend', 'backend'):
            with self.subTest(component=component):
                self.assertEqual(classify([f'{component}/src/example', 'docs/ci-cd.md']), {component})

    def test_shared_and_unknown_paths_require_both_components(self):
        for path in ('deploy/nginx.conf', '.github/workflows/ci-cd.yml', 'ci/demo_smoke.py',
                     'requirements.txt', 'new-shared-file', 'AGENTS.md'):
            with self.subTest(path=path):
                self.assertEqual(classify([path]), {'backend', 'frontend'})

    def test_docs_only_or_empty_changes_do_not_release_images(self):
        self.assertEqual(classify(['README.md', 'docs/deployment.md', '']), set())
        self.assertEqual(classify([]), set())

    def test_manual_selection_is_explicit(self):
        self.assertEqual(classify([], 'frontend'), {'frontend'})
        self.assertEqual(classify([], 'backend'), {'backend'})
        self.assertEqual(classify([], 'all'), {'backend', 'frontend'})
        with self.assertRaises(ValueError):
            classify([], 'gateway')


if __name__ == '__main__':
    unittest.main()
