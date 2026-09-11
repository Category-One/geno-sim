# Copyright (c) 2026 Category One Limited. All rights reserved.
# Licensed for inspection, execution and verification only. See LICENSE.

"""Configuration loading for the demand model.

Mirrors genosim.config: a run is fully determined by (config file, seed).
Nothing else may enter the model — no environment variables, no wall-clock
time, no global RNG, no parameters set in scripts.

Every scenario reported anywhere must correspond to a file in configs/.
If a number cannot be traced to a config file, it is not reproducible.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import yaml

from .demand import AdoptionConfig, DemandConfig, MarketConfig, ProductConfig


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _check_market(m: MarketConfig) -> None:
    total = m.pool_local + m.pool_stable + m.pool_other
    if abs(total - 1.0) > 1e-9:
        raise ValueError(
            f"market {m.name!r}: pool_local + pool_stable + pool_other must "
            f"sum to 1.0, got {total}"
        )
    for field in ("local_inflation", "us_inflation", "dollar_stress_prob",
                  "dollar_stress_severity"):
        if getattr(m, field) < 0:
            raise ValueError(f"market {m.name!r}: {field} must be >= 0")
    if not 0.0 <= m.dollar_stress_prob <= 1.0:
        raise ValueError("dollar_stress_prob must be a probability in [0, 1]")
    if not 0.0 <= m.dollar_stress_severity <= 1.0:
        raise ValueError("dollar_stress_severity must be a fraction in [0, 1]")
    if not 0.0 < m.smartphone_access <= 1.0:
        raise ValueError("smartphone_access must be in (0, 1]")
    if m.households < 1000:
        raise ValueError("households below 1000 gives unstable agent draws")


def _check_product(p: ProductConfig) -> None:
    if p.spread_floor > p.roundtrip_spread:
        raise ValueError("spread_floor cannot exceed roundtrip_spread")
    if not 0.0 <= p.protection_rate <= 1.0:
        raise ValueError("protection_rate must be in [0, 1]")


def _check_adoption(a: AdoptionConfig) -> None:
    for month, effect in a.validation_events:
        if month < 0:
            raise ValueError("validation event month must be >= 0")
        if not 0.0 <= effect < 1.0:
            raise ValueError("validation effect must be in [0, 1)")
    if a.awareness_external < 0 or a.awareness_internal < 0:
        raise ValueError("awareness coefficients must be >= 0")
    if a.trust_threshold_sd < 0:
        raise ValueError("trust_threshold_sd must be >= 0")
    if not 0.0 <= a.churn_base <= 1.0:
        raise ValueError("churn_base must be an annual rate in [0, 1]")


def validate(cfg: DemandConfig) -> DemandConfig:
    _check_market(cfg.market)
    _check_product(cfg.product)
    _check_adoption(cfg.adoption)
    if cfg.n_steps < cfg.steps_per_year:
        raise ValueError("n_steps must cover at least one year")
    return cfg


# ---------------------------------------------------------------------------
# Hashing and loading
# ---------------------------------------------------------------------------

def to_dict(cfg: DemandConfig) -> dict[str, Any]:
    return asdict(cfg)


def content_hash(cfg: DemandConfig) -> str:
    """Stable hash of the full parameter set.

    Recorded in the manifest so a published figure traces to the exact
    configuration that produced it.
    """
    blob = json.dumps(to_dict(cfg), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def load_demand_config(path: str | Path) -> DemandConfig:
    """Load and validate a demand scenario. The only entry point for parameters."""
    path = Path(path)
    with path.open() as fh:
        raw = yaml.safe_load(fh)

    adoption_raw = dict(raw.get("adoption", {}))
    if "validation_events" in adoption_raw:
        adoption_raw["validation_events"] = tuple(
            (int(m), float(e)) for m, e in adoption_raw["validation_events"]
        )

    cfg = DemandConfig(
        name=raw["name"],
        seed=int(raw["seed"]),
        n_steps=int(raw.get("n_steps", 120)),
        steps_per_year=int(raw.get("steps_per_year", 12)),
        market=MarketConfig(**raw.get("market", {})),
        product=ProductConfig(**raw.get("product", {})),
        adoption=AdoptionConfig(**adoption_raw),
        notes=raw.get("notes", ""),
    )
    return validate(cfg)


def load_sweep_grid(path: str | Path) -> dict[str, list[Any]]:
    """Read the optional `sweep:` block from a scenario file."""
    with Path(path).open() as fh:
        raw = yaml.safe_load(fh)
    return raw.get("sweep", {})


def set_path(cfg: DemandConfig, dotted: str, value: Any) -> DemandConfig:
    """Return a new config with one nested field replaced. Configs are frozen."""
    parts = dotted.split(".")
    if len(parts) == 1:
        return replace(cfg, **{parts[0]: value})
    if len(parts) == 2:
        section, field_name = parts
        if section not in ("market", "product", "adoption"):
            raise ValueError(f"unknown config section: {section!r}")
        sub = getattr(cfg, section)
        return replace(cfg, **{section: replace(sub, **{field_name: value})})
    raise ValueError(f"unsupported parameter path: {dotted!r}")
