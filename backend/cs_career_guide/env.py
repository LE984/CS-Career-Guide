"""Typed environment settings shared by deployment configuration."""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


def env(name, default=None, *, aliases=(), required=False):
    value = next((os.environ[key] for key in (name, *aliases) if key in os.environ), default)
    if required and (value is None or not str(value).strip()):
        raise ImproperlyConfigured(f"Set the {name} environment variable")
    return value


def env_bool(name, default=False):
    value = str(env(name, str(default))).strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ImproperlyConfigured(f"{name} must be a boolean")


def env_int(name, default, *, minimum=0, maximum=None):
    try:
        value = int(env(name, default))
    except (TypeError, ValueError) as exc:
        raise ImproperlyConfigured(f"{name} must be an integer") from exc
    if value < minimum or (maximum is not None and value > maximum):
        raise ImproperlyConfigured(f"{name} is outside the allowed range")
    return value


def env_list(name, default=""):
    return [value.strip() for value in env(name, default).split(",") if value.strip()]


def env_path(name, default, *, base_dir):
    value = Path(os.path.expandvars(str(env(name, default)))).expanduser()
    return value if value.is_absolute() else Path(base_dir) / value
