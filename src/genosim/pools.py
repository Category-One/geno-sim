# Copyright (c) 2026 Category One Limited. All rights reserved.
# Licensed for inspection, execution and verification only. See LICENSE.

"""Household savings pools and aggregation to absolute figures.

These were previously inline in shell commands, which made the headline
dollar numbers untraceable. They are model INPUTS and belong here, versioned,
with a source and a status recorded against every figure.

STATUS VALUES
  cited      — taken from a named published source
  derived    — computed from cited figures; the calculation is stated
  estimate   — the author's judgement; NOT measured. Must be swept.

IMPORTANT SCOPE NOTE
The denominator is HOUSEHOLD SAVINGS, not M2. M2 includes business deposits,
checkable deposits and money market funds, none of which are addressable.
Using M2 roughly doubles every figure by counting money that was never in
scope. Do not substitute it.

CURRENCY NOTE
Growth rates are USD-denominated nominal growth in household deposits. For
high-inflation economies, local nominal growth is largely offset by currency
depreciation, so the USD-denominated pool grows far more slowly than local
CPI would suggest. This is why EM high-inflation carries a 2% growth rate
despite 30% local inflation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Status = Literal["cited", "derived", "estimate"]


@dataclass(frozen=True)
class Pool:
    """One savings pool, with provenance attached to the figure."""

    name: str
    value_usd_tn: float
    annual_growth: float
    curve: str                 # which adoption curve applies: dm | em_mod | em_high
    status: Status
    source: str
    accessible: bool = True    # False = capital controls / sanctions / bans
    note: str = ""


# ---------------------------------------------------------------------------
# Pool definitions
# ---------------------------------------------------------------------------
# All value_usd_tn figures below are ESTIMATE status: they are order-of-
# magnitude approximations assembled from general knowledge of national
# household deposit statistics, NOT retrieved from the source databases.
# Before publication each must be replaced with a cited figure from the
# relevant central bank or statistical agency (Fed Z.1 for the US, ECB BSI
# for the euro area, BoE Bankstats, BoJ Flow of Funds, RBI, BCB, etc.).

# Primary source where available: IMF Financial Access Survey (FAS),
# "Outstanding Deposits by Households at Commercial Banks".
#   FRED series {ISO3}FCLODCHXDC  (national currency, level)
#   FRED series {ISO3}FCLODCHGGDPPT (percent of GDP)
# One definition, all countries — this resolves the US/euro-area
# comparability defect noted in earlier versions, at the cost of using a
# commercial-banks-only measure that excludes NS&I-type state schemes,
# building societies in some jurisdictions, and money market funds.
#
# Where a FAS level was not retrieved, the figure is DERIVED as
#   nominal GDP x assumed household-deposit/GDP ratio
# with the ratio banded against the two FAS ratios that were retrieved
# (India 39.9%, Turkey ~19%). Those bands are the author's judgement and
# are marked "derived" rather than "cited".

POOLS: tuple[Pool, ...] = (
    # ---------------- Developed ----------------
    Pool("US", 8.83, 0.04, "dm", "cited",
         "FRED BOGZ1FL193030205Q (Z.1) — Households; Other Deposits Including "
         "Time and Savings Deposits, Q1 2026 = $8,834,692m",
         note="Time and savings only; excludes checkable deposits ($5.62tn, "
              "BOGZ1FL193020005Q) and money market fund shares."),
    Pool("Euro area", 10.35, 0.04, "dm", "derived",
         "ECB blog Oct 2024: EUR151bn cross-border = 1.6% of all household "
         "deposits => EUR9.44tn; at 1.10 USD/EUR = $10.35tn",
         note="TOTAL household deposits incl. overnight. Broader basis than "
              "the US line above — likely overstates in comparison."),
    Pool("UK", 2.33, 0.04, "dm", "cited",
         "IMF FAS via FRED GBRFCLODCHXDC, 2024 = GBP1,790,191m; at 1.30 "
         "USD/GBP = $2.33tn",
         note="Mintel reports GBP2.19tn for early 2026 on a broader basis "
              "(incl. NS&I and building societies) = ~$2.85tn. The FAS "
              "figure is used for cross-country consistency."),
    Pool("Japan", 7.51, 0.03, "dm", "cited",
         "BoJ Flow of Funds, Q1 2026: household cash and deposits "
         "JPY1,126tn; at 150 JPY/USD = $7.51tn"),
    Pool("Other DM", 3.20, 0.04, "dm", "derived",
         "Canada, Australia, Switzerland, Nordics. GDP x household-deposit "
         "ratio banded 30-45% on FAS comparators. NOT individually retrieved."),

    # ---------------- Restricted ----------------
    Pool("China", 22.50, 0.06, "em_mod", "cited",
         "PBoC household savings, record CNY160tn (2025); at 7.1 CNY/USD",
         accessible=False,
         note="Largest single pool. ~54% of any scenario including it. "
              "Capital controls and crypto ban. Report separately."),
    Pool("Russia", 0.60, 0.03, "em_mod", "derived",
         "GDP x banded ratio. NOT retrieved.", accessible=False,
         note="Sanctions."),

    # ---------------- EM moderate inflation ----------------
    Pool("India", 1.68, 0.08, "em_mod", "cited",
         "IMF FAS via FRED INDFCLODCHGGDPPT: 39.92% of GDP (2024); "
         "x ~$4.2tn nominal GDP = $1.68tn"),
    Pool("Brazil+Indonesia+Mexico+Vietnam+Philippines", 1.78, 0.07, "em_mod",
         "derived",
         "GDP x household-deposit ratio banded 16-55% against the India "
         "(39.9%) and Turkey (~19%) FAS ratios. Individual FAS levels NOT "
         "retrieved — replace with {ISO3}FCLODCHXDC series."),
    Pool("Other EM", 2.10, 0.06, "em_mod", "derived",
         "Thailand, Malaysia, South Africa, Colombia, Chile, Peru, "
         "Bangladesh, Kenya, Morocco and others. Residual estimate."),

    # ---------------- EM high inflation ----------------
    Pool("Turkey", 0.27, 0.02, "em_high", "cited",
         "IMF FAS via FRED TURFCLODCHXDC, 2024 = TRY9.46tn; at ~35 TRY/USD",
         note="Implies ~19% of GDP — the low end of the FAS band, and a "
              "direct illustration of the currency point: household "
              "deposits grew 5.5x in TRY from 2020-2024 while barely "
              "moving in USD."),
    Pool("Argentina+Nigeria+Egypt+Pakistan", 0.32, 0.02, "em_high", "derived",
         "GDP x banded ratio (8-30%). FAS levels NOT retrieved.",
         note="USD growth ~2%: local nominal growth offset by depreciation."),
)


def aggregate(curves: dict[str, list[float]], year: int,
              include_inaccessible: bool = False,
              grow_pools: bool = True) -> dict[str, float]:
    """Absolute CIC balances in USD bn at a given year.

    curves: mapping of curve name -> adoption share per monthly step.
    Returns a per-pool breakdown plus a total. The breakdown matters: a
    single total can conceal that one pool contributes the large majority.
    """
    idx = year * 12
    out: dict[str, float] = {}
    total = 0.0
    for p in POOLS:
        if not p.accessible and not include_inaccessible:
            continue
        share = curves[p.curve][idx]
        value = p.value_usd_tn * ((1 + p.annual_growth) ** year if grow_pools else 1.0)
        contribution = value * share * 1000.0      # -> USD bn
        out[p.name] = contribution
        total += contribution
    out["TOTAL"] = total
    return out


def provenance_table() -> str:
    """Render the pool assumptions with status and source, for the register."""
    lines = [f"{'pool':<20}{'$tn':>7}{'growth':>8}{'curve':>9}"
             f"{'access':>8}{'status':>10}  source"]
    for p in POOLS:
        lines.append(
            f"{p.name:<20}{p.value_usd_tn:>7.2f}{p.annual_growth:>8.1%}"
            f"{p.curve:>9}{str(p.accessible):>8}{p.status:>10}  {p.source}"
        )
    return "\n".join(lines)
