import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from check_build_context import check_context, sentinel_paths, verify_export


class ContextExportTests(unittest.TestCase):
    def test_docker_probe_is_refused_outside_actions(self):
        with patch.dict(os.environ, {}, clear=True), patch('check_build_context.subprocess.run') as run:
            with self.assertRaises(ValueError):
                check_context('backend')
            run.assert_not_called()

    def test_missing_sources_and_leaked_sentinels_are_rejected(self):
        for component in ('backend', 'frontend'):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with self.assertRaises(RuntimeError):
                    verify_export(root, component)
                for name in ('Dockerfile', '.env.example', 'requirements-runtime.txt', 'package-lock.json'):
                    (root / name).write_text('synthetic-source')
                verify_export(root, component)
                for name in sentinel_paths(component):
                    path = root / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text('synthetic-probe')
                    with self.subTest(component=component, name=name), self.assertRaises(RuntimeError):
                        verify_export(root, component)
                    path.unlink()


if __name__ == '__main__':
    unittest.main()
