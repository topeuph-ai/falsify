# Changelog

All notable changes to Falsification Engine are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com); version
numbers follow [Semantic Versioning](https://semver.org).

## [v0.3.6] — 2026-06-17

### Fixed

- **Reject control / non-portable characters in string fields.** `validate_manifest` now rejects any manifest whose string fields contain a C0/C1 control character (including U+0085 NEL, which PyYAML does not round-trip), U+007F, U+2028/U+2029, or U+FEFF. Such characters canonicalize to non-portable or non-round-trippable bytes across the Python/JS/Go/Rust reference implementations, so a manifest containing them could lock to a hash that does not faithfully represent the input. The rule is additive: no conformance vector contains these characters, so every valid manifest's hash is unchanged and all 21 vectors still pass byte-identically (571 unit tests pass). Printable Unicode (emoji, CJK, accents) is unaffected. See `spec/analysis/canonicalization-portability-v0.1.md`.
- **JS/Go/Rust reference impls now mirror the control-char reject rule.** All four reference implementations reject a manifest carrying a forbidden character before hashing — JS in `validateManifest`, Go and Rust as a guard in their `hash`/`verify` command paths — and accept emoji/CJK/accents. The clean-manifest hash is byte-identical across all four (`a18da30…` on the shared test manifest), and all 21 conformance vectors still pass byte-for-byte in every impl. Exit codes on rejection follow each impl's existing bad-manifest convention (Python `2`, JS/Go/Rust `11`); the parity property is that all four *reject* rather than silently hash.

## [v0.3.5] — 2026-06-04

### Fixed

- **Docs/spec consistency sweep + refreshed published metadata.** Updated `prml-verify-action` references from `@v1` to `@v2` (current major), corrected the v0.1 conformance-suite doc to 13 vectors and the required-field count to 9, and updated the EU AI Act high-risk obligation date to 2 December 2027 (Digital Omnibus deferral; Article 50 transparency unchanged at 2 August 2026) across the spec site. This release re-publishes the package so the PyPI project page reflects the corrected README. Docs only; no behaviour or API change.

## [v0.3.4] — 2026-06-02

### Fixed

- **Conformance vector TV-013 had a malformed `dataset.hash` (65 chars, not 64).** PRML v0.1 §2.3.2 fixes `dataset.hash` as 64 lowercase hex; TV-013's value carried one extra character. The canonicalization/hash tests never validated it, so it slipped through, but `validate_manifest` (Python and JS reference impls) correctly rejects it. Corrected to a valid 64-hex value and regenerated the suite; TV-013's hash changes from `08c3af63…` to `cb9683ce…`. All four reference implementations reproduce the new hash byte-for-byte, and `validateManifest` now accepts every v0.1 vector input. The integer→float threshold coercion TV-013 was added to lock is unchanged (`threshold: 90` still canonicalizes as `90.0`).

## [v0.3.3] — 2026-06-02

### Fixed

- **Documentation: conformance-vector count corrected to 21 (13 v0.1 + 8 v0.2) across all surfaces.** The v0.3.2 release added TV-013 but several docs still read "20 / 12 v0.1" — the README spec-artifacts list and status banner, the spec pages (`spec/index.html`, `PRML-v0.1.md`, `PRML-v0.2-RFC.md`, demo, editor, schema, iso-42001, eval-audit), the JOSS paper, ROADMAPs, and `CITATION.cff`. All now state 21 / 13. Also refreshed the README test badge (571 passing) and the `falsify --version` line (0.3.3). Frozen preprints (`*.tex`) and the historical canonicalization-portability analysis are intentionally left at their as-published counts. Docs only; no behaviour change.

## [v0.3.2] — 2026-06-02

### Added

- **PRML v0.1 conformance vector TV-013 ("Integer-valued threshold").** Locks the v0.1 integer→float threshold coercion: a bare `threshold: 90` MUST canonicalize as `90.0`. This is the behaviour the v0.3.1 CLI fix introduced, but no conformance vector previously pinned it. All four reference implementations (Python, JavaScript, Go, Rust), the conformance runner's reference target, and the public registry reproduce it byte-for-byte. **Non-breaking:** every prior vector's hash is unchanged. The v0.1 suite is now 13 vectors (21 total, including v0.2's 8).

### Fixed

- **Conformance test wiring (`tests/test_prml_vectors.py`).** The PRML vector tests verified the falsify-*engine* canonicalizer (`falsify._canonicalize`, a different schema that does not apply the PRML v0.1 threshold coercion) instead of the PRML reference (`falsify_prml.canonicalize`). The mismatch was invisible while every vector used a float threshold; TV-013 exposed it. The suite now exercises the PRML CLI canonicalizer.
- **`spec/test-vectors/v0.1/reference-target.py` and `generate.py`** now apply the same v0.1 threshold coercion, so the conformance runner's reference target and the vector generator agree with the four implementations.
- **Multi-language conformance workflow** Python reference switched from `falsify._canonicalize` (engine) to `falsify_prml.canonicalize` (PRML CLI) for both suites, so CI reproduces TV-013 byte-for-byte across all four languages (21 vectors, 84 agreements per run).

## [v0.3.1] — 2026-05-31

### Fixed

- **PRML CLI: integer-valued `threshold` now canonicalizes as a float in v0.1.** PRML v0.1 fixes `threshold` as float64, but the shipped `falsify` CLI emitted a bare integer (`threshold: 1`) when a manifest used an integer literal, producing a SHA-256 that disagreed with the JavaScript / Go / Rust reference implementations and the public registry (a spurious `TAMPERED`). It now coerces an integer-valued `threshold` to `1.0` for `prml/0.1`, matching the other implementations. v0.2 (where `threshold` is `int|float`) is unchanged, and all 20 locked conformance vectors still pass byte-for-byte. Regression test added in `tests/test_prml_cli.py`.

## [v0.3.0] — 2026-05-30

The `falsify` command is now the **PRML reference CLI** — `lock` / `verify` / `hash` / `init` / `test-vectors` operating directly on a `*.prml.yaml` manifest, byte-equivalent to the JavaScript / Go / Rust reference implementations (passes all 20 conformance vectors). `pip install falsify` finally gives a tool that hashes and verifies PRML manifests.

**Breaking change.** The pre-registration *workflow engine* (the previous `falsify` command: `init` → `lock` → `run` → `verdict` → `guard` over `.falsify/<name>/` claim specs) is now the **`falsify-engine`** command, shipped in the same install. Replace `falsify` with `falsify-engine` for workflow-engine usage.

**Conformance: unchanged.** All 20 vectors and their locked hashes are untouched; the canonicalization contract is identical.

### Added

- **`falsify_prml.py`** — the PRML CLI (new `falsify` entry point). PASS / FAIL / TAMPERED with exit codes 0 / 10 / 3.
- **`tests/test_prml_cli.py`** — conformance gate: the shipped CLI reproduces all 20 locked vectors (v0.1 + v0.2) byte-for-byte, plus predicate and exit-code checks.

### Changed

- **`pyproject.toml`** — `falsify = falsify_prml:main`, `falsify-engine = falsify:main`; version `0.3.0`.
- **`prml-verify-action`** gains a `manifest` mode that runs `falsify verify` for genuine PRML-manifest hash/tamper verification; the engine modes (`guard` / `verdict` / `lock`) now invoke `falsify-engine`.

## [v0.2.0] — 2026-05-22 (spec freeze)

PRML v0.2 specification frozen. Eight new conformance vectors promoted from
candidate to normative. Four reference implementations (Python, JavaScript,
Go, Rust) pass the full 20-vector suite byte-for-byte.

**Breaking changes: none.** Every v0.1 manifest remains a valid v0.2 manifest;
hash-equivalence is preserved. See `spec/MIGRATION-v0.1-to-v0.2.md`.

### Added — specification

- **`spec/MIGRATION-v0.1-to-v0.2.md`** — migration guide covering breaking-change
  audit, optional field reference, identity levels, and v0.3 deferral.
- **§2.3.4 timestamp anchor distinction** in `spec/PRML-v0.1.md` — clarifies
  manifest `created_at` is producer-declared; audit-strength timestamps come
  from external anchor mechanisms (git, registry, RFC 3161, Sigstore Rekor,
  arXiv, DOI, CI logs).
- **Freeze-day editorial decisions** in `spec/PRML-v0.2-RFC.md` and
  `spec/v0.2-rfc/PRML-v0.2-RFC.md`:
  1. Selective non-publication remains out of scope (§8.1 restated).
  2. Multi-metric claims = multiple manifests (claim-tree deferred to v0.3).
  3. Manifest timestamp = producer-declared, audit value lives in anchor.
  4. `producer` stays plain string with SHOULD-level external anchoring.
  5. **P-02 `attestation_uri` distinction** (contributed by Ceri John,
     Topeuph AI / ValiChord) — execution attestation (Pattern 11, Sigstore)
     vs. independence attestation (Pattern 13, blind commit-reveal).
- **`spec/v0.3-backlog/`** — three deferred RFC issues:
  - `01-claim-tree.md` — multi-metric suite manifests
  - `02-producer-struct.md` — structured producer with key_id / signature
  - `03-tolerance.md` — GPU floating-point non-determinism epsilon

### Added — cookbook (companion repo `studio-11-co/falsify-cookbook`)

- **Pattern 13 — PRML + commit-reveal validation for independence attestation**
  (co-authored with Ceri John, Topeuph AI / ValiChord). Cookbook's first
  co-authored entry. License CC0-1.0.
- **`IDENTITY-LEVELS.md`** — non-normative ladder for `producer` binding
  strength (Level 0 unsigned to Level 4 institutional).
- **Pattern 11 author metadata block** added retroactively for cookbook
  consistency.

### Added — crosswalk pages

- Interpretive-mapping disclaimer banners on EU AI Act Article 12, NIST AI
  RMF, and ISO/IEC 42001 crosswalk pages (`spec.falsify.dev/eu-ai-act/`,
  `nist-ai-rmf/`, `iso-42001/`). Each page now explicitly states the
  crosswalk is not legal advice, regulatory acceptance, or certification.

### Changed — registry

- `countUniqueProducers()` in the live registry worker normalises quoted vs
  unquoted `producer.id` values and targets the `producer:` block specifically
  in regex fallback. The previous version mis-counted `dataset.id` and
  `model.id` as producer IDs when YAML parsing failed on truncated previews.
  Lock #1 `unique_producer_count` corrects from a displayed 8 to the actual 2
  (two test placeholders, `example.com` and `onboarding-walkthrough-test`).
  Live as of 2026-05-20.

### Locks (meta pre-registration)

- **Lock #2** — `external_contributor_count` for the v0.2 RFC, target ≥ 3,
  resolved 2026-05-22 23:59 UTC at **0 / 3**. Lock failed. Post-mortem at
  `/notes/lock-2-postmortem/`. The mechanism worked; the outreach didn't.
- Lock #1 remains pending (target ≥ 25 unique producers on registry,
  resolves 2026-06-15).

---

## [Unreleased]

Specification-track changes after 0.2.0 will accumulate here. No
behaviour changes in the installed `falsify` Python package between
0.1.4 and 0.2.0.

### Added — specification

- **v0.2 RFC** at `spec/v0.2/RFC.md` and live at
  `spec.falsify.dev/v0.2/rfc` — ten changes, five open questions, freeze
  targeted 2026-05-22, release 2026-06-15. Companion paper outline at
  `spec/paper/prml-v0.2-preprint.tex`.
- **Eight v0.2 candidate vectors** at `spec/test-vectors/v0.2/test-vectors.json`
  (TV-013 through TV-020). Supersedes the six-vector candidate set at
  `spec/v0.2/test-vectors-candidates.json` for CI purposes; the latter
  is retained for historical reference until v0.2 freeze.
- **JSON Schemas** for v0.1 and v0.2 manifests shipped under `spec/schema/`,
  linked from the SchemaStore catalog and surfaced in the spec masthead.
- **Zenodo DOI** [10.5281/zenodo.20177839] for the v0.1 spec. README,
  CITATION.cff, spec/index.html footer, and the arXiv preprint author
  block all carry the DOI.
- **SchemaStore catalog merge** — PRML manifests are now JSON-schema-
  validated by every editor that uses SchemaStore (VS Code, JetBrains,
  Neovim, etc.). Routed for ISO/IEC JTC 21 review.

### Changed — conformance CI

- `.github/workflows/multi-lang-conformance.yml` runs all 20 vectors
  (12 v0.1 normative + 8 v0.2 candidate) across Python, JS, Go, and
  Rust per push and daily at 04:00 UTC. Total verification surface:
  4 implementations × 20 vectors = 80 byte-for-byte agreements per run.
  Replaces the earlier 18-vector configuration. Redundant
  `.github/workflows/conformance.yml` removed.
- `impl/{js,go,rust}` canonicalizers are now **version-aware** on
  `FLOAT_FIELDS`. v0.1 keeps `threshold` as float64 (integer thresholds
  carry `.0`); v0.2 RFC P-XX relaxes `threshold` to `int|float`, so
  integer thresholds render as plain integers under v0.2. All four
  reference implementations now pass 12/12 v0.1 + 8/8 v0.2 byte-for-byte.

### Changed — registry

- `registry.falsify.dev` Worker now parses incoming YAML via `js-yaml`
  and runs the byte-equivalent canonicalizer (port of
  `impl/js/falsify.js`, version-aware). Replaces the prior naive
  text-based canonicalize that diverged from `yaml.safe_dump` for
  nested manifests. 19/20 conformance vectors agree byte-for-byte
  with the Python reference; TV-006 (2^64-1 seed) is a JS-Number-
  precision edge case documented as a known limitation.

### Added — tooling

- `tools/registry_hash.py` — local helper that computes the
  `registry.falsify.dev`-equivalent SHA-256 without a network round-trip,
  for offline verification and CI gating.

## [0.1.4] — 2026-05-08

### Fixed

- **Wheel packaging gap.** v0.1.3 PyPI wheel was unusable on a clean install: `falsify lock` failed with `FileNotFoundError: hypothesis.schema.yaml` and `falsify init` failed with `template not found`, because the schema and template files lived at the repo root (outside the `py-modules = ["falsify"]` namespace) and were therefore not shipped in the wheel. v0.1.4 inlines both files as `_BUNDLED_SCHEMA_YAML` and `_BUNDLED_TEMPLATE_YAML` constants in `falsify.py` and uses them as fallbacks when the external files are missing. Dev mode (where the files exist alongside the script) still prefers the on-disk files; installed mode now works end-to-end without any external fetch.
- `falsify lock` now succeeds against a clean `pip install falsify==0.1.4` with no companion files.
- `falsify init <claim>` now writes a usable spec.yaml on a clean install.

### Notes

- Schema and template content unchanged — only delivery mechanism fixed.
- Downstream consumers (e.g. `studio-11-co/prml-verify-action`) can drop the curl-based data-file workaround once 0.1.4 is on PyPI.

## [0.1.3] — 2026-05-02

Documentation, brand, and metadata refresh. No functional code changes.

### Changed

- **Repository transferred** from `github.com/sk8ordie84/falsify` to `github.com/studio-11-co/falsify`. Old URLs 301-redirect to canonical; all in-source references (README, spec, test vectors, preprint .tex, Dockerfile, CITATION.cff, action workflows, package metadata) updated to the new canonical URL.
- **Editor identity standardised** to `Cüneyt Öztürk` across spec, CHANGELOG, CITATION, generator footers, and live spec.falsify.dev hosting. Aligns with falsify.dev landing.
- **Pre-commit hook reference** in README updated to `rev: v0.1.4`.

### Why this release

PyPI metadata (`Repository`, `Issues`, `Changelog` URLs in `pyproject.toml`) was frozen at v0.1.2 with the previous GitHub URL. This release refreshes metadata so `pip show falsify` and PyPI's project page reflect the canonical org. No code changes; behaviour identical to 0.1.2.

## [0.1.2] — 2026-05-01

The PRML specification day — three reference implementations across Python, JavaScript, and Go all reproducing the v0.1 conformance vectors byte-for-byte; six additional v0.2 candidate vectors; four cross-language portability findings documented; arXiv preprint, compliance landing copy, positioning matrix, v0.2 RFC roadmap, and the HumanEval worked example all published. Code itself unchanged from 0.1.1; this release exists to mark a specification-level milestone.

### Added — specification

- **PRML v0.1 specification** at `spec.falsify.dev/v0.1` (RFC-style, CC BY 4.0, ~18 pages). Editor: Cüneyt Öztürk (Independent).
- **Twelve v0.1 conformance test vectors** with locked SHA-256 digests under `spec/test-vectors/v0.1/`.
- **Six v0.2 candidate vectors** (TV-013 through TV-018) under `spec/v0.2/test-vectors-candidates.json`. Five pass byte-for-byte across all three reference implementations; TV-018 surfaces Finding 4 (small-magnitude float rendering diverges three ways across language stdlibs).
- **arXiv preprint** in `spec/paper/prml-v0.1-preprint.tex` — 14-page LaTeX working draft, CC BY 4.0, cs.CR submission in flight.
- **EU AI Act mapping** in `spec/compliance/AI-Act-mapping-v0.1.md` — Articles 12, 17, 18, 50, 72, 73 with field-level bindings.
- **Compliance landing copy** in `spec/compliance/landing.md` — for compliance leads, AI governance officers, notified body assessors.
- **Positioning matrix** in `spec/analysis/positioning-v0.1.md` — PRML vs in-toto, SLSA, Model Cards, HELM, ClinicalTrials.gov; two-axis framework; six common confusions cleared.
- **Canonicalization portability findings** in `spec/analysis/canonicalization-portability-v0.1.md` — four cross-language gotchas surfaced by the JS and Go implementations, with severity asymmetry analysis per language.
- **v0.2 RFC roadmap** in `spec/v0.2/ROADMAP.md` — ten changes, five open RFC questions, freeze targeted 2026-05-22, release 2026-06-15.
- **PRML scoring methodology** in `spec/analysis/scoring-methodology-v0.1.md` (carried over from 0.1.1 publishing window) with twelve worked examples.

### Added — implementations

- **`impl/js/falsify.js`** — Node.js second reference implementation. ~400 LOC, hand-rolled canonicalizer, zero runtime dependencies beyond Node.js stdlib. Reproduces all twelve v0.1 vectors byte-for-byte. CLI: `init / lock / verify / hash / test-vectors`.
- **`impl/go/falsify.go`** — Go third reference implementation. ~450 LOC, hand-rolled canonicalizer, standard library only. Reproduces all twelve v0.1 vectors byte-for-byte on first compile. Notably, Go's `encoding/json` with `Decoder.UseNumber()` handles two of the three v0.1 portability findings without workarounds.
- **`impl/js/README.md`** and **`impl/go/README.md`** — build / run docs and severity-asymmetry tables.

### Added — tests

- `tests/test_prml_v02_candidates.py` — 17 new unittests asserting that the Python reference reproduces the v0.2 candidate vectors. Total test count: 547 → 564, no regressions.

### Added — examples

- `examples/humaneval-walkthrough/` — end-to-end procedure document and runnable Python script demonstrating PRML on a real benchmark (HumanEval `pass@1`). Covers pinning the dataset, locking the manifest, running inference, verifying, and tamper detection.

### Added — operational artefacts (private to the launch directory)

- `proposals/_TEMPLATES.md` — six proposal / SOW / MSA / invoice templates for the post-outreach sales flow.
- `outreach/eu-ai-act-compliance-targets.md` — twelve named EU AI Act compliance / consulting / provider / academic targets with custom cold-mail angles.
- `outreach/MONDAY-2026-05-04-batch.md` — twelve fully personalised outreach mails ready to fire Monday 2026-05-04 at 09:00–11:00 CET.
- `monitoring/baseline-2026-05-01.md` — engagement baseline snapshot.
- `monitoring/sunday-monday-tuesday-playbook.md` — hour-by-hour operational playbook for Sunday, Monday, and Tuesday.
- `landing/falsify-dev-content-brief.md` — content brief for upgrading the falsify.dev landing page.
- `blog/i-implemented-prml-in-two-languages.md` — dev.to-format blog post covering Findings 1–3 (publishable from Sunday onward).

### Changed

- `README.md` — new "Specification artifacts" section surfacing the eight new public docs and three reference implementations; "Repository layout" updated with `impl/`, `spec/analysis/`, `spec/compliance/`, `spec/paper/`, `spec/v0.2/`; "Roadmap" section expanded to point at both the CLI roadmap (`ROADMAP.md`) and the spec roadmap (`spec/v0.2/ROADMAP.md`).
- `ROADMAP.md` — rewritten to clearly separate CLI tool features from PRML specification evolution. CLI v0.2 retargeted to 2026-06-15, three weeks after the spec freeze on 2026-05-22.
- `spec/index.html` — new "Related documents" section linking the eight new public artefacts via canonical GitHub blob URLs.

### Notes

- Code unchanged from 0.1.1: same canonicalizer, same exit codes, same 547 + 17 = 564 tests passing. This release marks the specification milestone, not a code change.
- The Finding 4 cross-language float divergence (TV-018) is documented but deliberately not patched in v0.1; the v0.2 grammar (RFC-Q-04, always-quote-numbers) is the strategic fix.
- arXiv submission to cs.CR is in flight pending endorsement from a TUF / in-toto / SLSA contributor.

## [0.1.1] — 2026-04-28

First public release on PyPI. `pip install falsify` now works.

### Added

- PyPI publication: `pip install falsify` installs the CLI globally.
- `Homepage = "https://falsify.dev"` URL in `pyproject.toml`.

### Changed

- All public-facing references migrated from intermediate brand
  surfaces to the project's own surfaces (landing page, repo
  metadata).

