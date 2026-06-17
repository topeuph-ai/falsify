# Embedding PRML

PRML is small on purpose. You don't need the `falsify` CLI, a server, or a new
format in your stack — PRML is **three pure functions over a dict** plus an
optional in-toto bridge. This page is the whole integration surface for a host
(an eval platform, a governance/runtime layer, a CI system) that wants to offer
"lock the claim before the run" without adopting a new tool.

```bash
pip install falsify        # ships falsify_prml (the reference) + the CLI
```

## The contract

A PRML manifest is a plain dict with 9 required fields:

```python
manifest = {
    "version": "prml/0.1",
    "claim_id": "01900000-0000-7000-8000-000000000000",
    "created_at": "2026-06-18T00:00:00Z",
    "metric": "accuracy",
    "comparator": ">=",
    "threshold": 0.90,
    "dataset": {"id": "imagenet-val-2012", "hash": "<sha256 of the dataset>"},
    "seed": 42,
    "producer": {"id": "your-org-or-domain"},
}
```

## The three functions

Everything PRML does is these three. They are pure, dependency-light, and
byte-identical across the Python/JS/Go/Rust reference implementations.

```python
from falsify_prml import validate_manifest, manifest_hash, evaluate_predicate

errors = validate_manifest(manifest)   # [] if valid; list of reasons otherwise
lock   = manifest_hash(manifest)       # 64-hex SHA-256 over the canonical bytes
passed = evaluate_predicate(observed, manifest["comparator"], manifest["threshold"])
```

- `validate_manifest` → `list[str]`. Empty list means valid. Rejects missing
  fields, a malformed `dataset.hash`, an unknown comparator/version, and any
  control / non-portable character (C0/C1, U+007F, U+2028/U+2029, U+FEFF) in
  any key or value — the things that would make a hash non-portable.
- `manifest_hash` → the lock. Canonicalizes (keys sorted, block YAML, LF,
  trailing whitespace stripped, one trailing newline, UTF-8) then SHA-256s.
  Recompute it any time; if the manifest changed, the hash changes.
- `evaluate_predicate` → `bool`. The post-run check.

## The 5-line emit hook (lock *before* the run)

The only rule that matters: seal the bar **before** the result exists, or it
isn't a pre-registration. Embed this where your platform starts an eval run:

```python
from falsify_prml import validate_manifest, manifest_hash

def lock_claim(manifest: dict) -> str:
    errs = validate_manifest(manifest)
    if errs:
        raise ValueError("invalid PRML manifest: " + "; ".join(errs))
    return manifest_hash(manifest)        # store this next to the run, before it starts
```

After the run, verify the stored lock still matches and check the result:

```python
from falsify_prml import manifest_hash, evaluate_predicate

def verify_claim(manifest, locked_hash, observed) -> str:
    if manifest_hash(manifest) != locked_hash:
        return "TAMPERED"                  # the bar moved after locking
    return "PASS" if evaluate_predicate(
        observed, manifest["comparator"], manifest["threshold"]) else "FAIL"
```

That's the entire mechanism. Anti-pattern to avoid: computing the hash *after*
the run from whatever the manifest says then — that hashes the story you tell
afterward, not the bar you committed to. Lock first.

## Already speak in-toto / SLSA? Use the attestation bridge

If your host ingests in-toto / SLSA attestations, a PRML lock is just one more
predicate type — no PRML CLI required:

```python
from falsify_prml import to_intoto_statement

stmt = to_intoto_statement(manifest)      # validates, then returns a dict
# json.dump(stmt, ...) into your attestation bundle / transparency log
```

It returns an in-toto **Statement v1**:

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [
    {"name": "<claim_id>",  "digest": {"sha256": "<the PRML lock hash>"}},
    {"name": "<dataset.id>", "digest": {"sha256": "<dataset.hash>"}}
  ],
  "predicateType": "https://falsify.dev/prml/v0.1",
  "predicate": {
    "claim_id": "...", "created_at": "...", "metric": "...",
    "comparator": ">=", "threshold": 0.90, "seed": 42,
    "producer": {"id": "..."}, "prml_version": "prml/0.1",
    "manifest_sha256": "<the PRML lock hash>"
  }
}
```

The subject digest **is** the PRML lock, so the attestation is self-anchoring:
anyone can recompute `manifest_hash(predicate-derived manifest)` and confirm it
matches the subject. `to_intoto_statement` raises `ValueError` on an invalid
manifest, so you never attest a malformed or non-portable claim.

CLI equivalent (for shelling out from any language):

```bash
falsify attest claim.prml.yaml          # prints the Statement JSON to stdout
```

## Exit codes (for CI / shell embedding)

The CLI's exit codes are the API; all four reference impls agree:

| Code | Meaning |
|---|---|
| `0`  | PASS — verified, predicate satisfied |
| `2`  | BAD — unreadable / unparseable / invalid manifest / bad `--observed` |
| `3`  | TAMPERED — recomputed hash ≠ the locked hash |
| `10` | FAIL — verified, predicate not satisfied |
| `11` | GUARD — environmental (e.g. missing sidecar) |

## What PRML does and does not claim

PRML proves a specific evaluation **bar** (metric, threshold, dataset, seed) was
committed before the result could be silently rewritten. It does **not** prove
the result is true, that the run was reproduced, or that the dataset is what it
claims to be. It is a smaller, sharper guarantee than reproducibility — and the
right primitive to embed when you want "the claim can't move after the fact."

Other reference implementations (byte-identical): `impl/js`, `impl/go`,
`impl/rust`. Spec: <https://spec.falsify.dev/v0.1>.
