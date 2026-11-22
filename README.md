# Python-to-C++ Translator

[![tests](https://github.com/Amidu-Dabor/python-to-cpp-translator/actions/workflows/tests.yml/badge.svg)](https://github.com/Amidu-Dabor/python-to-cpp-translator/actions/workflows/tests.yml)

Port slow, compute-heavy Python into high-performance C++ with an LLM (GPT or Claude), compile it to a native executable, and **verify that it still gives the same answer** before trusting the speed-up.

**Benchmark result: identical output, over 77,000× faster** (63.1 s → 0.0008 s of compute time).

---

## Why

Python is easy to write but slow in tight numerical loops. Rewriting hot code in C++ by hand is slow and error-prone. LLMs can do the rewrite in seconds, but their code can be subtly wrong: it may compile, run fast and still print the wrong answer. This tool treats the translation as untrusted until it passes a check.

## How it works

```
Python source ──► LLM (GPT or Claude) ──► C++ source ──► clang++ / g++ -O3 ──► native executable
      │                                                                              │
      └──────── run both ──► compare results (timing lines ignored) ──► PASS / FAIL ◄┘
```

1. **Translate** (`translator/llm.py`): sends the Python to the model with a prompt that asks for complete C++17 with identical output, integer types wide enough for every value, and the fastest correct algorithm. The C++ is pulled out of the reply (`extract.py`).
2. **Compile** (`build.py`): uses `clang++` or `g++` with `-O3 -std=c++17`. `--strict` adds `-Wall -Wextra -Werror`, so a warning such as a narrowing conversion stops the build.
3. **Verify** (`verify.py`): runs the original Python and the executable, drops lines that legitimately differ (execution time), and compares the rest. A crash, empty output or any difference is a FAIL, with a diff.

## Benchmark

[`benchmarks/python_hard.py`](benchmarks/python_hard.py): generate 10,000 pseudo-random integers with a linear congruential generator (LCG), find the maximum subarray sum, and repeat 20 times with different seeds. The two model outputs are in [`outputs/`](outputs/), exactly as generated.

**Original run** (my machine, compute time measured inside each program):

| Version | Output | Time | Speed-up | Correct |
|---|---|---|---|---|
| Original Python | 10980 | 63.098 s | 1× | ✅ |
| GPT translation | **0** | 0.790 s | ~80× | ❌ |
| Claude translation | 10980 | 0.000812 s | **~77,700×** | ✅ |

**Reproduced run** (Intel Xeon 2.1 GHz, Ubuntu 24.04, Python 3.13, clang 18):

| Version | Output | Compute time | Speed-up | End-to-end time\* | Correct |
|---|---|---|---|---|---|
| Original Python | 10980 | 44.457 s | 1× | 46.5 s | ✅ |
| GPT translation | **0** | 0.694 s | ~64× | 0.70 s | ❌ |
| Claude translation | 10980 | 0.000525 s | ~84,700× | 0.0024 s | ✅ |

\* End to end includes starting the process; measured by `python -m translator verify`. On that basis the Claude version is about 19,500× faster. Compute time is the figure each program prints itself.

### Where the speed-up comes from

- **Native compilation:** fixed-width integers and no interpreter overhead.
- **A better algorithm:** the Python checks every subarray with a nested loop (O(n²): about 50 million additions per seed, 1 billion across the 20 seeds). The Claude translation replaced it with a single pass that tracks the running sum and the smallest prefix sum (O(n), Kadane-style), which gives the same answer. **Most of the speed-up comes from this change.** The GPT translation kept the O(n²) loop, which is why it is "only" 64–80× faster.

### The bug the verifier catches

The GPT translation compiles with a warning and runs, but prints **0** instead of **10980**:

```
warning: implicit conversion from 'long' to 'uint32_t' changes value from 4294967296 to 0
```

The LCG modulus `m = 2**32` was stored in a 32-bit `uint32_t`. 2³² needs 33 bits, so it silently became 0, every `% m` became a modulo by zero (undefined behaviour in C++), and the final total was wrong. Python integers never overflow, so the bug only exists in the translation. The Claude version stores the modulus as `1ULL << 32` in a 64-bit type.

```text
$ python -m translator verify benchmarks/python_hard.py outputs/optimized_gpt.cpp --expected benchmarks/python_hard.expected.txt
  compiler outputs/optimized_gpt.cpp:8:78: warning: implicit conversion from 'long' to 'uint32_t' ... changes value from 4294967296 to 0
Python output : Total Maximum Subarray Sum (20 runs): 10980
C++ output    : Total Maximum Subarray Sum (20 runs): 0
FAIL: the output differs from the Python output.
```

With `--strict`, the same file is rejected at compile time on both clang++ and g++. **Lesson: a fast answer is worthless if it is wrong; check correctness before measuring speed.**

## Getting started

Requirements: Python 3.10+, `clang++` or `g++` (on Windows, use WSL), and an OpenAI and/or Anthropic API key for translating.

```bash
git clone https://github.com/Amidu-Dabor/python-to-cpp-translator.git
cd python-to-cpp-translator
pip install -r requirements.txt
cp .env.example .env     # add OPENAI_API_KEY and/or ANTHROPIC_API_KEY
```

Keys are read from the environment and never stored in code. Change models with `OPENAI_MODEL` or `ANTHROPIC_MODEL`.

### Commands

```bash
# Translate only
python -m translator translate benchmarks/python_hard.py --provider anthropic -o outputs/my_translation.cpp

# Verify an existing translation (runs the Python for the reference answer and the speed-up)
python -m translator verify benchmarks/python_hard.py outputs/optimized_claude.cpp

# Verify against a saved answer instead of re-running slow Python; fail on any compiler warning
python -m translator verify benchmarks/python_hard.py outputs/optimized_gpt.cpp \
    --expected benchmarks/python_hard.expected.txt --strict

# Translate and verify in one step
python -m translator run benchmarks/python_hard.py --provider openai
```

`verify` exits with code 0 on PASS and 1 on FAIL, so it can be used in scripts and CI.

### Tests

```bash
pip install -r requirements-dev.txt
pytest
```

22 tests, no API keys needed (the model call is replaced in tests). They check code extraction, output comparison, and the two real translations end to end: the Claude version must pass, and the GPT version must be rejected at run time and, in strict mode, at compile time. They run on every push in GitHub Actions.

## Project layout

```
translator/
  prompts.py     system and user prompts
  llm.py         GPT and Claude calls (keys and models from the environment)
  extract.py     pull C++ out of the model reply
  build.py       find a compiler, compile, run with timing
  verify.py      normalise output and compare
  __main__.py    command line: translate, verify, run
benchmarks/      python_hard.py and its known-correct output
outputs/         the GPT and Claude translations, as generated
tests/           pytest suite
```

## Limitations and next steps

- One input is a smoke test, not a proof. Next: generate many inputs, including edge cases, and compare every one (differential testing).
- Model output varies between runs; always verify.
- Programs that read input, use randomness from the clock or print floating-point values need a tolerance-aware comparison.
- Feed compiler errors and failed checks back to the model to repair the translation automatically.

## Background

I first built this as a Jupyter notebook while studying LLM engineering, then rebuilt it as a tested package with a command line and a verification step.

## Tech stack

Python · OpenAI API · Anthropic API · C++17 · clang++ / g++ · pytest · GitHub Actions

## Author

**Amidu Dabor** · [LinkedIn](https://linkedin.com/in/adabor) · [GitHub](https://github.com/Amidu-Dabor)

Licensed under the MIT License.
