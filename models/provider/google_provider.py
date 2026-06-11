import os
import io
import base64

from .base import ModelProvider, ChatMessage, ChatResponse


class GoogleProvider(ModelProvider):
    """Provider for Google Gemini models. Uses google-genai SDK.
    Reads API key from environment variable at init time.
    """

    def __init__(self, api_key_env_var: str = "GOOGLE_API_KEY"):
        try:
            from google import genai
        except ImportError:
            raise ImportError(
                "google-genai is not installed. Run: pip install google-genai"
            )

        try:
            from PIL import Image

            self._Image = Image
        except ImportError:
            raise ImportError("Pillow is not installed. Run: pip install Pillow")

        api_key = os.environ.get(api_key_env_var)
        if not api_key:
            raise ValueError(
                f"Google AI API key not found in environment variable '{api_key_env_var}'. "
                f"Set it and restart."
            )

        self._client = genai.Client(api_key=api_key)
        self._genai = genai

    def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatResponse:
        from google.genai import types

        system_prompt = None
        history = []

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
                continue

            parts = []
            if msg.content:
                parts.append(types.Part.from_text(text=msg.content))
            if msg.images:
                for img_b64 in msg.images:
                    image_bytes = base64.b64decode(img_b64)
                    parts.append(
                        types.Part.from_bytes(data=image_bytes, mime_type="image/png")
                    )

            role = "model" if msg.role == "assistant" else "user"
            history.append(types.Content(role=role, parts=parts))

        if not history:
            raise ValueError("No user/assistant messages provided.")

        config_kwargs = {"temperature": temperature}
        if max_tokens:
            config_kwargs["max_output_tokens"] = max_tokens
        if system_prompt:
            config_kwargs["system_instruction"] = system_prompt

        config = types.GenerateContentConfig(**config_kwargs)

        response = self._client.models.generate_content(
            model=model,
            contents=history,
            config=config,
        )

        try:
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count
        except Exception:
            input_tokens = output_tokens = 0

        text = response.text.strip() if response.text else ""

        return ChatResponse(
            content=text,
            thinking=None,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
