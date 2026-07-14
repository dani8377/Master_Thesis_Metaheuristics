# Development diagnostics

One-off diagnostic and smoke-test scripts used while debugging the cloud module
(SA temperature calibration, eco-mode SA behaviour, scalability sweeps, B&B).
They are **not** part of the experimental pipeline and are not needed to
reproduce any thesis result.

Run them from the `Cloud_scheduling/` directory so the `tools/` and
`algorithms/` packages resolve, e.g.:

```bash
cd Cloud_scheduling
uv run --with numpy --with pandas --with pyyaml python scratch/_diag_t0_distribution.py
```
