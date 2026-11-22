"""End-to-end checks on the two real translations of benchmarks/python_hard.py.

These are the outputs the models produced. One is correct and one has an overflow bug;
the verifier must accept the first and reject the second.
"""

from pathlib import Path

import pytest

from translator.build import compile_cpp, find_compiler, run_executable
from translator.verify import compare

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = (ROOT / "benchmarks" / "python_hard.expected.txt").read_text()

try:
    find_compiler()
except RuntimeError:
    pytest.skip("no C++ compiler installed", allow_module_level=True)


def build_and_run(name, tmp_path, strict=False):
    exe = tmp_path / name
    result = compile_cpp(ROOT / "outputs" / f"{name}.cpp", exe, strict=strict)
    return result, (run_executable(exe, timeout=60) if result.ok else None)


def test_claude_translation_matches_python(tmp_path):
    build, run = build_and_run("optimized_claude", tmp_path)
    assert build.ok, build.diagnostics
    assert compare(EXPECTED, run.stdout, run.returncode).match


def test_claude_translation_compiles_cleanly_in_strict_mode(tmp_path):
    build, _ = build_and_run("optimized_claude", tmp_path, strict=True)
    assert build.ok, build.diagnostics


def test_gpt_translation_warns_about_the_truncated_modulus(tmp_path):
    build, _ = build_and_run("optimized_gpt", tmp_path)
    assert build.ok
    assert any("4294967296" in w for w in build.warnings)


def test_gpt_translation_is_rejected_by_the_verifier(tmp_path):
    build, run = build_and_run("optimized_gpt", tmp_path)
    verdict = compare(EXPECTED, run.stdout, run.returncode)
    assert not verdict.match


def test_strict_mode_stops_the_gpt_translation_at_compile_time(tmp_path):
    build, _ = build_and_run("optimized_gpt", tmp_path, strict=True)
    assert not build.ok
