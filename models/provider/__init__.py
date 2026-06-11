"""Model provider abstraction layer.

Usage:
    from models.provider import get_provider, ChatMessage, ChatResponse

    provider = get_provider(model_config)
    response = provider.chat(
        messages=[ChatMessage(role="user", content="Hello")],
        model="gemma4:e4b",
        temperature=0.7,
    )
"""

from .base import ModelProvider, ChatMessage, ChatResponse
from .ollama_provider import OllamaProvider
from .anthropic_provider import AnthropicProvider
from .google_provider import GoogleProvider
from settings.settings import settings

_PROVIDER_CACHE: dict[str, ModelProvider] = {}


def get_provider(model_config=None):
    """Get or create a ModelProvider instance.

    Args:
        model_config: A SimpleNamespace with at least a `provider` field
                      (e.g. settings.models.actor). If None, uses
                      settings.active_model_provider.

    Returns:
        A ModelProvider instance (OllamaProvider, AnthropicProvider, or GoogleProvider).
    """
    if model_config is None:
        provider_name = getattr(settings, "active_model_provider", "ollama")
    else:
        provider_name = getattr(model_config, "provider", None) or getattr(settings, "active_model_provider", "ollama")

    factory_map = {
        "ollama": _create_ollama_provider,
        "anthropic": _create_anthropic_provider,
        "google": _create_google_provider,
    }

    if provider_name not in factory_map:
        raise ValueError(
            f"Unknown model provider '{provider_name}'. "
            f"Available: {', '.join(factory_map.keys())}"
        )

    if provider_name not in _PROVIDER_CACHE:
        _PROVIDER_CACHE[provider_name] = factory_map[provider_name]()

    return _PROVIDER_CACHE[provider_name]


def clear_provider_cache():
    _PROVIDER_CACHE.clear()


def _create_ollama_provider() -> OllamaProvider:
    cfg = settings.model_providers.ollama
    return OllamaProvider(
        server_url=getattr(cfg, "server_url", "localhost:11434"),
        timeout=getattr(cfg, "timeout", 120),
    )


def _create_anthropic_provider() -> AnthropicProvider:
    cfg = settings.model_providers.anthropic
    return AnthropicProvider(
        api_key_env_var=getattr(cfg, "api_key_env_var", "ANTHROPIC_API_KEY"),
        base_url=getattr(cfg, "base_url", None),
    )


def _create_google_provider() -> GoogleProvider:
    cfg = settings.model_providers.google
    return GoogleProvider(
        api_key_env_var=getattr(cfg, "api_key_env_var", "GOOGLE_API_KEY"),
    )
