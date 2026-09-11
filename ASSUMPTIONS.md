# Assumptions Register — CIC Demand Model

Every parameter, its value, its source, and its evidential status.

**Status definitions**

| Status | Meaning |
|---|---|
| **cited** | Taken from a named published source |
| **derived** | Computed from cited figures; calculation stated |
| **estimate** | Author's judgement. Not measured. Must be swept. |
| **unmeasured** | No data exists. Swept across full plausible range. |

Anything that cannot be classified does not belong in the model.

---

## 1. Market structure

| Parameter | Value | Status | Source / note |
|---|---|---|---|
| `local_inflation` (EM high) | 30% | cited | National CPI, Argentina/Nigeria/Turkey class |
| `local_inflation` (EM mod) | 6% | cited | India, Brazil, Indonesia run 4–6% |
| `local_inflation` (DM) | 3% | cited | Developed-market CPI |
| `us_inflation` | 3% | cited | US CPI |
| `pool_local / pool_stable / pool_other` | varies | **estimate** | Split of household savings by current holding. Directionally informed by Chainalysis transaction-share data, but transaction share ≠ balance share. **Unvalidated.** |
| `median_balance` | 1,500–9,000 USD | **estimate** | Order-of-magnitude judgement |
| `balance_sigma` | 1.2 | **estimate** | Lognormal shape; not fitted to any wealth distribution |
| `spend_events_per_year` | 10–20 | **estimate** | No source |
| `smartphone_access` | 0.65–0.95 | cited | ITU / GSMA penetration, approximate |

## 2. Product terms

| Parameter | Value | Status | Note |
|---|---|---|---|
| `protection_rate` | 1.0 | **design assumption** | Taken as given per the project's specification. **Not independently verified.** All results are conditional on the mechanism delivering as specified. |
| `roundtrip_spread` | 1% (swept 0.25–3%) | **unmeasured** | No live market exists. Requires market-maker indications. |
| `spread_floor` | 0.2% | **estimate** | Assumed competitive floor |
| `redemption_fee` | 7% | design parameter | Backstop path only; not on the spend path |

## 3. Adoption behaviour — the weakest section

| Parameter | Value | Status | Note |
|---|---|---|---|
| `awareness_external` | 0.10 (swept 0.005–0.20) | **estimate, calibrated** | Calibrated to observed stablecoin diffusion under active suppression (see §5). **Highest-leverage parameter in the model.** |
| `awareness_internal` | 0.40 | **estimate** | Word-of-mouth coefficient. No empirical basis. |
| `trust_threshold_mean/sd` | 0.35 / 0.25 | **unmeasured** | Swept 0.15–0.60. Low leverage. |
| `trust_decay_per_year` | 0.10 | **estimate** | Assumed track-record effect |
| `churn_base` | 5%/yr | **estimate** | No source |
| `target_allocation` anchors | 0.20–0.75 | **unmeasured** | Saturation share. **No external anchor used** — see §6. Swept. |
| `dollar_stress_prob × severity` | 0–0.10 × 0–0.40 | **unmeasured** | Perceived dollar tail risk. Unmeasurable today. Swept. |

## 4. Savings pools

Primary source where available: **IMF Financial Access Survey**, "Outstanding
Deposits by Households at Commercial Banks" — FRED series `{ISO3}FCLODCHXDC`
(level) and `{ISO3}FCLODCHGGDPPT` (% of GDP). One definition across all
countries. This resolves the US/euro-area comparability defect noted in the
previous version, at the cost of a commercial-banks-only measure that
excludes state savings schemes (NS&I), some building societies, and money
market funds.

Where a FAS level was not retrieved, the figure is **derived** as nominal GDP
× an assumed household-deposit/GDP ratio, with the ratio banded against the
two FAS ratios that were retrieved: **India 39.9%** and **Turkey ~19%**. Those
bands are judgement, and are marked `derived`, not `cited`.

