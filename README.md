# Retail demand for a counter-inflation currency

An agent-based simulation of household adoption, published so it can be
reproduced, modified or contested.

**[Read the paper (PDF)](paper/geno-demand-study.pdf)** · seven pages, with the model
stated as equations.

## What it found

Seventeen behavioural parameters with no direct measurement were sampled
simultaneously across 8,000 draws, split between a developed-market and a
high-inflation specification. Adoption occurred in 99.92% of developed-market
samples and in all high-inflation samples. Median ten-year outcomes were 13.2%
and 12.5% of household savings balances, with fifth percentiles of 1.1% and 3.9%.

The binding constraint differs by market: trust in developed economies,
awareness where inflation is high.

## What it does not do

It does not predict adoption — it shows what follows from its assumptions. It
does not validate the instrument: full purchasing-power protection enters as an
input and is not tested. It does not measure demand; no dataset on
general-public demand for an instrument of this kind exists.

Read [ASSUMPTIONS.md](ASSUMPTIONS.md) before citing any figure. It records the
evidential status of every parameter, and documents four findings from earlier
versions that were later identified as artefacts rather than results.

---

# Demand model

Models retail adoption of CIC as a
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