### Notes

- Code unchanged from 0.1.0 — same 518 tests, same canonical
  YAML hashing, same exit-code contract. This release exists
  to make the CLI installable for non-developers.

### Documentation

- `SUBMISSION.md` rewritten with current scope numbers, sharper
  pitch, money-shot walkthrough, and an explicit known-gaps
  section.
- `docs/DEMO_SCRIPT.md` — 90-second demo video storyboard with
  TTS-ready voiceover, shot-by-shot terminal commands, and SRT
  captions.
- Clarified that direction `above`/`below` are strictly
  greater/less (not `>=`/`<=`) in `hypothesis.schema.yaml`
  inline docs and `docs/ARCHITECTURE.md` Core invariants.

### Changed

- `mcp_server/` upgraded from stub to real MCP-SDK implementation.
  Four tools (`list_verdicts`, `get_verdict`, `get_stats`,
  `check_claim`) and three resource URIs (`falsify://verdicts`,
  `falsify://verdicts/<claim>`, `falsify://stats`) registered via
  the `mcp.server.Server` decorators. Lazy SDK import — module
  loads cleanly without `mcp`; `python -m mcp_server` exits 2 with
  a clear hint when the SDK is missing. Plain helpers stay
  importable as `from mcp_server import list_verdicts, ...`.
  Optional install bumped to `mcp>=1.0.0`.

