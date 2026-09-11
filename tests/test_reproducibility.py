# Copyright (c) 2026 Category One Limited. All rights reserved.
# Licensed for inspection, execution and verification only. See LICENSE.

"""Reproducibility guarantees, enforced as tests.

If any of these fail, published numbers cannot be trusted. Run before
every commit and before generating any figure that goes into a document.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from genosim.config import load_config
from genosim.engine import run
from genosim.sweep import expand_grid, summarise

CONFIGS = Path(__file__).parent.parent / "configs"
REFERENCE = Path(__file__).parent.parent / "reference"
TOL = 1e-10


def _all_configs():
    return sorted(p for p in CONFIGS.glob("*.yaml"))


@pytest.mark.parametrize("path", _all_configs(), ids=lambda p: p.stem)
def test_same_seed_is_bitwise_identical(path):
    """Two runs of one config must produce identical output."""
    cfg = load_config(path)
    a, b = run(cfg), run(cfg)
    assert a.equals(b), f"{path.stem} is non-deterministic"


@pytest.mark.parametrize("path", _all_configs(), ids=lambda p: p.stem)
def test_different_seed_changes_output(path):
    """A different seed must actually change the draws.

    Guards against the opposite bug: a simulator that ignores its seed is
    trivially reproducible and completely uninformative.
    """
    cfg = load_config(path)
    a = run(cfg)
    b = run(replace(cfg, seed=cfg.seed + 1))
    assert not a.equals(b), f"{path.stem} ignores its seed"


def test_no_global_rng_leakage():
    """Seeding the global RNG must not affect results.

    This catches the single most common reproducibility bug: a bare
    np.random call somewhere in the model that silently couples results to
    unrelated code executed earlier in the process.
    """
    cfg = load_config(CONFIGS / "baseline.yaml")
    np.random.seed(1)
    a = run(cfg)
    np.random.seed(999)
    b = run(cfg)
    assert a.equals(b), "a global np.random call has leaked into the model"


def test_config_hash_is_stable_and_sensitive():
    cfg = load_config(CONFIGS / "baseline.yaml")
    assert cfg.content_hash() == load_config(CONFIGS / "baseline.yaml").content_hash()
    other = replace(
        cfg, mechanism=replace(cfg.mechanism, theta_max=cfg.mechanism.theta_max + 1)
    )
    assert cfg.content_hash() != other.content_hash()


def test_sweep_grid_order_is_deterministic():
    cfg = load_config(CONFIGS / "baseline.yaml")
    grid = {"mechanism.theta_max": [2.0, 4.0], "seed": [1, 2]}
    first = [c.name for c in expand_grid(cfg, grid)]
    second = [c.name for c in expand_grid(cfg, grid)]
    assert first == second
    assert len(first) == 4


@pytest.mark.parametrize("path", _all_configs(), ids=lambda p: p.stem)
def test_accounting_invariants(path):
    """Structural checks that must hold regardless of parameter values.

    These are not stress results. A violation here means the model itself
    is inconsistent, which would invalidate every scenario built on it.
    """
    cfg = load_config(path)
    if "sweep" in path.stem:
        pytest.skip("sweep configs are exercised via expand_grid")
    df = run(cfg)
    assert (df["reserve_value"] >= -TOL).all(), "reserve went negative"
    assert (df["cic_supply"] >= -TOL).all(), "CIC supply went negative"
    assert (df["geno_supply"] >= -TOL).all(), "GENO supply went negative"
    assert (df["claims_outstanding"] >= -TOL).all(), "claims went negative"
    assert np.isfinite(df["price"]).all(), "price went non-finite"
    assert np.isfinite(df["velocity"]).all(), "velocity went non-finite"


def test_sale_proceeds_do_not_raise_backing_ratio():
    """The 2x-backing question, encoded as a test.

    Selling CIC adds proceeds to reserves AND creates a matching redeemable
    claim. Both sides move together, so the ratio is unchanged. Only capital
    contributed without a corresponding claim raises it.
    """
    cfg = load_config(CONFIGS / "baseline.yaml")
    at_1x = run(cfg)["backing_ratio"].iloc[0]
    # Step 0 already applies one basket revaluation and one fee inflow, so the
    # ratio is near 1.0 rather than exactly 1.0. Compare configurations
    # instead of asserting an untouched initial value.
    assert 0.9 < at_1x < 1.1, f"baseline should be near 1x backing, got {at_1x}"

    over = replace(
        cfg,
        reserve=replace(cfg.reserve, external_capital=cfg.reserve.initial_claims),
    )
    at_2x = run(over)["backing_ratio"].iloc[0]
    assert at_2x / at_1x == pytest.approx(2.0, rel=1e-3), (
        "external capital equal to claims should double the backing ratio; "
        f"got {at_2x / at_1x}"
    )


@pytest.mark.parametrize("path", _all_configs(), ids=lambda p: p.stem)
def test_matches_stored_reference(path):
    """Compare against committed reference output.

    Regenerate deliberately with `python scripts/make_reference.py` after an
    intentional model change, and record why in the commit message. An
    unexplained failure here means your environment produces different
    numbers than the ones in your paper.
    """
    ref_path = REFERENCE / f"{path.stem}.json"
    if not ref_path.exists():
        pytest.skip(f"no reference fixture for {path.stem}")
    if "sweep" in path.stem:
        pytest.skip("sweep configs have no single-run reference")

    stored = json.loads(ref_path.read_text())
    current = summarise(run(load_config(path)))
    for key, expected in stored["summary"].items():
        actual = current[key]
        if isinstance(expected, bool):
            assert actual == expected, f"{key}: {actual} != {expected}"
        else:
            assert actual == pytest.approx(expected, rel=1e-9, abs=1e-12), (
                f"{key}: {actual} != {expected}"
            )
