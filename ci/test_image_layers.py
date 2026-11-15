"""Offline layout guards; real image identities/resources still require runner smoke."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ImageLayerTests(unittest.TestCase):
    def test_frontend_models_are_copied_before_application_in_separate_layer(self):
        text = (ROOT / 'frontend/Dockerfile').read_text()
        model = 'COPY public/models /usr/share/nginx/html/models'
        application = 'COPY --from=builder /build/frontend/dist /usr/share/nginx/html'
        self.assertLess(text.index(model), text.index('COPY nginx.conf'))
        self.assertLess(text.index(model), text.index(application))
        self.assertIn('npm run build && rm -rf dist/models', text)
        self.assertIn('--mount=type=cache,target=/root/.npm', text)
        self.assertIn('npm ci', text)

    def test_backend_wheels_are_ephemeral_not_retained_in_a_copy_layer(self):
        text = (ROOT / 'backend/Dockerfile').read_text()
        self.assertNotIn('COPY --from=builder /wheels', text)
        self.assertIn('--mount=type=bind,from=builder,source=/wheels,target=/wheels,ro', text)
        self.assertIn('--no-cache-dir --no-index --find-links=/wheels /wheels/*', text)
        self.assertIn('--mount=type=cache,target=/root/.cache/pip', text)
        self.assertIn('USER appuser', text)
        self.assertIn('docker-entrypoint.sh', text)


if __name__ == '__main__':
    unittest.main()
