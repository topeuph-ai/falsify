# v0.3 RFC issue: claim tree / suite manifests

**Status:** Deferred from v0.2 freeze (2026-05-22). Open for v0.3 design.
**Tracking:** to be mirrored as `rfc-v0.3` issue on `studio-11-co/falsify`.

## Problem

A modern ML evaluation rarely produces a single (metric, threshold) pair.
Public benchmarks like HELM, Big-Bench, LMSYS Arena, LiveCodeBench,
MMLU-Pro, and the HuggingFace Open LLM Leaderboard report results across
tens to hundreds of (metric × dataset × subgroup) cells. The v0.1 and v0.2
manifest format commits exactly one such cell.

A producer who wants to pre-register a full evaluation suite under v0.2
must therefore lock N separate manifests, one per cell. This is:

- A UX burden — N file edits, N `falsify lock` invocations, N badges
- A coordination burden — registry submissions are independent, no
  suite-level permalink
- A correctness burden — partial publication of a suite (publish 8 of 10
  cells) is invisible to the spec

The v0.2 editorial decision is to represent suites as N v0.1 manifests
sharing a `claim_group` string. That is enough to make the pattern
expressible. It is not enough to make it ergonomic.

## v0.2 position

Multi-metric claims **MUST** be expressed as multiple v0.1/v0.2 manifests.
A non-normative `claim_group` field MAY group them. The hash of a suite
is the ordered concatenation of leaf hashes; no normative wrapper exists.

## Proposed v0.3 direction

A normative `prml.suite` document type that contains an ordered list of
leaf manifests and hashes deterministically over its leaves. Sketch:

```yaml
version: prml/0.3-suite
suite_id: 01900000-0000-7000-8000-000000000099
producer:
  id: studio-11.co
created_at: '2026-09-01T00:00:00Z'
leaves:
  - manifest_ref: ./mmlu-stem.prml.yaml
    leaf_hash: sha256:a3f9...
  - manifest_ref: ./mmlu-humanities.prml.yaml
    leaf_hash: sha256:b210...
  - manifest_ref: ./mmlu-social.prml.yaml
    leaf_hash: sha256:c4d1...
suite_hash: sha256:<deterministic-over-leaves>
```

Canonicalization rules:

1. Leaves are sorted by `leaf_hash` ascending (not by file order).
2. The `suite_hash` is SHA-256 over the canonical bytes of the suite
   document with `suite_hash` itself elided.
3. A leaf is the canonical bytes of the leaf manifest, not a path; the
   `manifest_ref` is informative for tooling.

## Open questions

- **Pass/fail semantics.** Is a suite PASS iff all leaves PASS? Or
  configurable per-suite (`pass_policy: all | majority | weighted`)?
- **Partial publication detection.** Should the suite enumerate the
  required leaves up front (preventing later silent drop), or list
  observed leaves only?
- **Subgroup reporting.** Many leaderboards report aggregate + per-subgroup
  numbers from the same run. Are subgroups separate leaves, or a nested
  structure inside one leaf?
- **Conformance vectors.** Suite-level conformance vectors will need to
  exercise leaf-ordering edge cases (identical hashes, empty suites,
  single-leaf suites). Vector format TBD.
- **Registry semantics.** Suite-level permalinks vs. leaf-level. Does the
  registry store the suite document or only the suite_hash anchor?
- **Backwards compatibility.** Conformance constraint: a v0.3-suite
  document with a single leaf MUST hash differently from the leaf alone
  (so that `[manifest]` and `manifest` are not interchangeable).

## Inputs welcome

Real-world suite formats we should be able to canonicalize cleanly:

- HuggingFace `lighteval` / `lm-eval-harness` output JSON
- HELM scenario × model result matrices
- MMLU-Pro subject breakdown
- Big-Bench-Hard task breakdown
- LiveCodeBench monthly slices

If you maintain or rely on one of these and want PRML to map cleanly to
your format, please file an issue against `studio-11-co/falsify` with
label `rfc-v0.3` and a link to the format docs.