### Added

- `falsify bench` — micro-benchmark CLI command latency with
  min / median / p95 / max / mean / stddev per command; text and
  `--json` outputs; configurable `--runs` and `--warmup`.
- `docs/CASE_STUDIES.md` — three concrete adoption scenarios
  (ML team, DevOps team, research group) with literal command
  sequences.
- `docs/GLOSSARY.md` — 30+ term glossary with cross-references
  across all docs.
- 5th Claude skill `falsify-ci-doctor` — one-shot CI failure
  triage mapping `release-check` FAIL gates to exact fix
  commands.
- `.gitignore` rules for run artifacts
  (`.falsify/*/latest_run`, `verdict.json`, `runs/`);
  `.github/CODEOWNERS`, `FUNDING.yml`, `dependabot.yml` for
  GitHub repo maturity.
- `tests/test_integration_e2e.py` — single end-to-end lifecycle
  test with 18 stages covering init, lock, run, verdict, stats,
  trend, why, score, export, verify, replay, tampering detection,
  honest relock, and stale detection.
- `scripts/release_check.py` and `make release-check` — 12-gate
  pre-release validator covering version consistency, CHANGELOG,
  placeholders, tests, smoke, dogfood, docs, Claude surface,
  installability, git cleanliness, and self-integrity.
