"""LLM provider configuration and factory."""

from ..config import get_settings
from .anthropic import AnthropicProvider
from .base import LLMProvider
from .openai import OpenAIProvider


def get_provider(
    provider: str | None = None, model: str | None = None
) -> LLMProvider:
    """
    Get an LLM provider instance based on configuration.

    Args:
        provider: Provider name override ("anthropic" or "openai")
        model: Model name override

    Returns:
        Configured LLMProvider instance

    Raises:
        ValueError: If provider is not supported or API key is missing
    """
    settings = get_settings()
    provider_name = provider or settings.llm_provider
    model_name = model or settings.default_model

    if provider_name == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            default_model=model_name,
        )
    elif provider_name == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            default_model=model_name,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_name}")
