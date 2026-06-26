import os

from .base import ModelProvider, ChatMessage, ChatResponse
from utils.logger import logger
import anthropic as _anthropic
from settings.settings import settings

import time

DO_THINKING = False

if settings.orchestrator.use_autonomy_mode:
    if settings.models.autonomy_actor.thinking:
        DO_THINKING = True
else:
    if settings.models.actor.thinking:
        DO_THINKING = True


class AnthropicProvider(ModelProvider):
    """Provider for Anthropic's Claude models. Uses anthropic Python SDK.
    Reads API key from environment variable at init time.
    """

    def __init__(
        self, api_key_env_var: str = "ANTHROPIC_API_KEY", base_url: str | None = None
    ):
        try:
            import anthropic as _anthropic
        except ImportError:
            raise ImportError(
                "Anthropic-SDK is not installed. Run: pip install anthropic"
            )

        api_key = os.environ.get(api_key_env_var)
        if not api_key:
            raise ValueError(
                f"Anthropic API key not found in environment variable '{api_key_env_var}'. "
                f"Set it and restart."
            )
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = _anthropic.Anthropic(**kwargs)

    def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatResponse:

        timer_start = time.monotonic()

        system_prompt = None
        api_messages = []
        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
                continue

            role = "assistant" if msg.role == "assistant" else "user"
            content = []
            if msg.content:
                content.append({"type": "text", "text": msg.content})
            if msg.images:
                for img_b64 in msg.images:
                    content.append(
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": img_b64,
                            },
                        }
                    )
            api_messages.append({"role": role, "content": content})

        call_kwargs = {
            "model": model,
            "messages": api_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
        }

        if system_prompt:
            call_kwargs["system"] = system_prompt
        if DO_THINKING:
            call_kwargs["thinking"] = {"type": "adaptive"}
            call_kwargs["temperature"] = (
                1.0  # Enabling Thinking forces temperature to 1.0
            )
            call_kwargs["max_tokens"] = 16384
        if settings.model_providers.effort:
            call_kwargs["output_config"] = {
                "effort": settings.model_providers.anthropic.effort
            }

        try:
            response = self._client.messages.create(**call_kwargs)
        except _anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise

        content = ""
        thinking = None
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "thinking":
                thinking = (thinking or "") + block.thinking

        elapsed_time = int((time.monotonic() - timer_start) * 1000)

        return ChatResponse(
            content=content.strip(),
            thinking=thinking,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            total_duration_ms=elapsed_time,
        )
