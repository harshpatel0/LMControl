import os
import io

from .base import ModelProvider, ChatMessage, ChatResponse
from utils.logger import logger


class GoogleProvider(ModelProvider):
    def __init__(self, api_key_env_var: str = "GOOGLE_API_KEY"):
        import google.generativeai as genai
        api_key = os.environ.get(api_key_env_var)
        if not api_key:
            raise ValueError(
                f"Google AI API key not found in environment variable '{api_key_env_var}'. "
                f"Set it and restart."
            )
        genai.configure(api_key=api_key)
        self._genai = genai

    def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatResponse:
        genai = self._genai

        system_prompt = None
        history = []

        for msg in messages:
            parts = []
            if msg.content:
                parts.append(msg.content)
            if msg.images:
                import base64
                from PIL import Image
                for img_b64 in msg.images:
                    image_bytes = base64.b64decode(img_b64)
                    parts.append(Image.open(io.BytesIO(image_bytes)))

            if msg.role == "system":
                system_prompt = msg.content
            else:
                role = "model" if msg.role == "assistant" else "user"
                history.append({"role": role, "parts": parts})

        generation_config = {"temperature": temperature}
        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens

        model_instance = self._genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config,
            system_instruction=system_prompt,
        )

        if len(history) <= 1:
            contents = history[-1]["parts"] if history else [""]
            response = model_instance.generate_content(contents)
        else:
            last = history.pop()
            chat = model_instance.start_chat(history=history)
            response = chat.send_content(last["parts"])

        try:
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count
        except Exception:
            input_tokens = output_tokens = 0

        return ChatResponse(
            content=response.text.strip() if response.text else "",
            thinking=None,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
