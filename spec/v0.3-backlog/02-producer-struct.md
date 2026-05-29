# v0.3 RFC issue: structured producer field

**Status:** Deferred from v0.2 freeze (2026-05-22). Open for v0.3 design.
**Tracking:** to be mirrored as `rfc-v0.3` issue on `studio-11-co/falsify`.

## Problem

The `producer` field in v0.1 is a free-form string (or, optionally, a
mapping with `id` and `signature`). Two limitations surface in audit
practice:

1. **No machine-checkable identity binding.** A manifest claiming
   `producer: falsify.dev` is signed by anyone who possesses the canonical
   bytes; nothing in the manifest ties the producer string to a
   cryptographic key.
2. **No identity-strength signalling.** A registry observing two manifests
   with `producer: falsify.dev` has no way to distinguish one that was
   anchored against an OIDC-bound Sigstore certificate from one that was
   typed into a YAML file by hand.

The v0.1 §2.3.3 optional `signature` field addresses (1) for producers who
choose to sign over the canonical bytes, but is silent on (2).

## v0.2 position

`producer` remains a plain string (or v0.1 mapping). v0.2 adds a
non-normative recommendation that producers anchor identity to one or
more external artefacts (git commit, registry receipt, Sigstore bundle).
Identity levels 0–4 are documented in the cookbook before v0.3 opens.

## Proposed v0.3 direction

Upgrade `producer` to a structured object with SHOULD-level signature
binding:

```yaml
producer:
  id: falsify.dev                       # required, free-form
  key_id: sha256:fingerprint             # optional, identifies signing key
  signature: <detached signature over canonical bytes>  # optional
  sigstore_bundle: <inline JSON bundle>  # optional, alternative to signature
  identity_level: 3                       # optional, 0–4 per cookbook
```

Constraints:

- `id` remains required and remains a free string.
- Setting `key_id` without `signature` or `sigstore_bundle` is a v0.3
  conformance error (the key_id would be a claim no verifier can check).
- Setting `signature` without `key_id` is permitted but logs a verifier
  warning (the signature is verifiable only by an out-of-band key).
- `identity_level` is informative and reflects the producer's
  self-declared anchoring strength; verifiers MAY treat it as a hint but
  MUST NOT rely on it for security decisions.

## Compatibility with v0.1 and v0.2

A v0.1 string-valued `producer` and a v0.1 mapping-valued `producer` are
both valid v0.3 inputs. v0.3 canonicalization MUST normalize a string
`producer: foo` to `producer: {id: foo}` before hashing, OR retain the
string form — the conformance vectors will fix the choice. Whichever
choice lands, it MUST preserve v0.1 → v0.3 hash equivalence for v0.1-shaped
manifests.

## Open questions

- **Hash equivalence path.** String-form vs mapping-form: which one is
  canonical at hash time? v0.1 already uses mapping form when signature
  is present, so the precedent leans toward mapping-form-on-the-wire with
  string-form as syntactic sugar.
- **Multiple keys.** Some producers (institutions, consortia) sign with
  more than one key. Do we allow `signatures: [...]` list or one signature
  per manifest?
- **Sigstore vs PGP precedence.** When both `signature` and
  `sigstore_bundle` are present, which is authoritative? Proposal:
  verifier MUST check both; either failing is a verification failure.
- **Identity revocation.** A key compromise should not silently invalidate
  past manifests but should be discoverable. Probably handled at registry
  level, not manifest level — needs separate design.
- **Identity_level enforcement.** Should registries refuse manifests
  below a configurable identity_level? Out of scope for the spec; in
  scope for registry-policy patterns in the cookbook.

## Related

- Cookbook `IDENTITY-LEVELS.md` (lands before v0.3 opens)
- Cookbook Pattern 11 (PRML + Sigstore)
- v0.1 §2.3.3 (existing signature field semantics)
