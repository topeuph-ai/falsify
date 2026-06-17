"""Smoke test for examples/embed_host.py — the runnable companion to docs/EMBED.md.

Keeps the embed quickstart honest: if the public embed API or the example drifts,
this fails. Runs the script end-to-end and checks the host-embed flow happened.
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = REPO_ROOT / "examples" / "embed_host.py"


class EmbedExampleTests(unittest.TestCase):
    def test_runs_and_demonstrates_the_flow(self):
        self.assertTrue(EXAMPLE.exists(), f"missing {EXAMPLE}")
        r = subprocess.run([sys.executable, str(EXAMPLE)],
                           capture_output=True, text=True, cwd=REPO_ROOT)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        out = r.stdout
        for marker in ("[lock]", "[run]", "[verify] PASS", "[attest]",
                       "self-anchoring", "TAMPERED",
                       "https://in-toto.io/Statement/v1"):
            self.assertIn(marker, out, f"embed example output missing {marker!r}")


if __name__ == "__main__":
    unittest.main()
