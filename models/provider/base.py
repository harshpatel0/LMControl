from abc import ABC, abstractmethod
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ChatMessage:
    role: str
    content: str
    images: list[str] | None = None


@dataclass
class ChatResponse:
    content: str
    thinking: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_duration_ms: float = 0.0
    load_duration_ms: float = 0.0


class ModelProvider(ABC):

    @abstractmethod
    def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatResponse:
        raise NotImplementedError