- Self-dogfooding — three locked claims (`cli_startup`,
  `test_coverage_count`, `claude_surface`) verify falsify's own
  properties; `make dogfood` re-runs them; CI gates on them.
- `docs/COMPARISON.md` — 15-row feature matrix vs MLflow, W&B,
  DVC, OSF, pytest, pre-commit with honest positioning paragraphs.
- Three Claude Code slash commands: `/new-claim` (guided
  scaffold→lock→run), `/audit-claims` (repo-wide semantic audit),
  `/ship-verdict` (release-gate verification).
- `docs/FAQ.md` — 15 direct answers to common objections (git
  hooks, OSF, MLflow, DVC, pytest, and more).
- `CLAUDE.md` — project instructions for Claude Code users,
  encoding the prime directive, file layout, skills/subagents, and
  non-negotiable development rules.
- `pyproject.toml` — installable as `pip install .` with a
  `falsify` console entry point (`falsify:main`).
- `ROADMAP.md` — post-hackathon direction (0.2.0 MCP + Managed
  Agents, 0.3.0 Bayesian stopping, non-goals, discipline note).
- `mcp_server/` — Model Context Protocol server scaffold exposing
  the verdict store as read-only resources and four tool
  functions (`list_verdicts`, `get_verdict`, `get_stats`,
  `check_claim`). Optional install via `pip install -e '.[mcp]'`;
  tool logic is implemented, `stdio_server` SDK adapter is
  stubbed pending SDK version pin.
