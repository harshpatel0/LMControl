import ollama
import time
import random

from .base import ModelProvider, ChatMessage, ChatResponse
from utils.logger import logger
from utils.loading_text import get_loading_text


class OllamaProvider(ModelProvider):
    """Provider for locally-hosted Ollama models. Connects via ollama Python SDK."""

    def __init__(self, server_url: str = "localhost:11434", timeout: int = 120):
        self.server_url = server_url
        self.timeout = timeout
        self.client = ollama.Client(host=server_url)

    def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float,
        max_tokens: int | None = None,
        keep_alive: int = 0,
        output_format: str = "json",
        **kwargs,
    ) -> ChatResponse:
        ollama_messages = []
        for msg in messages:
            entry = {"role": msg.role, "content": msg.content}
            if msg.images:
                entry["images"] = msg.images
            ollama_messages.append(entry)

        options = {"temperature": temperature}
        if max_tokens:
            options["num_predict"] = max_tokens

        think = kwargs.get("thinking", False)

        last_error = None
        for attempt in range(3):
            try:
                logger.info(get_loading_text())
                response = self.client.chat(
                    model=model,
                    messages=ollama_messages,
                    options=options,
                    keep_alive=keep_alive,
                    format=output_format,
                    think=think,
                )

                if response and hasattr(response, "message"):
                    response.message.content = response.message.content.strip()

                rd = response.model_dump()
                content = rd["message"]["content"]
                thinking = rd["message"].get("thinking") or rd["message"].get("reasoning")
                total_duration = int(rd.get("total_duration", 0)) / 1_000_000
                load_duration = int(rd.get("load_duration", 0)) / 1_000_000

                return ChatResponse(
                    content=content,
                    thinking=thinking,
                    input_tokens=int(rd.get("prompt_eval_count", 0)),
                    output_tokens=int(rd.get("eval_count", 0)),
                    total_duration_ms=total_duration,
                    load_duration_ms=load_duration,
                )

            except KeyboardInterrupt:
                logger.warning("CTRL+C pressed, interrupting request and exiting")
                raise

            except ollama.ResponseError as e:
                last_error = e
                logger.warning(f"Ollama HTTP {e.status_code} (attempt {attempt+1}/3): {e.error}")
                if e.status_code == 400:
                    raise

            except Exception as e:
                last_error = e
                logger.warning(f"Ollama error (attempt {attempt+1}/3): {e}")

            if attempt < 2:
                sleep_time = (2 ** attempt) + random.uniform(0, 1)
                logger.info(f"Retrying in {sleep_time:.1f}s...")
                time.sleep(sleep_time)

        raise last_error or ConnectionError(
            f"Failed to reach Ollama at {self.server_url} after 3 attempts"
        )
