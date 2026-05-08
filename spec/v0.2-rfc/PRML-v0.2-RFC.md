# PRML v0.2 — RFC

**Status:** Draft (open for community comment)
**Editor:** Cüneyt Öztürk · Studio 11 · cuneyt@studio-11.co
**Comment window:** 2026-05-08 → 2026-05-22 (14 days)
**Freeze date:** 2026-05-22, 23:59 UTC
**Final draft expected:** 2026-05-29
**Spec home:** spec.falsify.dev/v0.2-rfc (this document)
**License:** CC BY 4.0 — same as v0.1

---

## How to comment

1. **GitHub issues** at `github.com/studio-11-co/falsify/issues` with label `rfc-v0.2`. Preferred for normative concerns.
2. **Email** the editor at `cuneyt@studio-11.co` with subject prefix `[v0.2 RFC]`. Preferred for confidential or institutional comments (JTC 21, AISI, audit firms).
3. **Pull request** against this document for prose-level edits.

A comment that lands by **2026-05-22 23:59 UTC** can change the freeze. A comment after that date is logged and rolled into v0.3 unless it identifies a security flaw.

## Goals of v0.2

v0.1 was scoped narrowly: eight fields, one hash, no I/O. v0.2 keeps that core unchanged and adds the smallest possible set of optional extensions to address gaps that surfaced during the v0.1 launch.

**v0.2 explicitly does not aim to:**
- Replace v0.1 — every v0.1 manifest remains a valid v0.2 manifest
- Add fields that mandate runtime infrastructure
- Solve selective publication (still §8.1)
- Solve execution-time attestation (deferred to v0.3)

## Compatibility statement

> A conforming v0.2 implementation MUST verify any v0.1 manifest as if it were a v0.2 manifest with all v0.2 optional fields absent. The hash of a v0.1 manifest, computed with v0.2 canonicalisation rules, MUST equal the hash computed with v0.1 rules. We will publish a conformance vector set that exercises this property.

This is non-negotiable. If any proposed v0.2 change breaks v0.1 hash-equivalence for v0.1-shaped manifests, that proposal is rejected before consideration.

## Proposals open for comment

### P-01 — Streaming / continuous-eval variant

**Problem.** Live systems (Chatbot Arena, A/B-tested production models, drift monitors) cannot pre-register a single threshold because the threshold *is* the live measurement.

**Proposal.** Add an optional `prml_mode` field with values `static` (default, current v0.1 behaviour) or `streaming`. In streaming mode:

- `pre_registered` becomes a window: `pre_registered_from` and `pre_registered_to` (RFC 3339 timestamps)
- `value` is replaced by `value_method` — a string identifier of the aggregation rule (e.g. `"mean_over_window"`, `"trimmed_mean_5pct"`, `"elo_rating"`)
- `sample_size` becomes a minimum, not an exact figure

**Example:**

```yaml
prml_version: "0.2"
prml_mode: "streaming"
metric: "elo_rating"
value_method: "lmsys_anonymous_chat_arena_v1"
threshold: 1300
threshold_direction: ">="
dataset: "lmsys-arena-live"
dataset_hash: "sha256:n/a-streaming"
model_version: "claude-3.5-sonnet@2025-10-01"
sample_size: 1000  # minimum
seed: null
pre_registered_from: "2026-05-01T00:00:00Z"
pre_registered_to: "2026-06-01T00:00:00Z"
```

**Open question.** Is `value_method` a free-form string (interoperability through community convention) or a controlled vocabulary (smaller set of canonical methods, with a registry)?

### P-02 — Optional runner attestation field

**Problem.** A determined publisher can hash a clean evaluation set, run on a contaminated one, and report the hash of the clean set. v0.1's hash commits to *what was claimed*, not proof of *what was run*.

**Proposal.** Add an optional `runner_attestation` field that, when present, points to an out-of-band attestation of the eval execution environment. Value is an opaque URI, not interpreted by PRML itself.

**Example:**

```yaml
prml_version: "0.2"
metric: "refusal_rate"
# ... v0.1 fields ...
runner_attestation: "sigstore://rekor.sigstore.dev/api/v1/log/entries/24296fb24b8ad77a..."
```

**Non-goal.** PRML does not specify what makes an attestation valid — that is the domain of Sigstore, in-toto, AWS Nitro, etc. PRML simply records that one was emitted.

**Open question.** Should `runner_attestation` be a single URI or a list? Multiple attestations from different layers (TEE + signing + provenance) are common in production.

### P-03 — Revocation primitive

**Problem.** A pre-registered manifest may need to be retracted (e.g. the underlying dataset is found contaminated; the model build is recalled). v0.1 has no in-spec revocation.

**Proposal.** Add an optional `revoked_at` field (RFC 3339 timestamp) and an optional `revocation_reason` field (one of `"dataset_compromised"`, `"model_recalled"`, `"author_request"`, `"other"`). A revoked manifest's hash MUST still verify; verification tools MUST surface revocation status separately from hash status.

**Example:**

```yaml
prml_version: "0.2"
# ... original fields ...
revoked_at: "2026-05-15T10:00:00Z"
revocation_reason: "dataset_compromised"
```

**Registry semantics.** A registry MAY mark manifests revoked. A revoked manifest's permalink remains; the badge endpoint emits `revoked` status alongside `valid`.

**Open question.** Should revocation require a separate `revocation_signature` field for non-repudiation? Adding signatures pulls in PKI choices that v0.1 deliberately avoided.

### P-04 — Conformance vector format

**Problem.** v0.1's "12 conformance vectors" are documented in prose. Future implementations cannot mechanically run them.

**Proposal.** Standardise the conformance vector format as a directory of `<vector_name>/manifest.yaml` and `<vector_name>/expected_hash.txt`. Tooling SHOULD provide a `falsify conform <impl-binary>` command that runs every vector through a target implementation and reports byte/hash match.

This is informative (non-normative) — the spec defines the format, not the test runner.

### P-05 — Patent grant in spec body

**Problem.** v0.1's patent non-assertion grant is published with the spec but appears as an appendix. CEN-CENELEC and other standards bodies have requested the grant text appear in §1 (preamble) of the spec.

**Proposal.** Move the existing grant text from Appendix C into a new §1.5 (preamble). No textual change to the grant itself. Backwards-compatible with v0.1 because the grant text is identical.

## Proposals deferred to v0.3+

The following were considered and deferred:

- **Native Sigstore signing** (deferred — wraps better around than into PRML)
- **Multi-metric manifests** (deferred — composability is a registry concern, not a manifest concern)
- **Granular field-level permissions** (out of scope — registries can implement)
- **Privacy-preserving variant** (deferred — needs separate threat-model document)

## Comment summary template

When you comment, please use this format:

```
Proposal: P-0X
Position: support / oppose / clarify
Rationale: [≤ 200 words]
Affected impl(s) (if applicable): py / js / go / rust / all
Suggested edit (optional): [diff]
```

Comments without a clear position are still useful but slow to act on.

## Editor's notes

The smallest possible change set is a feature. v0.2 is intended to be a 1-week implementation diff for any of the four reference implementations. If a proposal here cannot be implemented in that envelope, it belongs in v0.3 or later.

A list of comments received and their disposition will be published as `spec.falsify.dev/v0.2-comments` after the freeze.

— Cüneyt Öztürk, 2026-05-08
