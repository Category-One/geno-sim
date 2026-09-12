# Retail Demand for a Counter-Inflation Currency: Methods

**Category One Limited (British Virgin Islands)**
Model version 3 · Draft

---

## 1. What this study does and does not do

This is a simulation of retail adoption. It asks: *given a monetary
instrument with stated properties, and given stated assumptions about how
households learn of it, gain access to it, and come to trust it, what share
of household savings would move into it over ten years?*

It does not:

- **Predict adoption.** It shows what follows from its assumptions.
- **Validate the instrument.** Full purchasing-power protection is an input
  (`protection_rate = 1.0`), taken as given per the system's specification.
  Every result is conditional on that holding.
- **Measure demand.** No dataset exists on general-public demand for an
  inflation-protected savings instrument. Every available source either
  samples existing cryptocurrency users or measures a different product.
- **Model commercial or regulatory feasibility.** Whether the instrument may
  lawfully be distributed in a given jurisdiction is out of scope, with one
  exception noted in §6.

The central result is not a figure. It is that adoption occurs across
essentially the entire parameter space, including at its pessimistic
extremes.

---

## 2. Structure

An agent-based discrete-time model, monthly steps, ten-year horizon, run
over populations of 25,000–100,000 synthetic households per market.

Each household carries a savings balance drawn from a lognormal
distribution, a current holding (local currency, US-dollar stablecoin, or
other store of value), an annual savings-drawdown rate, a trust threshold,
and states for awareness and account access.

Each month, a household may become aware, may gain access, and — if aware,
with access, and with a net advantage exceeding its trust threshold — may
adopt. Allocation then rises with time successfully held.

### 2.1 Marginal gain

The benefit from adopting depends on what a household currently holds, not
on where it lives:

| Current holding | Annual gain |
|---|---|
| Local currency | Local inflation |
| US-dollar stablecoin | US inflation + perceived dollar tail risk |
| Other store of value | Half of US inflation + tail risk |

This asymmetry is the model's central economic mechanic. A household in
Argentine pesos gains roughly 30% a year; one already holding USDT gains
roughly 3% — identically in Buenos Aires and in London. Treating these as
one population is the principal source of overstatement in conventional
total-addressable-market estimates.

### 2.2 Access

Day-one access is the population already holding a cryptocurrency exchange
account. In-app MPC wallets combined with decentralised-exchange liquidity
make purchase a two-tap operation for that group, requiring no listing
decision by any venue. Households without an account must first open one and
complete identity verification.

**Account penetration estimates disagree materially**, and the model's
access parameter is sensitive to which is used. For the United States:

| Source | Estimate | Sample | Measures |
|---|---|---|---|
| Security.org, 2026 Cryptocurrency Annual Consumer Report | 30% of adults (70.4m) | 992 adults | Currently own |
| National Cryptocurrency Association / Harris Poll, Feb–Mar 2026 | ~25% (67m) | 10,000 holders | Currently own |
| Motley Fool Money, 2026 Cryptocurrency Investor Trends Survey | 22% | 2,000 adults | Own, incl. via ETF |
| Pew Research Center | ~20% | 8,512 adults | Have ever used |
| Federal Reserve, Survey of Household Economics and Decisionmaking, Oct 2025 | 10% used or held; 7% held as investment | ~13,000, nationally representative | Used or held in past year |

The Federal Reserve figure is the most methodologically rigorous —
nationally representative, largest sample — and is three times lower than
the commercial surveys. The discrepancy is partly definitional: SHED
measures activity within the past year, whereas the commercial surveys
measure current ownership, and commercial sampling frames skew toward
online panels with higher digital-finance participation.

**What this model needs is neither quantity exactly.** Access requires a
funded exchange account, which persists after a holder sells. That is
closer to "has ever owned" than to "used in the past year," which argues
for the upper end of the range. The parameter is nonetheless swept, and
this disagreement is the strongest argument for doing so.

