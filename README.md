# geno-sim

Reproducible simulation harness for the Geno Project (CIC / GENO).

**The economic model is not implemented.** Every function in
`src/genosim/model.py` is a placeholder marked `# >>> REPLACE`. The harness
exists so the reproducibility machinery is verified *before* your real
equations go in — that way, when you publish numbers, the only thing anyone
needs to argue about is the economics.

Any figure produced before you replace those stubs describes the
placeholders, not your design. Do not cite it.

---

## Quick start

```bash
pip install -r requirements.txt
export PYTHONPATH=src

python -m genosim verify configs/baseline.yaml           # determinism check
python -m genosim run   configs/baseline.yaml --outdir results/baseline
python -m genosim sweep configs/sweep_calibration.yaml --outdir results/sweep
pytest                                                   # reproducibility suite
```

---

## The reproducibility contract

A run is fully determined by **(config file, seed)**. Nothing else may enter
the simulator — no environment variables, no wall-clock time, no global RNG.

Five mechanisms enforce this:

1. **Seeded RNG, threaded explicitly.** One `np.random.default_rng(seed)`,
   created in `engine.run`, passed down. No module in this package calls
   `np.random` at module level. `test_no_global_rng_leakage` proves it.
2. **Parameters live in `configs/*.yaml`.** The simulator takes a config path
   and nothing else. A scenario is a file a reviewer can read, diff, and cite.
3. **Pinned environment.** `requirements.txt` uses `==`, not `>=`. Float
   results can shift across library versions.
4. **Manifest per run.** Every output directory gets `manifest.json`
   recording config hash, seed, git commit and dirty flag, Python and library
   versions, and a SHA-256 of each output file.
5. **Reference fixtures.** `reference/*.json` stores committed summary
   metrics. `pytest` fails if your environment produces different numbers
   than the ones in your paper.

Two design choices worth keeping:

- **Model and analysis are separate.** The engine emits raw time series to
  `series.parquet`. Charts and tables are produced downstream from that file.
  Reviewers can re-analyse your data without re-running your model.
- **Exogenous paths are drawn up front,** in fixed order, before the loop.
  This decouples RNG consumption from branching, so changing `theta_max`
  doesn't silently reshuffle every random draw and make two runs
  incomparable.

---

## Layout

```
configs/      scenario definitions — the only source of parameters
src/genosim/
  config.py   loading, validation, content-hashing
  model.py    ← ALL STUBS. Your equations go here.
  engine.py   deterministic loop, emits raw series
  manifest.py provenance capture
  sweep.py    parameter grids and summary metrics
  cli.py      run / sweep / verify
tests/        reproducibility suite
reference/    committed fixtures
scripts/      make_reference.py
```

---

## What you need to supply

`model.py` has six stubs, in dependency order:

| Function | What it needs from you |
|---|---|
| `observe_m_fiat` | The oracle. Data source, update frequency, staleness and failure behaviour. |
| `cic_supply_delta` | The Paper 3/4 supply rule. |
| `fee_flows` | Actual fee schedule and destinations. |
| `measure_velocity`, `geno_delta` | Paper 4 velocity governor and burn triggers. |
| `price_update` | **Price formation and the demand curve.** |
| `settle_redemptions` | Redemption policy: eligibility, minimums, fees, gating, spot vs ratio. |

`price_update` deserves emphasis. Whatever you assume there will dominate
every result the harness produces. State it explicitly in your paper and
vary it — a robustness claim that holds under only one price model is not a
robustness claim.

---

## Two things the harness encodes as tests

**Backing arithmetic.** `backing_ratio` computes reserve assets over
redeemable claims. A CIC sale adds proceeds to reserves *and* creates a
matching claim, so both sides move together and the ratio is unchanged.
Only `external_capital` — reserves funded without a corresponding claim —
raises it above 1.0. `test_sale_proceeds_do_not_raise_backing_ratio` asserts
this. If your design achieves 2x, set `external_capital` and document where
that capital comes from.

**Accounting invariants.** `test_accounting_invariants` asserts no negative
reserves, supplies, or claims, and finite prices and velocities, across every
scenario. A failure means the model is internally inconsistent, which
invalidates every result built on it — separate from any stress finding.

---

## Scenarios

| Config | Tests |
|---|---|
| `baseline` | Control. Misbehaviour here is a bug, not a result. |
| `stress_hyperinflation` | Mirror response when M_fiat goes vertical, with a 5-step oracle lag. |
| `stress_reserve_shock` | Correlated basket drawdown with claims fixed at par — the floor breaking from the asset side. |
| `stress_redemption_run` | 40% of claims presented during a demand collapse, with settlement lag. |
| `sweep_calibration` | 1,620-cell grid over the withheld parameters. Seeds are in the grid so parameter effects can be separated from run-to-run noise. |

The stress scenarios are chosen for a *redemption-backed* design. If backing
turns out to be weaker than described, add reflexivity scenarios — the
stabilising token losing value exactly when it's needed.

---

## Regenerating reference fixtures

```bash
python scripts/make_reference.py
```

Run this deliberately, after an intentional model change, and say why in the
commit message. Never run it to make a failing test pass — that is the one
action that quietly destroys the guarantee everything else here provides.

---

# Demand model

Separate from the monetary simulation. Models retail adoption of CIC as a
savings layer that households hold and convert out of to spend.

```bash
export PYTHONPATH=src
python -m genosim.demand_cli run       configs/demand/em_high_inflation.yaml
python -m genosim.demand_cli sweep     configs/demand/sweep_uncertainty.yaml   # 2,025 cells
python -m genosim.demand_cli verify    configs/demand/dm_developed.yaml
python -m genosim.demand_cli aggregate --years 10
pytest
```

**Read `ASSUMPTIONS.md` before using any number from this model.** It records
every parameter's evidential status. Most adoption-behaviour parameters are
estimates or unmeasured; only the relative sensitivities that held across the
full sweep should be reported as findings.

## Layout

```
configs/demand/    scenario files — the only source of parameters
src/genosim/
  demand.py        agent model (stubs marked # >>> REPLACE)
  demand_config.py loading, validation, hashing
  pools.py         savings pools, each figure with source and status
  demand_cli.py    run / sweep / verify / aggregate
tests/test_demand_reproducibility.py
ASSUMPTIONS.md     assumptions register
```

## Reporting rule

Report the sweep range and its drivers, not a single cell. A single cell is
not a forecast. Where a headline figure is needed, state the scenario
conditions on the face of it — accessible markets or all, static pools or
grown — rather than in a footnote.

---

## Licence and status of results

Copyright (c) 2026 Category One Limited. All rights reserved.

This repository is **source-available for verification**, not open source.
You may read it, run it, modify it locally to substitute your own
assumptions, and publish or criticise what you find. You may not
redistribute it or incorporate it into other work. See `LICENSE`.

**The outputs are conditional projections, not forecasts.** Many parameters
are unmeasured and are swept across ranges rather than fixed. Read
`ASSUMPTIONS.md` before citing any figure — it records the evidential status
of every parameter and states expressly what the model cannot determine.

Nothing here is an offer to sell or a solicitation to buy any security or
financial instrument, and nothing here is investment, financial, legal or
tax advice.
