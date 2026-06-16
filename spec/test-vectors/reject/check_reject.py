#!/usr/bin/env python3
"""Negative-conformance driver — every reference impl MUST reject these inputs.

Unlike the positive suites (which assert byte-identical canonical/hash output),
reject-vectors carry no canonical/hash: they are manifests that contain a
control / non-portable character (C0/C1, U+007F, U+2028/U+2029, U+FEFF) and so
MUST NOT lock. This driver feeds each vector's `input` to an implementation's
CLI (which takes a manifest path as its last argument) and asserts a NON-ZERO
exit — i.e. the impl rejected it rather than silently hashing a non-portable
manifest. A vector that the impl ACCEPTS (exit 0) is a parity regression.

Usage:
    check_reject.py -- <impl cmd ...>
        # the manifest path is appended as the final argument

Examples:
    check_reject.py -- python3 falsify.py lock
    check_reject.py -- node impl/js/falsify.js lock
    check_reject.py -- impl/go/falsify-go hash
    check_reject.py -- impl/rust/target/release/falsify-rs hash

Exit 0 iff every reject-vector was rejected by the impl.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_VECTORS = os.path.join(HERE, "reject-vectors.json")


def main():
    ap = argparse.ArgumentParser(description="PRML negative-conformance driver")
    ap.add_argument("--vectors", default=DEFAULT_VECTORS,
                    help="reject-vectors.json (default: alongside this script)")
    ap.add_argument("cmd", nargs=argparse.REMAINDER,
                    help="-- <impl cmd ...>  (manifest path appended last)")
    args = ap.parse_args()

    cmd = args.cmd
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        ap.error("provide the implementation command after `--`")

    vectors = json.load(open(args.vectors, encoding="utf-8"))
    leaked = 0
    tmpdir = tempfile.mkdtemp(prefix="prml-reject-")
    for v in vectors:
        path = os.path.join(tmpdir, f"{v['id']}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(v["input"], f, ensure_ascii=False)
        proc = subprocess.run(cmd + [path], capture_output=True, text=True)
        rejected = proc.returncode != 0
        status = "PASS" if rejected else "FAIL (ACCEPTED!)"
        if not rejected:
            leaked += 1
        print(f"{status:18} {v['id']}  {v['title']}")

    total = len(vectors)
    print(f"\nResult: {total - leaked}/{total} reject-vectors correctly rejected.")
    sys.exit(10 if leaked else 0)


if __name__ == "__main__":
    main()
