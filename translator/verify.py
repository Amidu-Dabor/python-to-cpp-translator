"""Decide whether a translated program gives the same answer as the original."""

import difflib
import re
from dataclasses import dataclass

# Lines that legitimately differ between runs (the measured time) are left out of the comparison.
DEFAULT_IGNORE = r"(?i)execution time|elapsed|seconds"


@dataclass
class Verdict:
    match: bool
    expected: str
    actual: str
    reason: str = ""

    @property
    def diff(self) -> str:
        return "\n".join(difflib.unified_diff(
            self.expected.splitlines(), self.actual.splitlines(),
            "expected (Python)", "actual (C++)", lineterm=""))


def normalise(output: str, ignore: str = DEFAULT_IGNORE) -> str:
    """Strip timing lines and whitespace differences so only the results are compared."""
    pattern = re.compile(ignore) if ignore else None
    lines = [" ".join(line.split()) for line in output.splitlines()]
    return "\n".join(line for line in lines if line and not (pattern and pattern.search(line)))


def compare(expected: str, actual: str, returncode: int = 0, ignore: str = DEFAULT_IGNORE) -> Verdict:
    exp, act = normalise(expected, ignore), normalise(actual, ignore)
    if returncode != 0:
        return Verdict(False, exp, act, f"the program exited with code {returncode}")
    if not act:
        return Verdict(False, exp, act, "the program printed no results")
    if exp != act:
        return Verdict(False, exp, act, "the output differs from the Python output")
    return Verdict(True, exp, act)