Other markets, from published 2026 figures: United Kingdom ~24% (up from
18%); Turkey ~25.6% of the internet population; Brazil ~20.6%; South Africa
~19.6%; globally ~21% of internet-connected adults, or approximately 9.9% of
world population (~560 million holders by Triple-A's count; 741 million by
Crypto.com's, the divergence again reflecting methodology).

The age gradient is steep. Security.org's 2026 breakdown places 32% of US
owners in the 30–44 band, 31% in 45–59, 19% in 18–29 and 17% at 60+.
Federal Reserve data likewise concentrates participation among under-45s and
higher-income households.

The long-run ceiling is swept between 0.35 and 0.95. The upper end
corresponds to access arriving through banks and payment applications rather
than cryptocurrency exchanges, in which case the relevant ceiling is
bank-account penetration.

### 2.3 Diffusion

Two populations. Word of mouth is fast *within* the account-holding
population, because a listener can act immediately. It is slow *across* to
non-holders, because acting first requires opening an account. At roughly
25% penetration the speaking population is not insular; most households know
several account holders.

Diffusion speed is anchored on M-Pesa rather than on cryptocurrency
adoption. M-Pesa reached 43% of Kenyan households within 17 months of its
March 2007 launch and approximately 70% within four years. Contemporary
accounts attribute this to its agent network — from 4,000 to 19,000
cash-in/cash-out outlets, against roughly 850 bank branches nationally —
rather than to advertising. The inference drawn is that distribution
infrastructure, not awareness, was the binding constraint.

### 2.4 Trust and salience

Protection-motivated switching is rapid when a threat is vivid and slow when
it is not. During the March 2023 Silicon Valley Bank episode, deposits moved
from regional to large banks within days with no yield differential
involved. Inflation's distinguishing feature is that it is a slow erosion
few households experience as a discrete loss.

Salience therefore modulates the trust threshold, through two channels
modelled separately because the evidence on them differs:

**Endogenous** — actual inflation prints, currency shocks, elections fought
on cost of living. Spikes and decays. Well evidenced: flood and earthquake
insurance take-up rises after nearby events and decays over following years.

**Manufactured** — campaign-driven, persistent while funded, lower ceiling.
Not well evidenced for this product. Distant-catastrophe appeals have
historically underperformed. An appeal that makes an already-incurred loss
legible is a different proposition with no clean reference class. Swept
across its full range, never assumed.

The trust threshold is set low but non-zero. Cohen and Dupas found
insecticide-treated bed-net take-up near 75% when free, collapsing to
roughly 20% at a small positive price — a discontinuity at zero rather than
an elasticity. A no-premium protective instrument should therefore face a
low barrier. It should not face none: a free bed net has no downside,
whereas moving savings into a novel instrument carries perceived principal
risk.

### 2.5 Allocation

Allocation rises with experience, not with the size of the benefit. A
household commits a small share on adoption and increases it for each year
successfully held, subject to a ceiling and to a liquid working buffer.

This produces a testable implication: mean allocation across adopters should
remain well below the ceiling for as long as adoption is growing, because
recent entrants drag the average down. In the baseline developed-market run,
48.4% of households have adopted by year ten while mean allocation stands at
39.8% against a 60% ceiling.

---

## 3. Data

| Quantity | Source |
|---|---|
| US household savings deposits | FRED `BOGZ1FL193030205Q` (Z.1), Q1 2026 |
| UK household deposits | IMF FAS via FRED `GBRFCLODCHXDC` |
| Japan household cash and deposits | Bank of Japan Flow of Funds, Q1 2026 |
| China household savings | People's Bank of China |
| India, Turkey, Argentina, Chile | IMF Financial Access Survey |
| Euro area household deposits | Derived from European Central Bank |
| Inflation rates | National consumer price indices |
| Account penetration | Security.org 2026; Fed SHED Oct 2025; Pew; NCA/Harris 2026 — see §2.2 for the disagreement between them |

Approximately 70% of the savings-pool total is cited; the remainder is
derived as nominal GDP multiplied by a household-deposit ratio banded
against the two Financial Access Survey ratios retrieved (India 39.9%,
Turkey ~19%). Each derived line names the series that would replace it.

Three material pools — Brazil, Indonesia and Mexico — do not report a
household breakdown to the Financial Access Survey, so complete citation is
not attainable from this source.

**Denominator.** The base is household *savings*, not M2. M2 includes
business deposits, transaction balances and money market fund shares, none
of which are addressable. Substituting M2 approximately doubles every
figure.

**Currency.** Pool growth rates are US-dollar denominated. Turkish household
deposits grew 5.5× in lira between 2020 and 2024 while barely moving in
dollars. High-inflation pools therefore carry low dollar growth despite high
local inflation.

---

## 4. Uncertainty

Behavioural parameters have no direct measurement, because no instrument of
this kind has been offered to this population. They are classified as:

- **cited** — traceable to a published figure
- **derived** — computed from cited figures, calculation stated
- **anchored** — set against a documented reference class
- **unmeasured** — plausible range only; swept, never fixed

The full classification is published in `ASSUMPTIONS.md`. No parameter falls
outside these four categories.

### 4.1 Global sensitivity analysis

Seventeen parameters were sampled simultaneously from continuous ranges
across 4,000 draws per market, rather than varied one at a time. One-at-a-
time sweeping holds other parameters at their defaults and systematically
overstates the leading parameter's influence.

Spearman rank correlation with year-ten share of household savings balances:

| Parameter | Developed | High-inflation |
|---|---|---|
| Trust threshold | **−0.511** | −0.132 |
| External reach | +0.287 | **+0.408** |
| Allocation ceiling | +0.273 | +0.379 |
| Account ceiling | +0.255 | +0.349 |
| Salience effect on trust | +0.221 | +0.140 |
| Account growth | +0.211 | +0.320 |
| Allocation ramp rate | +0.197 | +0.283 |
| Manufactured salience | +0.146 | +0.014 |
| Round-trip spread | −0.104 | −0.041 |

No parameter dominates. The constraints differ by market: **trust binds in
developed markets; awareness binds where inflation is high.** Manufactured
salience registers only where the threat is not already vivid.

### 4.2 Outcome distribution

| | Developed | High-inflation |
|---|---|---|
| 5th percentile | 1.12% | 3.87% |
| Median | 13.21% | 12.54% |
| 95th percentile | 37.82% | 30.63% |
| Adoption occurred | **99.92%** | **100%** |
| Self-sustaining | 92.0% | 98.8% |

Across 8,000 samples spanning seventeen simultaneously varied unmeasured
parameters, adoption occurred in all but three.

---

## 5. Reproducibility

A run is fully determined by its configuration file and seed. No global
random number generator, no wall-clock time, and no environment variable
enters the model. Each run writes a manifest recording the configuration
hash, seed, commit hash, library versions, and a checksum of every output.
Reference fixtures are committed, and the test suite fails if a different
environment produces different figures.

Code, configurations, and the assumptions register are published so results
can be reproduced, modified, or contested.

---

## 6. Scope boundaries and known limitations

**Categorical access barriers are treated as scenario boundaries.** Markets
with capital controls prohibiting the instrument are excluded from the base
case and reported separately, in the manner of an epidemiological study
excluding a population to which an intervention cannot lawfully be offered.
Jurisdiction-specific compliance questions are out of scope as
implementation-dependent.

**China is reported separately and never folded into a global total.** At
approximately $22.5tn it is the largest single pool and would dominate any
aggregate including it.

**Early-year figures carry the widest uncertainty.** The initial segment of
a diffusion curve is governed almost entirely by unmeasured parameters;
small changes move year one by multiples while barely affecting year ten.

**Terminal figures depend heavily on two unmeasured ceilings** — allocation
and account penetration — each swept but neither measured.

**Account penetration estimates vary threefold across published sources**
(§2.2). The baseline uses the upper end, on the reasoning that a funded
account persists beyond active holding. A reader preferring the Federal
Reserve figure should read the lower tail of the distribution rather than
the median.

**No competitive or regulatory response is modelled.**

**Corrections to earlier versions of this work** are set out in §7.

---

## 7. Corrections to earlier versions

Four findings reported during development were subsequently identified as
artefacts rather than results. They are recorded here because a reader
assessing the current model should know which earlier claims did not survive
scrutiny.

**Source-pool asymmetry.** Version 1 reported that local-currency holders
adopted at between 4:1 and 47:1 against holders of dollar stablecoins. This
was produced by an error in the friction calculation, which annualised
conversion cost by transaction count rather than by the portion of the
balance withdrawn, making the stablecoin cohort's net advantage negative.
Corrected, both cohorts adopt, and the asymmetry survives only in allocation
intensity.

**Allocation asymmetry of 3.75×.** This was the ratio of two configuration
values set by hand — an input restated, not a model output. Across a range
that moved the reported "finding" fivefold, the ten-year result varied by
17%.

**Awareness threshold.** Version 1 reported that adoption fails to become
self-sustaining below roughly 2% annual external reach. Any diffusion model
of this form has such a threshold; its location moves with the word-of-mouth
coefficient and disappears at high values. The structure is a property of
the functional form rather than a discovered feature of the instrument.

**Parameter leverage.** Version 1 reported awareness carrying 13.7 times the
influence of any other parameter. One-at-a-time sweeping holds other
parameters at their defaults and systematically overstates the leading one.
Under simultaneous sampling (§4.1) no parameter dominates, and the binding
constraint differs by market.

---

## 8. Measurements that would most improve this work

1. A landing-page conversion test in two target markets, with real product
   terms — measures the developed-market binding constraint directly.
2. A general-population survey screened for savings balance — the only route
   to demand data uncontaminated by cryptocurrency-user sampling.
3. Household penetration data rather than transaction-volume growth for
   diffusion calibration.
4. Market-maker spread indications, once a venue exists.

---

*Nothing in this document constitutes an offer to sell or a solicitation of
an offer to buy any security or financial instrument, nor investment,
financial, legal or tax advice. Outputs are conditional projections derived
from stated assumptions, many of them unmeasured. They are not forecasts.*
