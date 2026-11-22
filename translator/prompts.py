"""Prompts sent to the LLM when translating Python into C++."""

SYSTEM_PROMPT = (
    "You are an expert C++ performance engineer. You port Python programs to "
    "high-performance, standard C++17. Respond only with the C++ code, in a single "
    "```cpp code block, with no explanation.\n"
    "Requirements:\n"
    "- The program must compile with `clang++ -O3 -std=c++17` and include every header it uses.\n"
    "- It must print exactly the same output as the Python program, apart from timing values.\n"
    "- Choose integer types wide enough for every value. Python integers never overflow; "
    "C++ integers do, so watch for overflow and narrowing conversions.\n"
    "- Make it as fast as possible, including better algorithms where the result is identical."
)


def build_user_prompt(python_code: str) -> str:
    """Wrap the Python source in the instruction sent as the user message."""
    return (
        "Rewrite this Python code in C++ with the fastest possible implementation that "
        "produces identical output in the fastest possible time.\n\n"
        f"```python\n{python_code}\n```"
    )
