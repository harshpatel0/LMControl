# Disclaimer

Read this before running Kodo. By running it, you accept all of the below.

## 1. This gives an AI broad control of your PC

Kodo lets a model click, type, run hotkeys, drag, scroll, and execute arbitrary Python code on your machine. The `python` action and skill entry points run real subprocesses with real filesystem/network access. The `.kodo_venv` virtual environment is **not a sandbox** — it only keeps packages off your system Python install. It does not contain, isolate, or limit what code can do (read/write/delete files, hit the network, run other programs, etc.).

**Prompt injection is a real risk.** If the model reads adversarial content while completing a task (a malicious webpage, document, email, etc.), it may be tricked into taking actions you didn't intend — including via the `python` action. Be deliberate about what tasks you give it and what it's exposed to. Don't leave it unattended on sensitive accounts, financial sites, or with access to data you can't afford to lose or leak.

## 2. Your screen, UI tree, and taskbar are part of the "context"

On every step, Kodo's context provider reads:

- The full accessibility (UIA) tree of the active window — every visible button, text field, label, and value it can find
- The active window title
- Taskbar contents and pinned apps
- Installed application list
- Optionally, a screenshot of the active window (if `attach_screenshot_of_active_window` is enabled)

This is sent to whichever model provider you've configured for that model role, every single step, for the duration of the task.

## 3. Using a cloud provider sends that context to a third party

If you set any model role's `provider` to `anthropic` or `google` (see [docs/MODEL_PROVIDERS.md](docs/MODEL_PROVIDERS.md)), everything in section 2 — UI tree contents, window titles, taskbar entries, installed app names, and optionally screenshots — is transmitted to that provider's API for every step of every task.

- **No data masking or redaction occurs.** Whatever is on screen, in the active window's UI tree, or in your taskbar gets sent as-is.
- **Anthropic / Google's own terms of service govern what they do with that data**, including retention, training use, and human review. Read their terms before enabling a cloud provider.
- **Google's free tier in particular** has been documented as using submitted data for training and human review. If you're not comfortable with your desktop activity being reviewed by a third party, do not use a cloud provider's free tier — use Ollama (fully local) instead, or a paid tier with stricter data terms.
- This applies to **any** provider you configure, present or future, local or remote — by using a provider you agree to that provider's terms of service, and I am not responsible for what they receive, retain, train on, or do with it.

## 4. This is token-heavy and cloud usage can cost real money

The actor receives a large prompt every single step: the full (or diffed) UI tree, taskbar elements, accumulated history, loaded skill documentation, and the system prompt — and this repeats for every action in every step of a task, potentially dozens of times for a single run. Autonomy mode can run up to `max_total_iterations` (default 50) such calls per task, each one a full model request.

If you point any model role at a paid cloud provider:

- You will be billed per-token by that provider according to their pricing.
- A single task can realistically involve tens of thousands of input tokens and many separate API calls.
- Misbehaving loops, replans, and retries (which are common — see the README's "In Practice" section) multiply this further. The repeated-action guard and iteration caps reduce but do not eliminate this risk.
- **I am not responsible for any charges, overages, or billing surprises on your account.** Monitor your usage and set spending limits with your provider directly. If cost is a concern, use Ollama (free, local) instead.

## 5. General "no responsibility" statement

This is a personal project, built without formal scope planning or a safety review, made available as-is:

- I am not responsible for any damage, data loss, financial loss, security incident, unintended action, or any other consequence resulting from running this software — whether caused by bugs, model misbehavior, prompt injection, misconfiguration, or anything else.
- I am not responsible for what any model provider (local or remote) does with the data this app sends it, including training, retention, or human review.
- I am not responsible for any costs incurred through use of a paid model provider.
- Running this software, granting it accessibility/UI control, and configuring any model provider is entirely **your decision and your responsibility**.

If any of the above is unacceptable to you, do not run Kodo — or only run it with Ollama, in a disposable/sandboxed environment, with no sensitive data, accounts, or files accessible.

! SKILLS CAN READ YOUR ENVIRONMENT VARIABLES, THIS MEANS THAT IT CAN JUST READ YOUR API KEYS!