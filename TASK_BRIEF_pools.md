# Task brief — household savings deposit figures

**Estimated time:** 2–4 hours. No specialist knowledge required.
**Deliverable:** one filled-in table (below), sent back as a spreadsheet or plain text.

---

## What we need and why

We are compiling household savings deposit totals by country. Some are
already sourced. About a third are currently estimates, and we need them
replaced with published figures so every number in our work can be traced to
a citable source.

**We need HOUSEHOLD deposits specifically — not total deposits.** Total
deposits include corporate and government money, which is not what we are
measuring. This distinction is the single most important part of the task.

---

## Where to get it

The IMF **Financial Access Survey (FAS)** publishes this for most countries
on one consistent definition. Easiest access is via FRED:

**https://fred.stlouisfed.org**

Type the series code into the search box at the top. Series codes follow a
fixed pattern:

| What it is | Pattern | Brazil example |
|---|---|---|
| Household deposits, national currency | `{ISO3}FCLODCHXDC` | `BRAFCLODCHXDC` |
| Household deposits, % of GDP | `{ISO3}FCLODCHGGDPPT` | `BRAFCLODCHGGDPPT` |
| ALL deposits (fallback only) | `{ISO3}FCLODCXDC` | `BRAFCLODCXDC` |

`{ISO3}` is the three-letter country code: BRA, IDN, MEX, VNM, PHL, NGA,
EGY, PAK, ARG, CAN, AUS, CHE, SWE, NOR, DNK, ZAF, THA, MYS, COL, CHL, PER,
BGD, KEN, MAR.

The IMF also publishes FAS directly at **https://data.imf.org** if FRED does
not have a particular country.

---

## What to record for each country

1. **Series code used** (e.g. `BRAFCLODCHXDC`)
2. **Value** — exactly as shown, do not round
3. **Year** of that value
4. **Currency** (FRED says "National Currency" — note which currency that is)
5. **Whether it is household-only or total** — critical, see below
6. **URL** of the page

---

## If the household series does not exist

Some countries do not report the household breakdown. In that case:

1. Record the **total** deposits series (`{ISO3}FCLODCXDC`) instead
2. **Mark it clearly as TOTAL, not household**
3. Note in the comments column that a household figure was unavailable

Do **not** estimate a household share yourself. Just flag it. We will handle
the adjustment and record it as derived rather than cited.

---

## Table to fill in

| Country | ISO3 | Series code used | Value | Year | Currency | Household or Total? | URL | Comments |
|---|---|---|---|---|---|---|---|---|
| Brazil | BRA | | | | | | | |
| Indonesia | IDN | | | | | | | |
| Mexico | MEX | | | | | | | |
| Vietnam | VNM | | | | | | | |
| Philippines | PHL | | | | | | | |
| Nigeria | NGA | | | | | | | |
| Egypt | EGY | | | | | | | |
| Pakistan | PAK | | | | | | | |
| Argentina | ARG | | | | | | | |
| Canada | CAN | | | | | | | |
| Australia | AUS | | | | | | | |
| Switzerland | CHE | | | | | | | |
| Sweden | SWE | | | | | | | |
| Norway | NOR | | | | | | | |
| Denmark | DNK | | | | | | | |
| South Africa | ZAF | | | | | | | |
| Thailand | THA | | | | | | | |
| Malaysia | MYS | | | | | | | |
| Colombia | COL | | | | | | | |
| Chile | CHL | | | | | | | |
| Peru | PER | | | | | | | |
| Bangladesh | BGD | | | | | | | |
| Kenya | KEN | | | | | | | |
| Morocco | MAR | | | | | | | |

Also record, as a cross-check on figures we already hold:

| India | IND | | | | | | | |
| Turkey | TUR | | | | | | | |

---

## Worked example

Searching `BRAFCLODCXDC` on FRED returns:

> Use of Financial Services, Liabilities: Outstanding Deposits at Commercial
> Banks for Brazil (BRAFCLODCXDC)
> 2024: 4,810,427,905,745.10
> Units: National Currency, Not Seasonally Adjusted

Recorded as:

| Brazil | BRA | BRAFCLODCXDC | 4,810,427,905,745.10 | 2024 | BRL | **TOTAL** | https://fred.stlouisfed.org/series/BRAFCLODCXDC | Household series BRAFCLODCHXDC not found; this is all deposits |

Note this example is the *fallback* case. Try `BRAFCLODCHXDC` first.

---

## Please do NOT

- Convert to US dollars. Leave figures in national currency; we handle FX.
- Round or reformat the numbers.
- Substitute a different data source without flagging it in Comments.
- Estimate anything. A blank with a note is more useful than a guess.
- Use total deposits without marking them as total.

---

## Questions to flag rather than resolve

- If a country has several similar-looking series, record all of them and
  note the ambiguity.
- If the most recent year differs a lot from the previous year, note it.
- If a series is marked DISCONTINUED, record it and say so.

Accuracy matters far more than completeness here. Twelve correct rows with
three flagged gaps is worth more than twenty-four rows with two silent
errors.
