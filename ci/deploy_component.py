"""Server-local single-service digest deployment/rollback; no AI configuration transfer."""

import argparse

from sync_runtime_env import apply_remote


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-path', required=True)
    parser.add_argument('--component', choices=('frontend', 'backend'), required=True)
    parser.add_argument('--image', required=True)
    args = parser.parse_args()
    apply_remote(args.env_path, {}, args.component, args.image)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        # Compose/configuration failures may hold secrets; diagnose privately.
        raise SystemExit('Component activation failed; inspect the server privately')