- `managed_agents/` — Anthropic Console deployment manifests for
  `verdict-refresher` (scheduled, 6-hour cron) and `claim-auditor`
  (on-demand webhook).
- `docs/MANAGED_AGENTS.md` — Console setup guide, cost
  expectations, rollback, security notes.
- `falsify stats --html` — self-contained HTML dashboard with
  dark-mode-aware inline CSS, per-spec cards with state-colored
  badges. `--output PATH` writes to a file. `--json` and `--html`
  are mutually exclusive.
- `falsify export` — deterministic JSONL audit trail of every
  lock, run, and verdict. Read-only. Records carry
  `schema_version: 1` and verdict records include a `locked_hash`
  that chains back to the originating lock. Flags: `--output`,
  `--name`, `--since`, `--include-runs`.
- `falsify verify` — integrity check for JSONL audit trails.
  Validates hash chain (verdict `locked_hash` ↔ lock
  `canonical_hash`), per-spec timestamp monotonicity, no record
  reordering, and schema version. Exit 0 VALID, 10 INVALID,
  2 bad input. Flags: `--strict`, `--json`.
- `.github/workflows/release.yml` — tag-triggered release pipeline.
  Runs tests + smoke, verifies the `v*.*.*` tag matches
  `falsify.__version__`, builds sdist + wheel, publishes a GitHub
  Release with the matching `CHANGELOG` section as the body.
