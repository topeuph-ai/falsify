"""Tests for the in-toto (ITE-6) attestation embed path: `to_intoto_statement`
and the `falsify attest` CLI subcommand.

The attestation is the embed bet's bridge for hosts that already speak
in-toto/SLSA. The contract that matters: it validates first (never attest a
malformed/non-portable claim), and the subject digest IS the PRML lock hash
(self-anchoring — anyone can recompute and confirm).
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FALSIFY_PRML = REPO_ROOT / "falsify_prml.py"

sys.path.insert(0, str(REPO_ROOT))
import falsify_prml  # noqa: E402

VALID = {
    "version": "prml/0.1",
    "claim_id": "01900000-0000-7000-8000-000000000000",
    "created_at": "2026-06-18T00:00:00Z",
    "metric": "accuracy",
    "comparator": ">=",
    "threshold": 0.90,
    "dataset": {"id": "imagenet-val-2012",
                "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},
    "seed": 42,
    "producer": {"id": "acme.ai"},
}


class IntotoStatementTests(unittest.TestCase):
    def test_shape_is_statement_v1(self):
        s = falsify_prml.to_intoto_statement(VALID)
        self.assertEqual(s["_type"], "https://in-toto.io/Statement/v1")
        self.assertEqual(s["predicateType"], "https://falsify.dev/prml/v0.1")
        self.assertIsInstance(s["subject"], list)
        self.assertIsInstance(s["predicate"], dict)

    def test_subject_digest_is_the_lock_hash(self):
        """Self-anchoring: the first subject's sha256 must equal manifest_hash,
        and the predicate must echo the same hash."""
        s = falsify_prml.to_intoto_statement(VALID)
        lock = falsify_prml.manifest_hash(VALID)
        self.assertEqual(s["subject"][0]["digest"]["sha256"], lock)
        self.assertEqual(s["predicate"]["manifest_sha256"], lock)

    def test_dataset_is_a_subject(self):
        s = falsify_prml.to_intoto_statement(VALID)
        names = {sub["name"]: sub["digest"]["sha256"] for sub in s["subject"]}
        self.assertIn(VALID["dataset"]["id"], names)
        self.assertEqual(names[VALID["dataset"]["id"]], VALID["dataset"]["hash"])

    def test_predicate_carries_the_bar(self):
        p = falsify_prml.to_intoto_statement(VALID)["predicate"]
        for k in ("metric", "comparator", "threshold", "seed"):
            self.assertEqual(p[k], VALID[k])

    def test_version_v02(self):
        m = dict(VALID, version="prml/0.2")
        self.assertEqual(falsify_prml.to_intoto_statement(m)["predicateType"],
                         "https://falsify.dev/prml/v0.2")

    def test_raises_on_invalid_manifest(self):
        with self.assertRaises(ValueError):
            falsify_prml.to_intoto_statement({"version": "prml/0.1", "metric": "acc"})

    def test_raises_on_control_char(self):
        bad = dict(VALID, metric="accu racy")
        with self.assertRaises(ValueError):
            falsify_prml.to_intoto_statement(bad)


class AttestCliTests(unittest.TestCase):
    def _run(self, args, cwd):
        return subprocess.run([sys.executable, str(FALSIFY_PRML), *args],
                              capture_output=True, text=True, cwd=cwd)

    def test_attest_prints_valid_json_exit_0(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "claim.json")
            with open(p, "w") as f:
                json.dump(VALID, f)
            r = self._run(["attest", p], cwd=d)
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            stmt = json.loads(r.stdout)
            self.assertEqual(stmt["_type"], "https://in-toto.io/Statement/v1")
            self.assertEqual(stmt["subject"][0]["digest"]["sha256"],
                             falsify_prml.manifest_hash(VALID))

    def test_attest_rejects_invalid_exit_2(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "bad.json")
            with open(p, "w") as f:
                json.dump({"version": "prml/0.1", "metric": "acc"}, f)
            r = self._run(["attest", p], cwd=d)
            self.assertEqual(r.returncode, 2, msg=r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
