# Copyright (c) 2026 Category One Limited. All rights reserved.
# Licensed for inspection, execution and verification only. See LICENSE.

"""Economic core of the Geno simulation.

=============================================================================
EVERY FUNCTION IN THIS FILE IS A PLACEHOLDER.

The bodies below are deliberately simple, transparent, and almost certainly
NOT your design. They exist so the harness runs end-to-end and the
reproducibility machinery can be verified before the real model goes in.

Replace each body marked  # >>> REPLACE  with your actual equations. The
signatures are the contract with the engine; keep them, change the insides.
Each stub documents what the engine expects back and why it matters.
=============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import MechanismConfig, ReserveConfig


@dataclass
class State:
    """Mutable simulation state, advanced one step at a time."""

    step: int
    cic_supply: float
    geno_supply: float
    reserve_value: float
    claims_outstanding: float
    m_fiat: float
    velocity: float
    price: float
    pending_redemptions: float
    redemption_queue: list[tuple[int, float]]
    floor_breached: bool = False


def backing_ratio(state: State, reserve: ReserveConfig) -> float:
    """Reserve assets per unit of redeemable claim, in numeraire terms.

    This is the number that determines whether the arbitrage floor holds.
    Note the accounting: a CIC sale adds proceeds to `reserve_value` AND adds
    a matching claim to `claims_outstanding`. Both move together, so sales
    leave this ratio unchanged. Only `external_capital` raises it above 1.0.
    """
    denom = state.claims_outstanding * reserve.redemption_ratio
    if denom <= 0:
        return float("inf")
    return state.reserve_value / denom


# ---------------------------------------------------------------------------
# 1. Oracle: what the mechanism believes M_fiat to be
# ---------------------------------------------------------------------------

def observe_m_fiat(
    history: np.ndarray,
    step: int,
    lag: int,
    noise_sd: float,
    rng: np.random.Generator,
) -> float:
    """Return the mechanism's *observed* M_fiat, not the true value.

    The mirror mechanism cannot act on ground truth. It acts on a feed with
    latency and error. Keeping this separate from the true series is what
    lets the simulation surface oracle-induced instability, which is a
    failure mode that vanishes if you assume perfect information.

    # >>> REPLACE with your actual data source model: update frequency,
    # >>> staleness behaviour, and what happens when the feed fails entirely.
    """
    idx = max(0, step - lag)
    observed = float(history[idx])
    if noise_sd > 0:
        observed *= float(rng.normal(1.0, noise_sd))
    return observed


# ---------------------------------------------------------------------------
# 2. Mirror mechanism: CIC supply response to observed fiat expansion
# ---------------------------------------------------------------------------

def cic_supply_delta(
    state: State,
    observed_m_fiat: float,
    prev_observed_m_fiat: float,
    mech: MechanismConfig,
) -> float:
    """Change in effective CIC supply for this step.

    Paper 3 asserts d(S_CIC_effective)/d(M_fiat) < 0. The placeholder below
    implements the simplest possible version of that sign condition. Your
    real rule presumably includes the fee-reutilisation term and the
    threshold behaviour from Paper 4.

    # >>> REPLACE with the supply rule from Paper 3/4.
    """
    if prev_observed_m_fiat <= 0:
        return 0.0
    fiat_growth = (observed_m_fiat - prev_observed_m_fiat) / prev_observed_m_fiat
    return -mech.mirror_sensitivity * fiat_growth * state.cic_supply


# ---------------------------------------------------------------------------
# 3. Fee flow
# ---------------------------------------------------------------------------

def fee_flows(
    transaction_volume: float, mech: MechanismConfig
) -> tuple[float, float]:
    """Split fees into (to_reserve, to_geno_issuance).

    # >>> REPLACE with the actual fee schedule, including any tiering and
    # >>> the treasury share if one exists.
    """
    total_fee = transaction_volume * mech.fee_rate
    return (
        total_fee * mech.fee_split_to_reserve,
        total_fee * mech.fee_split_to_geno,
    )


# ---------------------------------------------------------------------------
# 4. Velocity governor
# ---------------------------------------------------------------------------

def measure_velocity(
    volume_history: np.ndarray, supply: float, step: int, window: int
) -> float:
    """Trailing velocity estimate over `window` steps.

    The lag here is load-bearing. A governor acting on a stale velocity
    reading is a delayed feedback loop, and delayed feedback loops oscillate.
    If your on-chain measurement differs, change it here rather than
    assuming instantaneous observation.

    # >>> REPLACE if your velocity definition differs.
    """
    if supply <= 0:
        return 0.0
    lo = max(0, step - window)
    if step <= lo:
        return 0.0
    return float(volume_history[lo:step].mean()) / supply


def geno_delta(state: State, mech: MechanismConfig, geno_issued: float) -> float:
    """Net change in GENO supply: issuance from fees minus burn.

    # >>> REPLACE with the Paper 4 burn rule, including the exact trigger
    # >>> conditions at theta_min and theta_max.
    """
    burn = 0.0
    if state.velocity > mech.theta_max:
        excess = state.velocity - mech.theta_max
        burn = mech.geno_burn_rate * excess * state.geno_supply
    return geno_issued - burn


# ---------------------------------------------------------------------------
# 5. Price formation  <-- the assumption that dominates every result
# ---------------------------------------------------------------------------

def price_update(
    state: State,
    reserve: ReserveConfig,
    demand: float,
    supply_delta: float,
) -> float:
    """Return the new CIC price in numeraire units.

    With enforceable redemption, price is bounded below by the redemption
    value: arbitrageurs buy below the floor and redeem. The placeholder
    applies a simple demand/supply adjustment and then clamps at the floor,
    but ONLY while reserves can actually honour redemption. When the backing
    ratio falls below 1.0 the floor is no longer enforceable and the clamp
    is removed. That transition is the single most important behaviour in
    this file.

    # >>> REPLACE with your price model. State your demand curve explicitly.
    """
    floor = reserve.redemption_ratio if backing_ratio(state, reserve) >= 1.0 else 0.0

    if state.cic_supply <= 0:
        return floor

    pressure = demand / state.cic_supply
    raw = state.price * (1.0 + 0.05 * (pressure - 1.0)) - 0.01 * supply_delta / max(
        state.cic_supply, 1.0
    )
    return max(raw, floor)


# ---------------------------------------------------------------------------
# 6. Redemption mechanics
# ---------------------------------------------------------------------------

def settle_redemptions(
    state: State, reserve: ReserveConfig, step: int
) -> tuple[float, float]:
    """Settle any redemption requests whose lag has elapsed.

    Returns (claims_retired, reserve_paid_out). If reserves are insufficient
    the settlement is partial and `floor_breached` is set. Gating rules, if
    your design has them, belong here.

    # >>> REPLACE with your actual redemption policy: who may redeem, minimum
    # >>> sizes, fees, gating, and whether settlement is at spot or at ratio.
    """
    due = sum(amount for due_step, amount in state.redemption_queue if due_step <= step)
    state.redemption_queue = [
        (d, a) for d, a in state.redemption_queue if d > step
    ]
    if due <= 0:
        return 0.0, 0.0

    owed = due * reserve.redemption_ratio
    if owed <= state.reserve_value:
        return due, owed

    state.floor_breached = True
    settled_claims = state.reserve_value / reserve.redemption_ratio
    return settled_claims, state.reserve_value