- `.pre-commit-hooks.yaml` — hook manifest for consumer repos:
  `falsify-guard` (commit-msg stage), `falsify-doctor` (pre-commit
  stage), `falsify-stats` (informational).
- `.pre-commit-config.yaml` — local pre-commit configuration:
  standard hygiene hooks plus three local ones
  (`falsify-guard-local`, `falsify-doctor-local`, `unittest-fast`).
- `docs/PRE_COMMIT.md` — setup guide for both use cases.
- `TUTORIAL.md` — 15-minute hands-on walkthrough from init to
  first locked PASS/FAIL cycle.
- `falsify replay <run-id>` — deterministically re-runs a stored
  run's metric and verifies the value matches exactly (tolerance
  configurable via `--tolerance`). New exit code path: `10` on
  mismatch, `3` on stale spec. `cmd_verdict` now also writes
  `verdict.json` into the run dir as a per-run snapshot so
  replay can target arbitrary historical runs.
- `falsify score` — single-number honesty metric across all
  claims with text / json / shields.io / svg outputs. Powers
  README badges and CI gating; default exits `10` only on
  `fail` status, `--strict` also exits on `warn`.
- `falsify init --template {accuracy,latency,brier,llm-judge,ab}`
  — scaffolds a complete working claim (spec + metric + dataset
  + claim-local README) into `claims/<name>/` and mirrors
  `spec.yaml` into `.falsify/<name>/` so the canonical CLI flow
  works without further setup. Flags: `--name`, `--dir`,
  `--force`. Hyphenated template names default to a snake_case
  claim name so the metric module is importable.
