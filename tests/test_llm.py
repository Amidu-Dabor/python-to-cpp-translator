"""The LLM layer is tested with the API call replaced, so no keys or network are needed."""

import pytest

from translator import llm
from translator.prompts import build_user_prompt


def test_unknown_provider_is_rejected():
    with pytest.raises(ValueError):
        llm.model_for("gemini")


def test_model_can_be_overridden_from_the_environment(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_MODEL", "my-model")
    assert llm.model_for("anthropic") == "my-model"


def test_translate_sends_the_code_and_returns_extracted_cpp(monkeypatch):
    seen = {}

    def fake(code, model):
        seen.update(code=code, model=model)
        return "Sure!\n```cpp\nint main(){}\n```"

    monkeypatch.setitem(llm._CALLERS, "openai", fake)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    assert llm.translate("print(1)", "openai") == "int main(){}\n"
    assert seen == {"code": "print(1)", "model": "gpt-4o"}


def test_user_prompt_contains_the_python_source():
    assert "```python\nprint(1)\n```" in build_user_prompt("print(1)")
