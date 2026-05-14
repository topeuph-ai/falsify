#!/usr/bin/env python3
"""
registry_hash.py — Compute the registry.falsify.dev-equivalent SHA-256 hash
of a PRML manifest locally.

The public registry at registry.falsify.dev uses a text-based canonicalization
(top-level key blocks sorted alphabetically, trailing whitespace trimmed) that
differs from the reference impl's `yaml.safe_dump(sort_keys=True)` for nested
or multi-line manifests.

For flat v0.1-shaped manifests (8 top-level scalar fields), both canonicalizers
produce equivalent bytes and the hash matches the CLI hash. For nested or
multi-line cases (some v0.2 RFC proposals), they diverge.

Use this script to compute what the registry WILL hash before you POST, so you
can detect divergence and decide:
  - flat manifest: registry hash == CLI hash, safe to commit
  - nested/multi-line: registry hash != CLI hash, use the registry hash as the
    canonical commitment string for any badge or audit trail that points at
    registry.falsify.dev

Usage:
    python3 tools/registry_hash.py path/to/manifest.prml.yaml
    cat manifest.prml.yaml | python3 tools/registry_hash.py -

Note: full byte-equivalence between registry and CLI canonicalization is
scheduled for the v0.2 freeze (2026-05-22) via a js-yaml port to the
Cloudflare Worker.
"""
import hashlib
import sys


def registry_canonicalize(yaml_text: str) -> str:
    """Reproduce the worker's canonicalize() function in Python."""
    normalized = yaml_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    trimmed = "\n".join(line.rstrip() for line in lines).strip()
    blocks = []
    current = None
    for line in trimmed.split("\n"):
        # Top-level key line: starts at col 0, contains a colon, not a comment
        if (
            len(line) > 0
            and not line.startswith(" ")
            and not line.startswith("#")
            and ":" in line
        ):
            if current is not None:
                blocks.append(current)
            current = line + "\n"
        else:
            if current is None:
                current = ""
            current += line + "\n"
    if current is not None:
        blocks.append(current)
    blocks.sort()
    return "".join(blocks).rstrip() + "\n"


def main():
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    arg = sys.argv[1]
    if arg == "-":
        yaml_text = sys.stdin.read()
    else:
        with open(arg, "r") as f:
            yaml_text = f.read()

    canonical = registry_canonicalize(yaml_text)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    print(digest)


if __name__ == "__main__":
    main()
