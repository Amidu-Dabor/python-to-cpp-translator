import pytest

from translator.extract import extract_cpp


def test_takes_code_from_cpp_fence():
    reply = "Here you go:\n```cpp\nint main() { return 0; }\n```\nEnjoy."
    assert extract_cpp(reply) == "int main() { return 0; }\n"


@pytest.mark.parametrize("tag", ["c++", "CPP", "", "cxx"])
def test_accepts_other_fence_tags(tag):
    assert extract_cpp(f"```{tag}\nint main(){{}}\n```") == "int main(){}\n"


def test_picks_longest_block_when_there_are_several():
    reply = "```cpp\n// note\n```\ntext\n```cpp\n#include <iostream>\nint main(){}\n```"
    assert extract_cpp(reply).startswith("#include <iostream>")


def test_unfenced_reply_is_used_as_is():
    assert extract_cpp("  int main(){}  ") == "int main(){}\n"


def test_empty_reply_is_an_error():
    with pytest.raises(ValueError):
        extract_cpp("```cpp\n```")
