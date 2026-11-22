"""Call GPT or Claude to translate Python into C++.

API keys come from the environment (OPENAI_API_KEY, ANTHROPIC_API_KEY), never from code.
Model names can be changed with OPENAI_MODEL and ANTHROPIC_MODEL.
"""

import os

from .extract import extract_cpp
from .prompts import SYSTEM_PROMPT, build_user_prompt

PROVIDERS = ("openai", "anthropic")
DEFAULT_MODELS = {"openai": "gpt-4o", "anthropic": "claude-sonnet-4-5"}
MAX_TOKENS = 4096


def model_for(provider: str) -> str:
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider {provider!r}; choose one of {', '.join(PROVIDERS)}.")
    return os.getenv(f"{provider.upper()}_MODEL", DEFAULT_MODELS[provider])


def _ask_openai(python_code: str, model: str) -> str:
    from openai import OpenAI  # imported here so tests and `verify` need no API packages

    client = OpenAI()
    reply = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(python_code)},
        ],
    )
    return reply.choices[0].message.content or ""


def _ask_anthropic(python_code: str, model: str) -> str:
    import anthropic

    client = anthropic.Anthropic()
    reply = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_prompt(python_code)}],
    )
    return "".join(block.text for block in reply.content if block.type == "text")


_CALLERS = {"openai": _ask_openai, "anthropic": _ask_anthropic}


def translate(python_code: str, provider: str = "anthropic") -> str:
    """Translate Python source into C++ source with the chosen provider."""
    model = model_for(provider)
    return extract_cpp(_CALLERS[provider](python_code, model))
