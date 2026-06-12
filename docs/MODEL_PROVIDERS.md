# Model Providers - Choosing, Configuring, and Using

Kodo supports multiple model backends via a pluggable provider abstraction.
Each of the four model roles (`skill_installation`, `planner`, `actor`, `autonomy_actor`)
can use a **different provider** independently.

---

## Choosing a Provider

Set the `provider` field on each model role in `settings.json`:

```json
{
  "models": {
    "planner": { "provider": "anthropic", "model_name": "claude-sonnet-4-20250514", ... },
    "actor":   { "provider": "ollama",    "model_name": "gemma4:e4b", ... },
    "autonomy_actor": { "provider": "google", "model_name": "gemini-2.5-flash", ... }
  }
}
```

You can mix providers arbitrarily, each role resolves its own provider independently at call time.

---

## Disclaimer

By using an external provider, you agree to their terms of service.

By providers, I mean any external provders, local providers, providers I included support for in the app, and the Ollama local provider.

I am not responsible for the data that these providers receive, and process in the app. 
I am not responsible if the data that the app has provided to their AI model.
I am not responsible for your data being used for training, data collection, or human review. You should have read their terms of service.

I am not responsible, legally, or financially, or any other aspect, when you use the app.

By using this app, you are aware that this is in development, and may cause an excessive charge on your account.
By using the Gemini AI provider in its free plan, you clearly understand that according to their Terms of Service: **YOUR DATA WILL BE COLLECTED, TRAINED ON, AND HUMAN REVIEWED ACCORDING TO THEIR GUIDELINES. I AM NOT RESPONSIBLE FOR THIS. PLEASE BE CAREFUL WITH WHAT THE ORCHESTRATORS AND CONTEXT PROVIDERS COLLECT ABOUT YOUR PC**

That said, I am not personally collecting your PC information, the data collected is sent to the model, and that's it.

## Configuring Each Provider

### Ollama (local models)

```json
{
  "active_model_provider": "ollama",
  "model_providers": {
    "ollama": {
      "server_url": "192.168.68.254:11434",
      "timeout": 120
    }
  },
  "models": {
    "actor": {
      "provider": "ollama",
      "model_name": "gemma4:e4b",
      "temperature": 0.5,
      "keep_alive": 60,
      "thinking": true,
      "attach_screenshot_of_active_window": true
    }
  }
}
```

Ollama-specific params (`keep_alive`, `output_format`) are accepted via `**kwargs`
and silently ignored by other providers.

### Anthropic (Claude)

Set the environment variable first:

```bash
set ANTHROPIC_API_KEY=sk-ant-...
```

You can also set the corresponding key and its value in a .env file, this will be picked up without needing to set the environment variable.
Ensure your .env file stays hidden, unless you're feeling very generious.

Then configure:

```json
{
  "model_providers": {
    "anthropic": {
      "api_key_env_var": "ANTHROPIC_API_KEY",
      "base_url": null
    }
  },
  "models": {
    "planner": {
      "provider": "anthropic",
      "model_name": "claude-sonnet-4-20250514",
      "temperature": 0.3
    }
  }
}
```

The SDK reads your key from the env var specified in `api_key_env_var`.
`base_url` is optional (useful for API proxies).

### Google (Gemini)

Set the environment variable first:

```bash
set GOOGLE_API_KEY=AIza...
```

You can also set the corresponding key and its value in a .env file, this will be picked up without needing to set the environment variable.
Ensure your .env file stays hidden, unless you're feeling very generious.

Then configure:

```json
{
  "model_providers": {
    "google": {
      "api_key_env_var": "GOOGLE_API_KEY"
    }
  },
  "models": {
    "autonomy_actor": {
      "provider": "google",
      "model_name": "gemini-2.5-flash",
      "temperature": 0.5
    }
  }
}
```

#### Warning

Google has said they will use model requests made on the Free Tier to train their models, including human review. Please do not send sensitive data, absolutely no data masking occurs when it is sent to Google, Google will see your active window, a screenshot of your desktop, and your taskbar. If you can't trust an outside provider. Please use Ollama.

The project is still in development, uses a lot of input tokens and requires reasoning, this is all intensive for your model, and so, you would be billed accordingly if using a paid plan.

---

## Using the Provider Directly

All existing code (`ActorModel.run()`, `PlannerModel.run()`, `SkillInstallationMode.run()`)
resolves the provider internally — no changes needed in your task code.

But you can also use the provider directly for custom logic:

```python
from models.provider import get_provider, ChatMessage
from settings.settings import settings

cfg = settings.models.planner
provider = get_provider(cfg)

response = provider.chat(
    messages=[
        ChatMessage(role="system", content="You are a planner"),
        ChatMessage(role="user", content="Plan this task for me"),
    ],
    model=cfg.model_name,
    temperature=cfg.temperature,
)

print(response.content)       # the text output
print(response.thinking)      # chain-of-thought (if supported)
print(response.input_tokens, response.output_tokens)
```

---

## Adding a New Provider

1. **Create the provider class** in `models/provider/` that implements `ModelProvider.chat()`:

```python
# models/provider/deepseek_provider.py
from .base import ModelProvider, ChatMessage, ChatResponse

class DeepseekProvider(ModelProvider):
    def __init__(self, api_key: str, base_url: str | None = None):
        import openai
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url or "https://api.deepseek.com",
        )

    def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatResponse:
        api_messages = [
            {"role": m.role, "content": m.content} for m in messages
        ]
        response = self.client.chat.completions.create(
            model=model,
            messages=api_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        return ChatResponse(
            content=choice.message.content.strip(),
            thinking=None,
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
        )
```

2. **Register it in the factory** in `models/provider/__init__.py`:

```python
from .deepseek_provider import DeepseekProvider

def _create_deepseek_provider() -> DeepseekProvider:
    cfg = settings.model_providers.deepseek
    return DeepseekProvider(
        api_key=os.environ.get(getattr(cfg, "api_key_env_var", "DEEPSEEK_API_KEY")),
        base_url=getattr(cfg, "base_url", None),
    )

# Add to factory_map:
"deepseek": _create_deepseek_provider,
```

3. **Add its config section** to `model_providers` in `settings.json`:

```json
{
  "model_providers": {
    "deepseek": {
      "api_key_env_var": "DEEPSEEK_API_KEY",
      "base_url": "https://api.deepseek.com"
    }
  }
}
```

4. **Use it** on any model role:

```json
{
  "models": {
    "actor": { "provider": "deepseek", "model_name": "deepseek-chat", ... }
  }
}
```

That's it — no other file in the codebase needs to know about your new provider.
