"""Build model connection options from Django's environment settings."""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def get_llm_kwargs(model_setting="LLM_MODEL"):
    names = ("LLM_API_KEY", "LLM_BASE_URL", model_setting)
    missing = [name for name in names if not getattr(settings, name, "")]
    if missing:
        raise ImproperlyConfigured(f"Set environment variables: {', '.join(missing)}")
    return {
        "api_key": settings.LLM_API_KEY,
        "base_url": settings.LLM_BASE_URL,
        "model": getattr(settings, model_setting),
        "timeout": settings.LLM_TIMEOUT,
    }
