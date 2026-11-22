"""Command line: translate, verify, or do both.

    python -m translator translate benchmarks/python_hard.py --provider anthropic -o outputs/claude.cpp
    python -m translator verify benchmarks/python_hard.py outputs/optimized_claude.cpp
    python -m translator run benchmarks/python_hard.py --provider anthropic
"""

import argparse
import sys
import tempfile
from pathlib import Path

from .build import compile_cpp, run_executable, run_python
from .verify import DEFAULT_IGNORE, compare


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def cmd_translate(args) -> int:
    from .llm import translate
    cpp = translate(Path(args.python).read_text(), args.provider)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(cpp)
    print(f"Wrote {out} ({len(cpp.splitlines())} lines) using {args.provider}.")
    return 0


def cmd_verify(args) -> int:
    python_path, cpp_path = Path(args.python), Path(args.cpp)

    # 1. Reference result: run the Python, or read a saved expected output.
    if args.expected:
        expected, py_seconds = Path(args.expected).read_text(), None
        print(f"Expected output: {args.expected}")
    else:
        print(f"Running Python: {python_path} ...")
        py = run_python(python_path, timeout=args.timeout)
        if py.returncode != 0:
            print(py.stderr, file=sys.stderr)
            print("FAIL: the original Python program failed.")
            return 2
        expected, py_seconds = py.stdout, py.seconds

    # 2. Compile.
    with tempfile.TemporaryDirectory() as tmp:
        exe = Path(tmp) / "translated"
        build = compile_cpp(cpp_path, exe, strict=args.strict)
        for line in build.warnings:
            print(f"  compiler {line.strip()}")
        if not build.ok:
            print(build.diagnostics, file=sys.stderr)
            print("FAIL: the C++ did not compile" + (" in strict mode." if args.strict else "."))
            return 1

        # 3. Run and compare.
        cpp = run_executable(exe, timeout=args.timeout)
    verdict = compare(expected, cpp.stdout, cpp.returncode, args.ignore)

    print(f"\nPython output : {verdict.expected or '(none)'}")
    print(f"C++ output    : {verdict.actual or '(none)'}")
    if py_seconds is not None:
        print(f"Python time   : {py_seconds:.3f} s (wall clock, incl. start-up)")
    print(f"C++ time      : {cpp.seconds:.4f} s (wall clock, incl. start-up)")
    if verdict.match:
        if py_seconds is not None:
            print(f"Speed-up      : {py_seconds / cpp.seconds:,.0f}x end to end")
        print("PASS: identical results.")
        return 0
    print(f"FAIL: {verdict.reason}.")
    if verdict.diff:
        print(verdict.diff)
    return 1


def cmd_run(args) -> int:
    args.output = args.output or f"outputs/{Path(args.python).stem}_{args.provider}.cpp"
    cmd_translate(args)
    args.cpp = args.output
    return cmd_verify(args)


def main(argv=None) -> int:
    _load_dotenv()
    parser = argparse.ArgumentParser(prog="python -m translator", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    def add_verify_options(p):
        p.add_argument("--expected", help="file with the known-correct output (skips running the Python)")
        p.add_argument("--strict", action="store_true", help="treat compiler warnings as errors")
        p.add_argument("--ignore", default=DEFAULT_IGNORE, help="regex for output lines to ignore (timings)")
        p.add_argument("--timeout", type=float, default=600, help="seconds before a run is stopped")

    p = sub.add_parser("translate", help="translate a Python file into C++")
    p.add_argument("python")
    p.add_argument("--provider", choices=["openai", "anthropic"], default="anthropic")
    p.add_argument("-o", "--output", required=True)
    p.set_defaults(func=cmd_translate)

    p = sub.add_parser("verify", help="compile C++, run both programs and compare their output")
    p.add_argument("python")
    p.add_argument("cpp")
    add_verify_options(p)
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("run", help="translate, then verify")
    p.add_argument("python")
    p.add_argument("--provider", choices=["openai", "anthropic"], default="anthropic")
    p.add_argument("-o", "--output")
    add_verify_options(p)
    p.set_defaults(func=cmd_run)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
