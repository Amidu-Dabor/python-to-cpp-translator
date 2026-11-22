"""Compile C++ and run programs with timing."""

import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

BASE_FLAGS = ["-O3", "-std=c++17"]
# In strict mode, narrowing conversions (like 2**32 into a 32-bit int) stop the build.
STRICT_FLAGS = ["-Wall", "-Wextra", "-Werror"]


@dataclass
class CompileResult:
    ok: bool
    command: list
    diagnostics: str

    @property
    def warnings(self) -> list:
        return [line for line in self.diagnostics.splitlines() if "warning:" in line]


@dataclass
class RunResult:
    stdout: str
    stderr: str
    returncode: int
    seconds: float


def find_compiler() -> str:
    """Return clang++ or g++, whichever is installed (clang++ preferred)."""
    for name in ("clang++", "g++"):
        path = shutil.which(name)
        if path:
            return path
    raise RuntimeError("No C++ compiler found. Install clang++ or g++.")


def compile_cpp(source: Path, output: Path, strict: bool = False, compiler: str | None = None) -> CompileResult:
    command = [compiler or find_compiler(), *BASE_FLAGS, *(STRICT_FLAGS if strict else []),
               "-o", str(output), str(source)]
    proc = subprocess.run(command, capture_output=True, text=True)
    return CompileResult(ok=proc.returncode == 0, command=command, diagnostics=proc.stderr)


def _run(command: list, timeout: float) -> RunResult:
    start = time.perf_counter()
    proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    return RunResult(proc.stdout, proc.stderr, proc.returncode, time.perf_counter() - start)


def run_executable(path: Path, timeout: float = 600) -> RunResult:
    return _run([str(Path(path).resolve())], timeout)


def run_python(path: Path, timeout: float = 600) -> RunResult:
    # -I (isolated mode) stops the script importing modules from its own folder by accident.
    return _run([sys.executable, "-I", str(path)], timeout)
