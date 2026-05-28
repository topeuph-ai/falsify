# Calibration sample

Public-safe 20-row fixture for demonstrating the Falsification Engine
against a set of probabilistic model predictions.

Each row is a **synthetic** prediction: a model-assigned probability and
the binary outcome that was later observed. The numbers are seeded so the
Brier score lands near 0.22, close enough to the `0.25` threshold that
both PASS and FAIL demos are credible with a small threshold nudge.

## Running the demo

```bash
mkdir -p .falsify/calibration
cp examples/calibration_sample/spec.yaml .falsify/calibration/spec.yaml
python3 falsify.py lock calibration && python3 falsify.py run calibration && python3 falsify.py verdict calibration
```
