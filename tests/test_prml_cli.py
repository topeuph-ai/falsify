"""Conformance tests for the shipped PRML CLI (`falsify_prml`).

`falsify_prml.manifest_hash` is what `pip install falsify` ships as the
`falsify` command. It MUST reproduce every locked conformance vector
(v0.1 and v0.2) byte-for-byte — same contract as the Go / JS / Rust
reference implementations. A failure here is a specification-level event:
either the canonicalizer drifted (bump the version, never edit a vector)
or the vectors were regenerated.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import falsify_prml  # noqa: E402

VECTOR_FILES = [
    REPO_ROOT / "spec" / "test-vectors" / "v0.1" / "test-vectors.json",
    REPO_ROOT / "spec" / "test-vectors" / "v0.2" / "test-vectors.json",
]


def _load(path: Path):
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else data.get("vectors", [])


class PRMLCLIConformance(unittest.TestCase):
    def test_all_vectors_hash_byte_for_byte(self) -> None:
        total = 0
        for vf in VECTOR_FILES:
            for v in _load(vf):
                manifest = v.get("input") or v.get("manifest")
                expected = v.get("hash")
                if manifest is None or expected is None:
                    continue
                total += 1
                got = falsify_prml.manifest_hash(manifest)
                self.assertEqual(
                    got, expected,
                    msg=f"{vf.parent.name}/{v.get('id', '?')}: hash mismatch "
                        f"(expected {expected[:12]}, got {got[:12]})",
                )
        self.assertGreaterEqual(total, 20, "expected at least 20 conformance vectors")

    def test_canonical_bytes_match(self) -> None:
        for vf in VECTOR_FILES:
            for v in _load(vf):
                manifest = v.get("input") or v.get("manifest")
                expected_canon = v.get("canonical")
                if manifest is None or expected_canon is None:
                    continue
                self.assertEqual(
                    falsify_prml.canonicalize(manifest), expected_canon,
                    msg=f"{vf.parent.name}/{v.get('id', '?')}: canonical bytes mismatch",
                )

    def test_predicate_and_exit_semantics(self) -> None:
        self.assertTrue(falsify_prml.evaluate_predicate(0.95, ">=", 0.90))
        self.assertFalse(falsify_prml.evaluate_predicate(0.80, ">=", 0.90))
        self.assertEqual(falsify_prml.EXIT_TAMPERED, 3)
        self.assertEqual(falsify_prml.EXIT_FAIL, 10)

    def test_v01_integer_threshold_canonicalizes_as_float(self) -> None:
        # PRML v0.1 fixes `threshold` as float64. An integer-valued threshold
        # (written as `1`, not `1.0`) MUST canonicalize as "1.0" so the hash
        # matches the JS/Go/Rust reference impls and the public registry.
        base = {
            "version": "prml/0.1",
            "claim_id": "01900000-0000-7000-8000-000000000000",
            "created_at": "2026-05-01T12:00:00Z",
            "metric": "accuracy",
            "comparator": ">=",
            "dataset": {
                "id": "imagenet-val-2012",
                "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            },
            "seed": 42,
            "producer": {"id": "acme.example"},
        }
        as_int = dict(base, threshold=1)
        as_float = dict(base, threshold=1.0)
        self.assertIn("threshold: 1.0", falsify_prml.canonicalize(as_int))
        self.assertEqual(
            falsify_prml.manifest_hash(as_int),
            falsify_prml.manifest_hash(as_float),
            msg="integer and float threshold must canonicalize identically in v0.1",
        )
        # Cross-impl anchor: this is the hash the JS/Go reference impls produce.
        self.assertEqual(
            falsify_prml.manifest_hash(as_int),
            "444c5a0fcd43372d2255930c237249cf88949c70c24f9f9a695649c56e211919",
        )

    def test_v02_integer_threshold_stays_integer(self) -> None:
        # v0.2 relaxes threshold to int|float; an integer threshold must NOT be
        # coerced to float (it stays "1300"), so v0.1 coercion is version-gated.
        m = {
            "version": "prml/0.2",
            "metric": "elo",
            "comparator": ">=",
            "threshold": 1300,
        }
        self.assertIn("threshold: 1300", falsify_prml.canonicalize(m))
        self.assertNotIn("1300.0", falsify_prml.canonicalize(m))


if __name__ == "__main__":
    unittest.main()
