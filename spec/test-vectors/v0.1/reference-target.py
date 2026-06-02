#!/usr/bin/env python3
"""
Reference conformance target — Python.

Reads a single PRML manifest as JSON on stdin, writes
{"canonical": "...", "hash": "..."} on stdout. Used as a sanity reference
for the conform.py runner; matches the canonicalisation rules of the
falsify Python reference impl.

Usage as a runner target:

    python3 conform.py "python3 reference-target.py"
"""

from __future__ import annotations

import hashlib
import json
import sys

import yaml  # PyYAML; the reference impl uses this


def canonicalise(manifest: dict) -> str:
    """PRML v0.1 §4 canonicalisation:
        - keys recursively sorted
        - YAML default flow off (block style)
        - LF line endings
        - trailing whitespace stripped
        - one trailing newline
        - UTF-8 encoded

    PRML v0.1 §2 fixes `threshold` as float64: an integer-valued threshold
    (e.g. `90`) MUST canonicalize as a float (`90.0`), matching the falsify
    Python/JS/Go/Rust reference impls. v0.2 relaxes threshold to int|float,
    so this coercion is v0.1-only.
    """
    m = dict(manifest)
    if m.get("version") == "prml/0.1":
        v = m.get("threshold")
        if isinstance(v, int) and not isinstance(v, bool):
            m["threshold"] = float(v)
    canonical = yaml.safe_dump(
        m,
        default_flow_style=False,
        sort_keys=True,
        width=float("inf"),
        allow_unicode=True,
    )
    canonical = canonical.replace("\r\n", "\n").rstrip() + "\n"
    return canonical


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        sys.stderr.write("no input on stdin\n")
        return 2
    manifest = json.loads(raw)
    canonical = canonicalise(manifest)
    h = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    sys.stdout.write(json.dumps({"canonical": canonical, "hash": h}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
