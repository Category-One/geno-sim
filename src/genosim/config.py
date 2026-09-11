# Copyright (c) 2026 Category One Limited. All rights reserved.
# Licensed for inspection, execution and verification only. See LICENSE.

"""Configuration loading, validation, and content-hashing.

A run is fully determined by (config, seed). Nothing else may enter the
simulator: no environment variables, no wall-clock time, no global RNG.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ReserveConfig:
    """Reserve/backing parameters.

    initial_reserve_value: value of assets held at t=0, in numeraire units.
    initial_claims: CIC units outstanding at t=0.
    redemption_ratio: basket-value units delivered per CIC redeemed.
    external_capital: reserve funded independently of CIC sales. This is the
        ONLY route to a backing ratio above 1.0. Sale proceeds do not raise
        the ratio, because each sale creates a matching redeemable claim.
    basket_weights: composition of reserve assets, must sum to 1.0.
    basket_vol: annualised volatility per basket component.
    basket_drift: annualised drift per basket component.
    """

    initial_reserve_value: float = 1_000_000.0
    initial_claims: float = 1_000_000.0
    redemption_ratio: float = 1.0
    external_capital: float = 0.0
    basket_weights: dict[str, float] = field(default_factory=lambda: {"a": 1.0})
    basket_vol: dict[str, float] = field(default_factory=lambda: {"a": 0.15})
    basket_drift: dict[str, float] = field(default_factory=lambda: {"a": 0.0})


@dataclass(frozen=True)
class MechanismConfig:
    """Supply, fee and velocity-governor parameters.

    These are the parameters your papers withhold. They are exposed here so
    that a sweep can test the parameter-insensitivity claim directly.
    """

    fee_rate: float = 0.001
    fee_split_to_reserve: float = 0.5      # alpha_0
    fee_split_to_geno: float = 0.5
    theta_min: float = 0.5                 # velocity floor
    theta_max: float = 4.0                 # velocity ceiling
    geno_burn_rate: float = 0.02           # beta
    velocity_window: int = 30              # measurement lag, in steps
    mirror_sensitivity: float = 1.0        # dS_CIC / dM_fiat coupling


@dataclass(frozen=True)
class ScenarioConfig:
    """Exogenous environment and run mechanics."""

    n_steps: int = 720
    steps_per_year: int = 360
    fiat_expansion_rate: float = 0.05      # baseline annual M_fiat growth
    fiat_shock_step: int | None = None
    fiat_shock_magnitude: float = 0.0      # additive annualised rate
    demand_shock_step: int | None = None
    demand_shock_magnitude: float = 0.0    # fractional change in demand
    redemption_run_step: int | None = None
    redemption_run_fraction: float = 0.0   # fraction of claims presented
    redemption_settlement_lag: int = 0     # steps between request and settle
    oracle_lag: int = 1                    # steps of delay on M_fiat feed
    oracle_noise: float = 0.0              # sd of multiplicative oracle error


@dataclass(frozen=True)
class RunConfig:
    name: str
    seed: int
    reserve: ReserveConfig
    mechanism: MechanismConfig
    scenario: ScenarioConfig
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def content_hash(self) -> str:
        """Stable hash of the full parameter set.

        Used in the manifest so a published figure can be traced back to the
        exact configuration that produced it.
        """
        blob = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _check_weights(reserve: ReserveConfig) -> None:
    total = sum(reserve.basket_weights.values())
    if abs(total - 1.0) > 1e-9:
        raise ValueError(f"basket_weights must sum to 1.0, got {total}")
    for key in reserve.basket_weights:
        if key not in reserve.basket_vol or key not in reserve.basket_drift:
            raise ValueError(f"basket component {key!r} missing vol or drift")


def _check_mechanism(mech: MechanismConfig) -> None:
    split = mech.fee_split_to_reserve + mech.fee_split_to_geno
    if split > 1.0 + 1e-9:
        raise ValueError(f"fee splits exceed 1.0: {split}")
    if mech.theta_min >= mech.theta_max:
        raise ValueError("theta_min must be < theta_max")


def load_config(path: str | Path) -> RunConfig:
    """Load and validate a scenario file. The only entry point for parameters."""
    path = Path(path)
    with path.open() as fh:
        raw = yaml.safe_load(fh)

    cfg = RunConfig(
        name=raw["name"],
        seed=int(raw["seed"]),
        reserve=ReserveConfig(**raw.get("reserve", {})),
        mechanism=MechanismConfig(**raw.get("mechanism", {})),
        scenario=ScenarioConfig(**raw.get("scenario", {})),
        notes=raw.get("notes", ""),
    )
    _check_weights(cfg.reserve)
    _check_mechanism(cfg.mechanism)
    return cfg
