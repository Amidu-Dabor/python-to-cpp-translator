"""Pull the C++ source out of an LLM reply."""

import re

_FENCE = re.compile(r"```[ \t]*(?:cpp|c\+\+|cc|cxx)?[ \t]*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_cpp(reply: str) -> str:
    """Return the C++ code from a model reply.

    Models usually wrap code in a ```cpp fence, sometimes with text around it.
    If there are several fenced blocks, the longest is taken as the program.
    If there is no fence, the whole reply is treated as code.
    """
    blocks = [b.strip() for b in _FENCE.findall(reply)]
    code = max(blocks, key=len) if blocks else reply.strip()
    if not code:
        raise ValueError("The model reply did not contain any C++ code.")
    return code + "\n"