- `falsify why <claim>` — human-readable state diagnostic with
  actionable next steps for every claim state (PASS / FAIL /
  INCONCLUSIVE / STALE / UNRUN / UNLOCKED / UNKNOWN). Always
  exits 0 — informational. Flags: `--json`, `--verbose`.
- `falsify trend <claim>` — ASCII sparkline of the metric across
  recorded runs, with threshold overlay and an
  `improving` / `degrading` / `flat` / `mixed` classifier based
  on first-third vs last-third means. Flags: `--last N` (cap 200),
  `--width`, `--ascii`, `--json`.
- `docs/ADVERSARIAL.md` — threat model enumerating 8 defended and
  6 undefended attack classes with mitigations. Linked from
  README, SECURITY, and SUBMISSION.
- Claude skill `claim-review` — reviews PR diffs for unlocked
  specs, silent threshold edits, and broken `metric_fn`
  references. Runs in PR CI, exits `1` on any CRITICAL finding.
  Paired with [`docs/PR_REVIEW.md`](docs/PR_REVIEW.md) for setup.
- `Dockerfile` + `.dockerignore` — reproducible demo environment
  (`docker run --rm -it falsify-demo` fires the auto-demo).
- `docs/DOCKER.md` — quick run, interactive session, repo-mount,
  image size + build-determinism notes.

