# v0.3 RFC issue: tolerance / epsilon for hardware non-determinism

**Status:** Deferred from v0.2 freeze (2026-05-22). Open for v0.3 design.
**Tracking:** to be mirrored as `rfc-v0.3` issue on `studio-11-co/falsify`.

## Problem

PRML v0.1 specifies exact comparison: a claim with `comparator: '>='` and
`threshold: 0.9400` passes if and only if the observed value is at least
0.9400. On classical CPU-only workloads with identical seeds, this is fine.

On GPU workloads — which is most production ML — it is not fine. Sources of
sub-permille variance across runs of identical code with identical seeds:

- **CUDA atomic operations** (e.g. `atomicAdd` in reduction kernels) are
  not commutative across thread schedules; results vary at the LSB.
- **Mixed-precision arithmetic** (bf16, fp16, fp8 accumulating to fp32)
  produces different rounding paths on different SM generations.
- **`flash-attention` and similar fused kernels** use different
  tiling strategies per GPU architecture; identical seeds produce
  numerically-close-but-not-identical outputs.
- **DataLoader worker ordering** under non-deterministic data sharding
  affects gradient batches even at fixed seed.
- **Distributed training** introduces all-reduce ordering effects.
- **PyTorch `torch.use_deterministic_algorithms(True)` does not fix all
  of the above** — its documentation explicitly enumerates exceptions.

A claim locked at exactly `>= 0.9400` can therefore FAIL on a verifier
GPU even when the producer's machine PASSed under identical code. This is
not malicious tampering; it is hardware reality. The current v0.2 answer
("encode slack into the threshold") puts the burden on the producer to
guess the right margin, which is unsatisfying.

## v0.2 position

No tolerance field. A producer who needs slack must either:

- Lower the threshold (`>= 0.9395` instead of `>= 0.9400`), or
- Use a `comparator` other than strict equality.

This is operationally adequate but semantically misleading: the threshold
reflects engineering slack, not the actual claim.

## Proposed v0.3 direction

Option A — **numeric tolerance**:

```yaml
threshold: 0.9400
tolerance: 0.001
comparator: '>='
```

Verifier semantics: PASS if `observed >= (threshold - tolerance)`. Hash
includes `tolerance` so it cannot be tuned post-hoc.

Option B — **named tolerance method**:

```yaml
threshold: 0.9400
tolerance_method: 'gpu-mixed-precision'
comparator: '>='
```

With a registry of named methods (`exact`, `gpu-mixed-precision`,
`bootstrap-95ci`, etc.), each defining a deterministic procedure.
Implementations ship the method table; method changes are versioned.

Option C — **both**, with `tolerance_method` taking precedence when
present.

## Open questions

- **Which option?** Numeric is simpler and harder to abuse (you can see
  the slack). Named method is more honest about why the slack exists.
- **Hash inclusion.** Whatever option lands, `tolerance` MUST be in the
  canonical bytes. A post-hoc tolerance bump must change the hash.
- **Conformance vectors.** Vector set needs to exercise edge cases:
  exactly at threshold, exactly at threshold minus tolerance, between.
- **Verifier reporting.** When PASS is achieved only because of
  tolerance, should the verdict output distinguish PASS from
  PASS-with-tolerance? Proposal: yes, in human output; no, in exit code
  (still exit 0).
- **Tolerance and FAIL.** Does tolerance apply symmetrically? A claim
  `<= 0.05` with tolerance 0.001 — does observed 0.0505 PASS? Most likely
  yes; the comparator + tolerance defines a half-plane.
- **Statistical tolerance vs hardware tolerance.** Bootstrap CI and GPU
  determinism are different beasts. Conflating them in one field is
  potentially confusing. Separate fields may be cleaner.

## Workarounds available today (v0.1/v0.2)

- Encode the tolerance into the threshold itself and document it in the
  manifest's free-text fields.
- Pair PRML with execution-attestation (cookbook Pattern 11) so that a
  FAIL is at least pinned to a specific run rather than ambiguous.
- For research with multiple seeds, pre-register the seed list and
  threshold on the seed-averaged value, not per-seed.

## Inputs welcome

If you have produced a real claim that failed v0.1 verification due to
hardware non-determinism, please file an issue with the manifest, the
two observed values, and the hardware delta. Real failure cases inform
the choice between Options A, B, and C.
