# `hello_claim` — the smallest end-to-end falsify run

The goal of this example is to prove the whole loop works on your machine in under a minute, with **no external models, no datasets, no API keys**. If `hello_claim` runs clean, the bug isn't in `falsify` — it's somewhere in your real pipeline.

## What this directory holds

| File | What it is |
|---|---|
| `spec_pass.yaml` | A claim that the experiment's accuracy is strictly above 0.85. The experiment is `echo 0.90`. This claim **passes**. |
| `spec_fail.yaml` | The same shape, but the threshold is 0.99. `echo 0.90` is below that. This claim **fails**. |
| `metrics.py` | A trivial `metric_fn` that reads the last non-empty line of `stdout.txt` and parses it as a float. |

The two specs are byte-identical except for the threshold, which is the whole point: a producer who quietly edits `0.99` to `0.85` after the fact would change the canonical bytes, and any pre-locked hash would no longer match.

## 60-second run

`falsify` expects every claim to live under `.falsify/<name>/spec.yaml`. The two specs in this directory are templates — copy them into the `.falsify/` tree, then **lock → run → verdict**.

The split matters: `run` executes your experiment and caches the result, `verdict` is what emits the exit code. CI gates should call `verdict`, not `run`.

From the repo root:

```bash
# 1. Pass case → verdict exits 0
mkdir -p .falsify/hello_pass
cp examples/hello_claim/spec_pass.yaml .falsify/hello_pass/spec.yaml
falsify lock hello_pass
PYTHONPATH=examples/hello_claim falsify run hello_pass
PYTHONPATH=examples/hello_claim falsify verdict hello_pass
echo "exit=$?"   # expect: exit=0   (Verdict: PASS)

# 2. Fail case → verdict exits 10
mkdir -p .falsify/hello_fail
cp examples/hello_claim/spec_fail.yaml .falsify/hello_fail/spec.yaml
falsify lock hello_fail
PYTHONPATH=examples/hello_claim falsify run hello_fail
PYTHONPATH=examples/hello_claim falsify verdict hello_fail
echo "exit=$?"   # expect: exit=10  (Verdict: FAIL)
```

The `PYTHONPATH` is just so the `metric_fn: "metrics:accuracy"` reference resolves against the local `metrics.py`. In a real project you'd install your metric module on the path the normal way.

## What just happened

1. `falsify` parsed the YAML, computed the canonical SHA-256 of its content-addressing fields (per [PRML §3](https://spec.falsify.dev/v0.1)), and ran the `experiment.command`.
2. The command printed `0.90` to stdout.
3. `metrics.accuracy` read that back as a float.
4. `falsify` compared the value against `failure_criteria` and emitted the verdict.

Exit codes follow PRML §7:

| Code | Meaning |
|---|---|
| `0` | PASS — the claim was not falsified by this run |
| `10` | FAIL — the claim's threshold was not met |
| `3` | TAMPER — the locked hash no longer matches the spec's canonical bytes |

## Re-verifying and tamper detection

After `falsify lock hello_pass` writes `.falsify/hello_pass/spec.lock.json`, the hash is frozen:

```bash
# Verify the locked claim — hash + threshold check
PYTHONPATH=examples/hello_claim falsify verdict hello_pass
```

Now edit `.falsify/hello_pass/spec.yaml` (drop the threshold to `0.50`, change the command, anything) and re-run `falsify verdict hello_pass`. The exit code switches to `3` — the locked hash no longer matches the canonical bytes of the edited spec. That tamper signal is the whole point of the format.

## Why this example is so small

Because the bug you're hunting is almost never in the metric. It's in canonicalization, in how your shell forwards the exit code, in how your CI provider buffers stdout, or in the path resolution for `metric_fn`. A trivial `echo 0.90` lets you rule all of those out in one minute. After `hello_claim` runs clean, swap in your real metric and your real command.

## See also

- [`humaneval-walkthrough/`](../humaneval-walkthrough/) — same shape on a real benchmark (164-problem HumanEval, pass@1 ≥ 0.65)
- [`calibration_sample/`](../calibration_sample/) — a deliberately non-trivial claim shape with multiple failure criteria
- [PRML v0.1 specification](https://spec.falsify.dev/v0.1)
- [registry.falsify.dev](https://registry.falsify.dev) — paste a manifest, get a SHA-256 permalink
