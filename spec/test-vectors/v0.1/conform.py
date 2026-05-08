#!/usr/bin/env python3
"""
PRML v0.1 conformance test runner.

Runs the test vectors in test-vectors.json against a target implementation
binary and reports byte-equivalence.

Protocol for the target binary:

    The runner spawns the binary, writes a single test-vector input as JSON
    on stdin, and reads stdout. The binary MUST write a JSON object to
    stdout with two fields:

        {"canonical": "<canonical bytes as utf-8 string>",
         "hash":      "<sha256 hex (no prefix)>"}

    Non-zero exit code is treated as failure.

Usage:

    python3 conform.py path/to/your-prml-impl
    python3 conform.py "node dist/cli.js conform"
    python3 conform.py "go run ./cmd/falsify-conform"

The binary is invoked via shell, so it can include arguments.

Exit codes:

    0  all vectors passed
    1  one or more vectors failed (details printed)
    2  binary not found / IO error
"""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).parent
DEFAULT_VECTORS = HERE / "test-vectors.json"


# ANSI colours (skip if not a TTY)
def _c(s: str, code: str) -> str:
    if not sys.stdout.isatty():
        return s
    return f"\033[{code}m{s}\033[0m"


def green(s: str) -> str: return _c(s, "32")
def red(s: str) -> str:   return _c(s, "31")
def gray(s: str) -> str:  return _c(s, "90")
def bold(s: str) -> str:  return _c(s, "1")


def run_vector(binary_cmd: str, vector_input: dict[str, Any], timeout: float = 10.0) -> dict[str, Any]:
    """Invoke the target binary with one vector input. Returns parsed stdout."""
    argv = shlex.split(binary_cmd)
    proc = subprocess.run(
        argv,
        input=json.dumps(vector_input),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"target exited with code {proc.returncode}\n"
            f"stderr: {proc.stderr.strip()}"
        )
    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"target stdout is not valid JSON: {exc}\n"
            f"stdout (first 200 chars): {proc.stdout[:200]!r}"
        )
    if "canonical" not in out or "hash" not in out:
        raise RuntimeError(
            f"target stdout missing 'canonical' or 'hash' field; got keys {list(out.keys())}"
        )
    return out


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        sys.stderr.write(__doc__ or "")
        return 2

    binary_cmd = argv[1]
    vectors_path = Path(argv[2]) if len(argv) > 2 else DEFAULT_VECTORS

    if not vectors_path.exists():
        sys.stderr.write(f"vectors not found: {vectors_path}\n")
        return 2

    vectors = json.loads(vectors_path.read_text(encoding="utf-8"))
    if not isinstance(vectors, list):
        sys.stderr.write(f"vectors file is not a JSON array\n")
        return 2

    print(bold(f"PRML v0.1 conformance — {len(vectors)} vectors"))
    print(gray(f"target: {binary_cmd}"))
    print(gray(f"file:   {vectors_path}"))
    print()

    passed = 0
    failed: list[tuple[str, str]] = []

    for v in vectors:
        vid = v.get("id", "??")
        title = v.get("title", "")
        try:
            got = run_vector(binary_cmd, v["input"])
        except Exception as exc:  # noqa: BLE001
            failed.append((vid, f"runtime error: {exc}"))
            print(f"  {red('FAIL')}  {vid}  {title}")
            continue

        expected_canonical = v["canonical"]
        expected_hash = v["hash"]
        got_canonical = got["canonical"]
        got_hash = got["hash"]

        if got_canonical != expected_canonical:
            # show the first diverging line
            ec_lines = expected_canonical.splitlines()
            gc_lines = got_canonical.splitlines()
            n = min(len(ec_lines), len(gc_lines))
            div_line = next((i for i in range(n) if ec_lines[i] != gc_lines[i]), n)
            failed.append((
                vid,
                f"canonical bytes differ at line {div_line + 1}\n"
                f"  expected: {ec_lines[div_line] if div_line < len(ec_lines) else '<eof>'!r}\n"
                f"  got:      {gc_lines[div_line] if div_line < len(gc_lines) else '<eof>'!r}",
            ))
            print(f"  {red('FAIL')}  {vid}  {title}  (canonical mismatch)")
            continue

        if got_hash != expected_hash:
            failed.append((
                vid,
                f"hash mismatch (canonical bytes match)\n"
                f"  expected: {expected_hash}\n"
                f"  got:      {got_hash}",
            ))
            print(f"  {red('FAIL')}  {vid}  {title}  (hash mismatch)")
            continue

        passed += 1
        print(f"  {green('PASS')}  {vid}  {title}")

    print()
    if failed:
        print(bold(red(f"{len(failed)} vector(s) failed:")))
        print()
        for vid, msg in failed:
            print(f"  {red(vid)}")
            for line in msg.split("\n"):
                print(f"    {line}")
            print()

    summary = f"{passed}/{len(vectors)} passed"
    if failed:
        print(bold(red(f"FAIL — {summary}")))
        return 1

    print(bold(green(f"PASS — {summary}")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
