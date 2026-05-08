#!/usr/bin/env python3
"""
Generate the 8 v0.2 conformance test vectors.

Each vector exercises one v0.2 feature beyond v0.1 baseline. Output:
test-vectors.json (input + canonical bytes + sha256 hash) using the
canonicalisation rules of the v0.1 reference target (PyYAML
safe_dump, sort_keys, allow_unicode, LF endings, one trailing newline).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml


def canon(d: dict) -> str:
    s = yaml.safe_dump(d, default_flow_style=False, sort_keys=True,
                       width=float("inf"), allow_unicode=True)
    return s.replace("\r\n", "\n").rstrip() + "\n"


def vec(vid: str, title: str, description: str, manifest: dict) -> dict:
    c = canon(manifest)
    h = hashlib.sha256(c.encode("utf-8")).hexdigest()
    return {
        "id": vid,
        "title": title,
        "description": description,
        "input": manifest,
        "canonical": c,
        "hash": h,
    }


VECTORS = [
    vec(
        "TV-013",
        "v0.1 input under v0.2 — baseline backwards compat",
        "A pure v0.1 manifest must hash identically under v0.2 canonicalisation. "
        "This vector duplicates TV-001 input; the hash must equal TV-001's hash.",
        {
            "version": "prml/0.1",
            "claim_id": "01900000-0000-7000-8000-000000000000",
            "created_at": "2026-05-01T12:00:00Z",
            "metric": "accuracy",
            "comparator": ">=",
            "threshold": 0.85,
            "dataset": {
                "id": "imagenet-val-2012",
                "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            },
            "seed": 42,
            "producer": {"id": "studio-11.co"},
        },
    ),

    vec(
        "TV-014",
        "Streaming variant — P-01 minimal",
        "A streaming manifest with prml_mode=streaming and value_method as a "
        "string identifier. value field replaced by value_method; "
        "pre_registered_at replaced by pre_registered_from + pre_registered_to.",
        {
            "version": "prml/0.2",
            "claim_id": "01900000-0000-7000-8000-000000000014",
            "prml_mode": "streaming",
            "metric": "elo_rating",
            "value_method": "lmsys_anonymous_chat_arena_v1",
            "comparator": ">=",
            "threshold": 1300,
            "dataset": {
                "id": "lmsys-arena-live",
                "hash": "n/a-streaming",
            },
            "seed": None,
            "producer": {"id": "studio-11.co"},
            "model": {"id": "claude-3.5-sonnet@2025-10-01"},
            "sample_size": 1000,
            "pre_registered_from": "2026-05-01T00:00:00Z",
            "pre_registered_to": "2026-06-01T00:00:00Z",
        },
    ),

    vec(
        "TV-015",
        "Runner attestation — P-02 single URI",
        "Optional runner_attestation field carrying an opaque URI to a Sigstore "
        "Rekor entry. PRML records the presence of the attestation; the URI is "
        "not interpreted by canonicalisation.",
        {
            "version": "prml/0.2",
            "claim_id": "01900000-0000-7000-8000-000000000015",
            "created_at": "2026-05-08T20:00:00Z",
            "metric": "refusal_rate",
            "comparator": ">=",
            "threshold": 0.95,
            "dataset": {
                "id": "harmbench-v1",
                "hash": "f1e2d3c4b5a6978878695a4b3c2d1e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d",
            },
            "seed": 42,
            "producer": {"id": "studio-11.co"},
            "model": {"id": "claude-3.5-sonnet@2025-10-01"},
            "runner_attestation": "sigstore://rekor.sigstore.dev/api/v1/log/entries/24296fb24b8ad77a",
        },
    ),

    vec(
        "TV-016",
        "Revocation — P-03 dataset_compromised",
        "A revoked manifest with revoked_at and revocation_reason. The hash "
        "still verifies; verifiers must surface revocation status separately.",
        {
            "version": "prml/0.2",
            "claim_id": "01900000-0000-7000-8000-000000000016",
            "created_at": "2026-04-01T12:00:00Z",
            "metric": "accuracy",
            "comparator": ">=",
            "threshold": 0.92,
            "dataset": {
                "id": "imagenet-val-2012",
                "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            },
            "seed": 42,
            "producer": {"id": "studio-11.co"},
            "revoked_at": "2026-05-15T10:00:00Z",
            "revocation_reason": "dataset_compromised",
        },
    ),

    vec(
        "TV-017",
        "Revocation — P-03 author_request",
        "Voluntary withdrawal under revocation_reason=author_request. "
        "Distinct hash from TV-016 because the reason differs.",
        {
            "version": "prml/0.2",
            "claim_id": "01900000-0000-7000-8000-000000000017",
            "created_at": "2026-04-01T12:00:00Z",
            "metric": "accuracy",
            "comparator": ">=",
            "threshold": 0.92,
            "dataset": {
                "id": "imagenet-val-2012",
                "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            },
            "seed": 42,
            "producer": {"id": "studio-11.co"},
            "revoked_at": "2026-05-15T10:00:00Z",
            "revocation_reason": "author_request",
        },
    ),

    vec(
        "TV-018",
        "Streaming + runner_attestation combined",
        "Both v0.2 features present in one manifest. Canonicalisation rule: "
        "all fields included, key-sorted. Demonstrates additivity.",
        {
            "version": "prml/0.2",
            "claim_id": "01900000-0000-7000-8000-000000000018",
            "prml_mode": "streaming",
            "metric": "win_rate",
            "value_method": "alpaca_eval_2_judge_v1",
            "comparator": ">=",
            "threshold": 0.5,
            "dataset": {
                "id": "alpaca-eval-2-live",
                "hash": "n/a-streaming",
            },
            "seed": None,
            "producer": {"id": "studio-11.co"},
            "model": {"id": "experimental-rlhf-2026-05-08"},
            "sample_size": 500,
            "pre_registered_from": "2026-05-01T00:00:00Z",
            "pre_registered_to": "2026-05-31T23:59:59Z",
            "runner_attestation": "sigstore://rekor.sigstore.dev/api/v1/log/entries/abcdef",
        },
    ),

    vec(
        "TV-019",
        "Streaming with min sample size below the bar — manifest valid; verdict undefined",
        "v0.2 sample_size in streaming mode is a *minimum*. The manifest is "
        "structurally valid even if the realised window collected fewer samples. "
        "Verdict computation in this case must return undefined; canonicalisation "
        "and hashing do not depend on realised data.",
        {
            "version": "prml/0.2",
            "claim_id": "01900000-0000-7000-8000-000000000019",
            "prml_mode": "streaming",
            "metric": "elo_rating",
            "value_method": "lmsys_anonymous_chat_arena_v1",
            "comparator": ">=",
            "threshold": 1100,
            "dataset": {
                "id": "lmsys-arena-live-niche",
                "hash": "n/a-streaming",
            },
            "seed": None,
            "producer": {"id": "studio-11.co"},
            "model": {"id": "obscure-7b-2026-04"},
            "sample_size": 5000,
            "pre_registered_from": "2026-05-01T00:00:00Z",
            "pre_registered_to": "2026-05-08T00:00:00Z",
        },
    ),

    vec(
        "TV-020",
        "All v0.2 features combined — stress test",
        "Streaming + runner_attestation + revocation. Tests that all v0.2 "
        "fields canonicalise correctly when present together.",
        {
            "version": "prml/0.2",
            "claim_id": "01900000-0000-7000-8000-000000000020",
            "prml_mode": "streaming",
            "metric": "elo_rating",
            "value_method": "lmsys_anonymous_chat_arena_v1",
            "comparator": ">=",
            "threshold": 1300,
            "dataset": {
                "id": "lmsys-arena-live",
                "hash": "n/a-streaming",
            },
            "seed": None,
            "producer": {"id": "studio-11.co"},
            "model": {"id": "claude-3.5-sonnet@2025-10-01"},
            "sample_size": 1000,
            "pre_registered_from": "2026-05-01T00:00:00Z",
            "pre_registered_to": "2026-06-01T00:00:00Z",
            "runner_attestation": "sigstore://rekor.sigstore.dev/api/v1/log/entries/zzz",
            "revoked_at": "2026-06-02T12:00:00Z",
            "revocation_reason": "model_recalled",
        },
    ),
]


def main() -> int:
    out_path = Path(__file__).parent / "test-vectors.json"
    out_path.write_text(json.dumps(VECTORS, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(f"wrote {len(VECTORS)} vectors to {out_path}", file=sys.stderr)
    for v in VECTORS:
        print(f"  {v['id']}  {v['hash'][:16]}…  {v['title']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