| Pool | $tn | Status | Accessible | Source |
|---|---|---|---|---|
| US | 8.83 | **cited** | yes | FRED BOGZ1FL193030205Q (Z.1) — Households |
| Euro area | 10.35 | **derived** | yes | ECB blog Oct 2024: EUR151bn cross-border = 1.6% of all household deposits => EUR9.44tn |
| UK | 2.33 | **cited** | yes | IMF FAS via FRED GBRFCLODCHXDC, 2024 = GBP1,790,191m |
| Japan | 7.51 | **cited** | yes | BoJ Flow of Funds, Q1 2026: household cash and deposits JPY1,126tn |
| Other DM | 3.20 | **derived** | yes | Canada, Australia, Switzerland, Nordics. GDP x household-deposit ratio banded 30-45% on FAS com |
| China | 22.50 | **cited** | NO | PBoC household savings, record CNY160tn (2025) |
| Russia | 0.60 | **derived** | NO | GDP x banded ratio. NOT retrieved. |
| India | 1.68 | **cited** | yes | IMF FAS via FRED INDFCLODCHGGDPPT: 39.92% of GDP (2024) |
| Brazil+Indonesia+Mexico+Vietnam+Philippines | 1.78 | **derived** | yes | GDP x household-deposit ratio banded 16-55% against the India (39.9%) and Turkey (~19%) FAS rat |
| Other EM | 2.10 | **derived** | yes | Thailand, Malaysia, South Africa, Colombia, Chile, Peru, Bangladesh, Kenya, Morocco and others. |
| Turkey | 0.27 | **cited** | yes | IMF FAS via FRED TURFCLODCHXDC, 2024 = TRY9.46tn |
| Argentina+Nigeria+Egypt+Pakistan | 0.32 | **derived** | yes | GDP x banded ratio (8-30%). FAS levels NOT retrieved. |

**Coverage: $43.1tn cited, $18.4tn derived, $0.0tn
estimate — of $61.5tn total.** Every remaining `derived` line names the
FAS series that would replace it.

**Denominator note:** the base is household *savings*, not M2. M2 includes
business deposits, checkable deposits and money market funds, none of which
are addressable. Substituting M2 roughly doubles every figure. The Z.1
headline household deposit figure ($20.5tn) includes MMF shares and is
likewise the wrong measure.

**Currency note, illustrated by Turkey.** Turkish household deposits grew
5.5× in lira between 2020 and 2024 (TRY1.73tn → TRY9.46tn) while barely
moving in USD. This is why high-inflation pools carry ~2% USD growth despite
30% local CPI, and why they stay small in dollar terms regardless of local
nominal expansion.

**China note.** At $22.5tn, China is the largest single pool and contributes
roughly 57% of Scenario C. Excluded from the base case on capital controls
and the crypto ban; must be reported separately, never folded into a global
total.

## 5. Diffusion calibration

Calibrated to observed stablecoin uptake achieved **under active
suppression** — Nigeria's 2021 bank ban, Argentine capital controls,
Lebanon's banking collapse. Regional on-chain value growth: LatAm +63%/yr,
Sub-Saharan Africa +52%, APAC +69%; global stablecoin volume +72% (2025).

Treated as a **floor**: legal distribution should exceed it.

**Known weakness:** these are transaction-*volume* growth rates, not
household penetration. Volume can rise because existing users transact more.
The mapping is loose and unvalidated. Chainalysis's grassroots penetration
index would be the correct series.

## 6. Rejected anchors, and why

**TIPS share of Treasury debt (~7.5% after 29 years)** — used in an earlier
draft as the low-gain saturation anchor. **Removed.** Category error: TIPS
competes for money already allocated to government bonds by investors who
also hold equities and property, so a small dedicated sleeve is rational for
them. The population modelled here holds cash savings with no protection from
any source. Different denominator, non-transferable number.

TIPS remains useful for the diffusion *timescale* — roughly 20 years from
launch to plateau, with a sovereign issuer and universal distribution — which
is why a 10-year horizon leaves the model mid-curve.

**On-chain holding-period data** — considered and not used. Available
datasets cannot cleanly separate traders from savers at the required
granularity. Note this cuts both ways: the same limitation applies to the
Goldman Sachs and Chainalysis figures cited in support of the demand thesis.

## 7. What this model cannot say

- It **cannot predict adoption.** It shows what follows from stated assumptions.
- It **cannot validate the mechanism.** Full protection is assumed, not tested.
- It **cannot measure demand.** No dataset exists on general-public demand for
  an inflation-protected savings instrument. Every available source samples
  crypto users or measures a different product.
- **Absolute figures are not forecasts.** Only the relative sensitivities held
  across the full sweep, and only those should be reported as findings.

## 8. Findings that survived the full parameter sweep

1. **Awareness dominates** — roughly 21× the leverage of round-trip spread,
   and far more than the trust threshold. Distribution is the binding
   constraint, not product economics.
