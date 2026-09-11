# Copyright (c) 2026 Category One Limited. All rights reserved.
# Licensed for inspection, execution and verification only. See LICENSE.

"""Reproducibility and invariant tests for the demand model."""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from genosim.demand import run_demand, summarise_demand, target_allocation, marginal_gain
from genosim.demand import MarketConfig, ProductConfig
from genosim.demand_config import content_hash, load_demand_config, set_path

CONFIGS = Path(__file__).parent.parent / "configs" / "demand"
REFERENCE = Path(__file__).parent.parent / "reference"


def _cfgs():
    return sorted(CONFIGS.glob("*.yaml"))


@pytest.mark.parametrize("p", _cfgs(), ids=lambda p: p.stem)
def test_deterministic(p):
    c = load_demand_config(p)
    assert run_demand(c).equals(run_demand(c)), f"{p.stem} non-deterministic"


@pytest.mark.parametrize("p", _cfgs(), ids=lambda p: p.stem)
def test_seed_matters(p):
    c = load_demand_config(p)
    assert not run_demand(c).equals(run_demand(replace(c, seed=c.seed + 1))), \
        f"{p.stem} ignores its seed"


def test_no_global_rng_leakage():
    c = load_demand_config(CONFIGS / "em_high_inflation.yaml")
    np.random.seed(1); a = run_demand(c)
    np.random.seed(999); b = run_demand(c)
    assert a.equals(b), "a global np.random call leaked into the demand model"


@pytest.mark.parametrize("p", _cfgs(), ids=lambda p: p.stem)
def test_invariants(p):
    df = run_demand(load_demand_config(p))
    for col in ("adopted_share_of_balances", "adopted_share_of_households",
                "aware_share", "effective_spread"):
        assert (df[col] >= -1e-12).all(), f"{col} negative"
        assert (df[col] <= 1.0 + 1e-9).all(), f"{col} exceeds 1.0"
    assert (df["aware_share"].diff().dropna() >= -1e-12).all(), \
        "awareness must be monotone non-decreasing"
    assert (df["cic_balances_usd"] >= -1e-9).all()
    assert np.isfinite(df["adopted_share_of_balances"]).all()


def test_spread_declines_with_adoption():
    df = run_demand(load_demand_config(CONFIGS / "em_high_inflation.yaml"))
    assert df["effective_spread"].iloc[-1] <= df["effective_spread"].iloc[0]


def test_marginal_gain_asymmetry():
    """The model's central mechanic: local-currency holders gain far more."""
    m = MarketConfig(local_inflation=0.30, us_inflation=0.03)
    g = marginal_gain(np.array([0, 1, 2]), m, ProductConfig())
    assert g[0] > g[1] * 5, "local-currency gain should dwarf stablecoin gain"


def test_dollar_tail_risk_raises_stablecoin_gain():
    base = MarketConfig(local_inflation=0.30, us_inflation=0.03)
    tail = MarketConfig(local_inflation=0.30, us_inflation=0.03,
                        dollar_stress_prob=0.10, dollar_stress_severity=0.40)
    g0 = marginal_gain(np.array([1]), base, ProductConfig())[0]
    g1 = marginal_gain(np.array([1]), tail, ProductConfig())[0]
    assert g1 > g0 * 2, "tail risk should materially raise the USDT-pool gain"


def test_allocation_monotone_in_gain():
    g = np.array([0.01, 0.03, 0.10, 0.30, 0.60])
    a = target_allocation(g)
    assert (np.diff(a) >= -1e-12).all(), "allocation must rise with gain"
    assert a.min() >= 0.0 and a.max() <= 1.0


def test_config_hash_stable_and_sensitive():
    c = load_demand_config(CONFIGS / "em_high_inflation.yaml")
    assert content_hash(c) == content_hash(load_demand_config(CONFIGS / "em_high_inflation.yaml"))
    assert content_hash(c) != content_hash(set_path(c, "product.roundtrip_spread", 0.05))


def test_pool_shares_validated():
    from genosim.demand_config import validate
    from genosim.demand import DemandConfig
    bad = DemandConfig(name="bad", seed=1,
                       market=MarketConfig(pool_local=0.5, pool_stable=0.3, pool_other=0.3))
    with pytest.raises(ValueError, match="sum to 1.0"):
        validate(bad)


@pytest.mark.parametrize("p", _cfgs(), ids=lambda p: p.stem)
def test_matches_reference(p):
    ref = REFERENCE / f"demand_{p.stem}.json"
    if not ref.exists():
        pytest.skip(f"no reference for {p.stem}")
    stored = json.loads(ref.read_text())["summary"]
    cur = summarise_demand(run_demand(load_demand_config(p)))
    for k, exp in stored.items():
        act = cur[k]
        if isinstance(exp, bool):
            assert act == exp, f"{k}: {act} != {exp}"
        else:
            assert act == pytest.approx(exp, rel=1e-9, abs=1e-12), f"{k}: {act} != {exp}"
