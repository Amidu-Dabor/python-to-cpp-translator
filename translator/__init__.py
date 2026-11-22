"""Translate Python into high-performance C++ with LLMs, then compile and verify it."""

from .build import compile_cpp, find_compiler, run_executable, run_python
from .extract import extract_cpp
from .verify import compare, normalise

__all__ = ["compile_cpp", "find_compiler", "run_executable", "run_python",
           "extract_cpp", "compare", "normalise", "translate"]


def translate(python_code: str, provider: str = "anthropic") -> str:
    from .llm import translate as _translate
    return _translate(python_code, provider)