2. **The local-currency pool >> the USD-stablecoin pool** as an adoption
   source, by 4:1 to 47:1 depending on dollar tail-risk assumptions. Anyone
   already holding USD stablecoins gains only ~3%/year from switching,
   identically in Buenos Aires and London.
3. **Ten-year outcomes are rate-limited, not ceiling-limited.** A 1.8× wider
   saturation assumption produces well under 1.8× adoption, because realistic
   diffusion reaches only a fraction of any plateau within a decade.
4. **Dollar tail risk changes composition more than magnitude** — it converts
   the stablecoin pool without materially raising the total.

## 9. Measurements that would most improve this model

Ranked by expected value per unit cost:

1. **Landing-page conversion test**, two target markets, real product terms —
   measures the highest-leverage parameter directly. ~£3–5k, 2–3 weeks.
2. **General-population survey** (YouGov/Ipsos omnibus), screened for savings
   balance — the only route to demand data uncontaminated by crypto-user
   sampling. ~£5–15k.
3. **Chainalysis grassroots penetration index** — replaces the volume-growth
   proxy currently used for diffusion calibration.
4. **Market-maker spread indications** — the only unmeasured product term.

---

# Addendum — model v3

v1 (`demand.py`) and v2 (`demand_v2.py`) are retained unchanged. v3
(`demand_v3.py`) is the current model. Three structural changes:

**1. Access is exchange-account penetration** (CITED, 2026): US ~30% of
adults, UK ~24%, Turkey ~25.6% of internet population, Brazil ~20.6%, South
Africa ~19.6%, global ~21% of internet-connected adults. Age gradient steep:
male ownership ~16.2% at 25-34, ~3.2% at 65+. Day-one reach is this
population, because in-app MPC wallets plus DEX liquidity make purchase a
two-tap operation requiring no listing decision.

`account_ceiling` (0.35-0.95, SWEPT) is the long-run maximum. The high end
assumes access arrives through banks and payment apps rather than crypto
exchanges, in which case the ceiling is bank-account penetration (~95% in
developed markets) rather than exchange penetration.

**2. Two-population diffusion.** Word of mouth is fast within the
account-holding population (the listener can act immediately) and slow
across to non-holders (the listener must first open an account). At ~25%
penetration the speaking population is not insular.

**3. Experience-based allocation ramp.** Households start small and increase
with time successfully held. Replaces v2's buffer-bounded allocation, which
allowed ~97% of savings within two years and produced an indefensible 63%
developed-market share. Testable implication: mean allocation across
adopters stays well below the ceiling while adoption is growing.

## v3 global sensitivity (2,000 samples per market, 17 parameters varied)

| Parameter | DM | EM high |
|---|---|---|
| trust_threshold_mean | **-0.545** | -0.174 |
| reach_external | +0.297 | **+0.415** |
| account_ceiling | +0.251 | +0.335 |
| alloc_ceiling | +0.250 | +0.364 |
| salience_trust_effect | +0.224 | +0.141 |
| alloc_ramp_per_year | +0.222 | +0.301 |
| account_growth | +0.182 | +0.302 |

Adoption occurred in 99.9% of developed-market samples and 100% of
emerging-market samples. Median year-10 outcome 13.0% and 12.2% of household
savings balances; 5th percentiles 0.99% and 3.63%.

**Trust is the dominant developed-market constraint; awareness dominates in
high-inflation markets.** v1's single-parameter dominance was an artefact of
that model having only one working constraint.

## Corrections to earlier reported findings

- The "4:1 to 47:1 local-currency vs stablecoin source ratio" (v1) was an
  artefact of a friction bug that made the stablecoin-pool advantage
  negative. The real asymmetry was 3.75x in allocation intensity, which was
  itself simply `alloc_high / alloc_low` -- an input, not a finding.
- The "below 2% awareness it fails" boundary is largely a property of Bass
  diffusion, and its location moves with the word-of-mouth coefficient.
- v1's "awareness at 13.7x leverage" was inflated by one-at-a-time sweeping.

## Outstanding

- v3 year-1 figure (~$90bn) has no precedent and should not be published.
- v3 year-10 scenario B (~$10.8tn) is ~34x the current stablecoin market.
  Driven by `alloc_ceiling`, which is unmeasured.
- v3 LHS run at 2,000 samples per market; 4,000 recommended.
- `protection_rate = 1.0` remains a design assumption, not a tested result.