### Notes

Next: MCP verdict-log server, Managed Agents integration for cloud
verdict refresh, multi-metric specs.

## [0.1.0] — 2026-04-21

### Added

- **Core CLI**: `init`, `lock`, `run`, `verdict`, `guard`, `list`
  subcommands with deterministic exit codes (`0` PASS, `10` FAIL,
  `2` bad spec / INCONCLUSIVE, `3` hash mismatch, `11` guard
  violation).
- **Canonical YAML + SHA-256** hashing for spec locks — the same
  logical claim always hashes identically across machines; any
  semantic edit invalidates the lock.
- **calibration sample** (`examples/calibration_sample/`) — a 20-row
  prediction ledger fixture with a Brier score metric, for the
  hackathon demo.
- **Additional CLI subcommands**: `stats` (aggregate dashboard
  across all locked verdicts), `diff` (unified canonical-YAML diff
  between the lock and the current spec), `hook install / uninstall`
  (commit-msg guard management with backup), `doctor` (environment +
  repo + per-spec self-diagnostic), `version` (version string, also
  exposed as `--version`).
- **Three Claude Code skills** in `.claude/skills/`:
  `hypothesis-author` (five-question dialogue that drafts a
  falsifiable spec), `falsify` (orchestrator routing empirical
  claims to the right pipeline step), `claim-audit` (lightweight
  text audit with handoff to the `claim-auditor` subagent).
- **Two forked-context subagents** in `.claude/agents/`:
  `claim-auditor` (paraphrase-aware semantic cross-reference of
  arbitrary text against the verdict log), `verdict-refresher`
  (autonomous refresh of STALE / INCONCLUSIVE / UNRUN verdicts).
- **GitHub Actions CI** (`.github/workflows/falsify.yml`) —
  unittest suite + `tests/smoke_test.sh` + calibration end-to-end
  (`lock` → `run` → `verdict`) + guard self-check, plus a dedicated
  skill-lint job that validates every `SKILL.md` and agent file.
- **Documentation**: `README.md` (jury-facing front door),
  `DEMO.md` (five-step runnable walkthrough),
  `docs/DEMO_SHOT_LIST.md` (second-by-second video script),
  `docs/ARCHITECTURE.md` (one-page technical overview with data
  flow + invariants), `CONTRIBUTING.md` (ground rules, PR checklist,
  skill/agent recipes), `SUBMISSION.md` (hackathon submission
  draft).

### Notes

- Initial public release for the Anthropic Built with Opus 4.7
  hackathon (April 21–26, 2026).
- MIT licensed. New work — not derived from prior projects.
- Built with Claude Code + Opus 4.7 (1M context). Every commit
  carries a `Co-Authored-By:` trailer.

[Unreleased]: https://github.com/studio-11-co/falsify/compare/v0.1.4...HEAD
[0.1.4]: https://github.com/studio-11-co/falsify/releases/tag/v0.1.4
[0.1.3]: https://github.com/studio-11-co/falsify/releases/tag/v0.1.3
[0.1.2]: https://github.com/studio-11-co/falsify/releases/tag/v0.1.2
[0.1.1]: https://github.com/studio-11-co/falsify/releases/tag/v0.1.1
[0.1.0]: https://github.com/studio-11-co/falsify/releases/tag/v0.1.0
