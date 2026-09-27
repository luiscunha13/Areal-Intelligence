# Sector & Industry Intelligence Engine v2 — Design Specification

## 0. What changes from v1 and why

1. **RS-Ratio / RS-Momentum replace the broken RS/Momentum pair.** v1's "Relative Strength" was `sector return − SPY return`, which is a constant shift of raw momentum — mathematically guaranteed to rank identically to Momentum every time (proof: v1's live output had zero sectors in the Improving/Weakening quadrants, only Leading/Lagging — structurally impossible for the quadrant model to do otherwise). True RRG methodology derives both axes from the *ratio* `Sector/SPY`, making them genuinely independent.
2. **Three-tier universe (Sector → Industry Group → Theme Basket)** instead of 11 sectors alone, so a theme like "AI/software" isn't diluted inside a broad sector ETF.
3. **Regime-sensitivity replaces the frozen 50.0 "Macro Regime Fit."** v1's factor needs 5+ historical dates with an exact matching regime label — which is why it's stuck at neutral for every sector right now. A rolling regression against your macro engine's dimension scores works immediately, with no cold-start problem.
4. **Breadth data replaces reliance on the ETF price alone** — so a sector "leading" because of 3 mega-cap names doesn't get mistaken for broad sector health (the same mega-cap-masking issue we discussed for the S&P 500 itself).
5. **Fundamentals/theme layer is added as a separate, unblended score** — same principle as the macro engine: don't average signals that are supposed to sometimes disagree with each other.
6. **Cross-sectional ranking resolution is fixed.** Ranking only 11 items gives you steps of ~9 percentile points each — far too coarse to differentiate leaders. Expanding the ranking universe to sectors + industry groups (~35 items) and using continuous z-scores internally (percentile shown to the user, but not the computation's only resolution) fixes this.

---

## 1. Universe Hierarchy

```
Level 1 — GICS Sectors (11)          e.g. XLK, XLE, XLV, XLF, XLI, XLRE, XLB, XLP, XLY, XLU, XLC
Level 2 — Industry Groups (~20-25)   e.g. Semiconductors (SOXX/SMH), Software (IGV/XSW),
                                       Biotech (XBI), Banks (KBE), Insurance (KIE),
                                       Homebuilders (XHB), Aerospace & Defense (ITA),
                                       Transportation (IYT), Retail (XRT), Oil & Gas E&P (XOP),
                                       Oilfield Services (OIH), Regional Banks (KRE), REITs by
                                       type (data center, residential, industrial), Media, etc.
Level 3 — Theme Baskets (custom)     e.g. AI Infrastructure, Cybersecurity, Clean Energy,
                                       Data Centers & Power Demand, Reshoring/Onshoring
```

**Level 2 selection rule**: only include an industry group if a liquid, low-expense-ratio ETF proxy exists (min. ~$500M AUM, tight spreads). Where no clean proxy exists, fall back to a custom-constructed basket of the largest constituents by market cap within that industry, cap-weighted, rebalanced quarterly.

**Level 3 theme baskets** are hand-curated constituent lists (not GICS-derived) with an explicit **revenue-exposure weight**, not just membership — e.g., a stock is included in "AI Infrastructure" weighted by the estimated % of its revenue tied to that theme, not equal-weighted or included as a binary flag. This is what lets the dashboard say "this basket is 70% concentrated in 4 names" — a stat your current page structurally cannot produce since it starts from sector ETFs, not constituent-level data.

---

## 2. Core Technical Factors (Levels 1 & 2, same formulas apply to both)

### Factor A: RS-Ratio (replaces v1's broken "Relative Strength")

```
Ratio_s(t) = 100 × (Price_s(t) / Price_SPY(t)) / SMA_n(Price_s / Price_SPY)
```

Where `SMA_n` is a smoothing window (typically 10-13 periods on weekly data, or equivalent on daily) applied to the raw price ratio to reduce noise. Normalize `Ratio_s` to a 0-100 cross-sectional score via z-score → sigmoid transform (not raw percentile rank — see Section 5) across the full Level 1 + Level 2 universe.

### Factor B: RS-Momentum (replaces v1's broken "Momentum")

```
RS-Momentum_s(t) = 100 × (RS-Ratio_s(t) / RS-Ratio_s(t − k)) 
```

This is the rate of change **of the ratio line itself** (k periods back, typically matching the smoothing window), not the sector's own raw price momentum. Because both axes are now derived from the same ratio series rather than one being a constant-shifted copy of the other, they are genuinely orthogonal — a sector can be high-Ratio/falling-Momentum (Weakening) or low-Ratio/rising-Momentum (Improving), which was structurally impossible in v1.

### Factor C: Trajectory / Tails (new — the single highest-value addition here)

Store the last N (default 10) periods of `(RS-Ratio, RS-Momentum)` coordinates per sector/industry. Render as a connected path on the rotation plane, not just today's dot. This is standard institutional RRG practice and is what actually makes the quadrant model useful: a sector sitting in "Leading" but curling downward toward "Weakening" over the last 4 periods is a materially different signal than one accelerating deeper into "Leading" — information a single snapshot throws away entirely.

### Factor D: Breadth (new)

```
Breadth_s = 0.5 × (% constituents above SMA50) + 0.5 × (% constituents above SMA200)
```

Computed from the constituent stock list per sector/industry (already planned per your v1 sub-page spec, §5.4 — this factor just makes use of data you already intended to have). This directly catches the "leading ETF, weak majority underneath" case: XLK can score 100 on price-derived Ratio/Momentum while Breadth reveals only 40% of its constituents are actually in uptrends, meaning the ETF's score is a handful of mega-caps carrying the average — the sector-level analog of the equal-weight-vs-cap-weight S&P divergence we discussed earlier.

### Factor E: Trend (continuous, replaces v1's 4-bucket binary)

```
Trend_s = 0.4 × clip(% distance from SMA200, −20%, +20%) rescaled to 0-100
        + 0.3 × clip(% distance from SMA50, −10%, +10%) rescaled to 0-100
        + 0.3 × clip(SMA200 20-day slope %, −5%, +5%) rescaled to 0-100
```

Continuous distance measures instead of binary flags — fixes v1's problem where 8 of 11 sectors tied at the maximum score with zero ability to differentiate "barely above SMA200" from "structurally strong uptrend."

### Factor F: Risk (kept from v1, upgraded)

```
Risk Penalty_s = (Volatility_20D × 100) + (|Drawdown| × 100) + (1 − ρ_s,SPY) × 20
Risk Score_s = max(10, 100 − Risk Penalty_s)
```

Same core formula as v1, with a new correlation-to-SPY term added so the score also reflects diversification value, not just standalone bounciness — a sector with identical volatility to another but lower correlation to the benchmark carries more genuine portfolio value.

---

## 3. Regime-Sensitivity Factor (replaces frozen "Macro Regime Fit")

Instead of requiring 5+ historical dates with an exact discrete regime label (which is why v1 is stuck at 50.0 for everything), regress each sector/industry's rolling returns against your macro engine's 6 dimension scores and their 3-month deltas:

```
Ret_s(t) = α_s + Σ β_s,d × DimensionScore_d(t) + Σ γ_s,d × ΔDimensionScore_d(t) + ε
```

Fit on a rolling 2-3 year window, refreshed monthly. This produces a live sensitivity profile per sector (e.g., "XLF has β = +0.6 to Rates, γ = +0.4 to ΔInflation") that works from day one — no need to wait years for enough historical instances of a specific discrete regime label to accumulate. The **Regime-Sensitivity Score** is then:

```
RegimeSensitivity_s = f(current macro dimension levels/momentum × sector's fitted β/γ coefficients)
```

normalized 0-100 across the universe. This also gives you something v1 could never produce: an explicit, inspectable answer to "why does the model think XLF benefits from the current regime" (because its historical β to Rates is high, and Rates is currently moving a certain way) — rather than an opaque historical-average lookup.

---

## 4. Fundamentals & Theme Layer (separate score — do not blend into Technical Score)

Applies at Level 2 (Industry Group) and Level 3 (Theme Basket), aggregated up from constituent-level data. Note: **within-sector breadth was relocated to Section 2, Factor D** (it's a price-derived question — "is the move broad" — not a fundamentals one), so it isn't duplicated here.

### 4.1 Estimate Revision Breadth

```
RevisionBreadth_s(t) = (UpRevisions_30d − DownRevisions_30d) / TotalActiveEstimates_30d
```

Computed per constituent, then cap-weighted up to the sector/industry level. Blend a 30-day and 90-day version (60/40 weight) so a single-day estimate-cut cluster doesn't dominate. This tends to **lead** price momentum rather than confirm it — it's the closest thing in this layer to a genuinely forward-looking signal rather than a lagging fundamental.

### 4.2 Forward EPS Growth

```
ForwardEPSGrowth_s = Σ (marketcap_i / Σmarketcap_s) × ForwardEPSGrowth_i    [cap-weighted]
```

Normalized via z-score across the Level 1 + Level 2 universe (same resolution fix as Section 5).

### 4.3 Revenue Growth & Margin Trend

```
RevenueGrowth_s   = cap-weighted YoY revenue growth, trailing quarter
MarginTrend_s     = cap-weighted YoY change in operating margin, trailing quarter
QualityFlag_s     = "Clean growth" if RevenueGrowth > 0 AND MarginTrend ≥ 0
                     "Diluted growth" if RevenueGrowth > 0 AND MarginTrend < 0
```

The flag matters more than either number alone — it's what separates "growing and getting more profitable" from "growing by spending margin to do it," which look identical if you only chart revenue.

### 4.4 Capex / Investment Growth

```
CapexGrowth_s     = cap-weighted YoY growth in trailing-4-quarter capex sum
CapexIntensity_s  = Capex / Revenue, trend over trailing 4 quarters
```

For the AI theme specifically, also track a small **hand-curated hyperscaler capex line** (MSFT, GOOGL, AMZN, META capex guidance) as its own headline stat rather than folding it into the sector average — right now this handful of companies' spending is disproportionately important enough that averaging it into "Tech capex growth" would understate how concentrated the driver actually is.

### 4.5 Valuation Percentile (context, not blended into the score — see below)

```
ValuationPercentile_s(t) = PercentileRank(Multiple_s(t) within trailing 5-10Y history of Multiple_s)
```

Use a **sector-appropriate multiple**, not P/E everywhere — P/E is distorted for financials (leverage), doesn't apply cleanly to REITs (use FFO multiple instead), and is noisy for cyclical Energy earnings (use EV/EBITDA). A one-size-fits-all multiple would quietly break this factor for several sectors.

### 4.6 Thematic Revenue Concentration (Level 3 baskets only)

```
ThemeConcentration_basket = Σ (constituent_i weight × RevenueExposure_i%)
TopN_Contribution_basket  = % of the basket's weighted move contributed by its top 4 constituents
```

`RevenueExposure_i%` (what share of a company's revenue is genuinely theme-linked, e.g. Azure/AI-cloud revenue vs. total Microsoft revenue) has no clean free-data source — start with manual curation for your first basket or two, using whatever segment reporting companies already break out (Azure, AWS, Google Cloud are disclosed segments; most aren't). NLP-based tagging from earnings call transcripts is a reasonable phase-2 upgrade once the basket list is proven useful, not a day-one requirement.

### 4.7 Scoring — don't blend valuation or concentration into the growth-quality number

```
Fundamentals Growth-Quality Score (0-100) =
    0.30(RevisionBreadth) + 0.25(ForwardEPSGrowth) + 0.25(RevenueGrowth & MarginTrend) + 0.20(CapexGrowth)
```

Valuation Percentile and Thematic Concentration are deliberately **excluded** from this blend and shown as standalone contextual stats instead. Reason: "expensive" isn't inherently bad the way "estimates being cut" is — a sector can have strong fundamentals *and* be expensive, and that's an expected, not contradictory, combination. Blending them into one number would force the same false choice the macro composite and the technical/fundamentals split were both built to avoid.

**Output pattern** — three adjacent readouts per sector, never merged:

> XLK: Technical 88.8 (Leading, trajectory strengthening) · Fundamentals Growth-Quality 76 (strong revision breadth, clean margin trend) · Valuation: 91st percentile of its own 10Y forward P/E range (richly valued)

### 4.8 Data sourcing — the honest constraint

Two of these six metrics **cannot be built from free data**, and it's worth knowing that going in rather than discovering it mid-build:

| Data need | Free option | Realistic option |
|---|---|---|
| Revenue, margins, capex (4.3, 4.4) | SEC EDGAR XBRL (free, but raw — needs parsing per filer) | Financial Modeling Prep or Alpha Vantage processed financials (cheap, much less integration work) |
| Forward EPS estimates & revisions (4.1, 4.2) | Not really available free at usable quality | Financial Modeling Prep's estimates endpoint (affordable) — Zacks/Refinitiv/Visible Alpha are institutional-grade but expensive |
| Historical multiple percentile (4.5) | Not available pre-built at sector granularity anywhere cheap | You'll likely need to compute and **accumulate your own history** going forward (price ÷ consensus forward EPS, stored over time) — this factor will only become meaningful after 1-2+ years of your own data collection, not on day one |
| Thematic revenue exposure (4.6) | Segment disclosures only for a few large caps | Manual curation initially; NLP-over-transcripts later |

Given this, I'd sequence the build as: 4.1–4.4 first (feasible now with an affordable data provider), 4.6 as a small manually-curated pilot on just the AI basket, and 4.5 last — start logging the raw ratio immediately even before you display a percentile, since the percentile is only as good as the history you've accumulated.

This is the direct answer to last message's question — it lets the dashboard say explicitly when a sector's price strength is fundamentally justified versus running ahead of its own history, instead of collapsing both into one score that can't distinguish the two cases.

---

## 5. Cross-Sectional Normalization Fix

v1 ranked only 11 sectors, giving each ranking step ~9.1 percentile points — too coarse to meaningfully separate adjacent sectors, and the direct cause of the Trend-score ties. Two changes:

1. **Expand the ranking universe** to Level 1 + Level 2 combined (~35 instruments) for any percentile-based normalization, so each step is closer to ~2.9 points.
2. **Use z-scores internally**, converted to percentile only for display. A z-score → sigmoid transform preserves the *magnitude* of outperformance (a sector crushing the field vs. one barely ahead), which raw rank position always discards regardless of universe size.

---

## 6. Overall Score Structure

Two separate composites, shown side by side per sector/industry — never merged into one number, per the same principle applied to the macro engine's regime label vs. composite score:

```
Technical Score = 0.30(RS-Ratio) + 0.25(RS-Momentum) + 0.20(Trend) + 0.15(Breadth) + 0.10(Risk)
Regime-Sensitivity Score = separate overlay (Section 3), shown as a modifier/tag, not blended in

Fundamentals Score = weighted combination of Section 4 metrics (weights TBD based on data availability)
```

Rotation Quadrant is computed purely from RS-Ratio (x-axis) × RS-Momentum (y-axis), now genuinely capable of producing all four quadrants since the two axes are mathematically independent.

---

## 7. Sub-Page Additions (`/sectors/[symbol]` and new `/industries/[symbol]`, `/themes/[basket]`)

Beyond v1's existing plan (profile, sub-factor gauges, multi-period returns, constituent list):

1. **RRG trajectory chart** — the last N periods plotted as a connected path on the Ratio/Momentum plane (Section 2, Factor C).
2. **Breadth chart** — % of constituents above SMA50/SMA200 over time, shown alongside the ETF's own price so divergence (price up, breadth falling) is visually obvious.
3. **Regime-sensitivity panel** — the fitted β/γ coefficients per macro dimension, so a user can see *why* the model favors or disfavors this sector right now, not just that it does.
4. **Fundamentals panel** — revision breadth trend, valuation percentile chart (current level marked on its own 5-10Y distribution), capex/revenue growth trend.
5. **Theme drill-down** (Level 3 only) — revenue-exposure-weighted constituent list with each name's % contribution to the basket's overall move.

---

## 8. Migration Notes (v1 → v2)

- Keep: raw price/return data pipeline, constituent list per sector (already planned in v1 §5.4), Risk factor's core vol+drawdown formula.
- Replace: RS calculation (constant-shift bug → true ratio-based RS-Ratio/RS-Momentum) — this is the priority fix, everything else downstream (quadrant classification) depends on it.
- Replace: Macro Regime Fit (discrete-date-matching → rolling regression) — same underlying data-backfill concern flagged for the macro engine; worth investigating whether it's one shared root cause.
- Replace: Trend's binary 4-bucket scoring → continuous distance-based scoring.
- Add: Level 2 (Industry Group) and Level 3 (Theme Basket) universes — start with a small, high-conviction Level 3 basket list (AI Infrastructure is the obvious first one given your current use case) rather than building out full theme coverage immediately.
- Add: Breadth factor (constituent-level MA data — likely already available if constituent lists are already being pulled per v1 §5.4).
- Add: Fundamentals layer — this is the largest net-new data requirement (needs an earnings-estimates/consensus data source you may not currently have; flag as a separate data-sourcing task before implementation).
- Add: trajectory/tails storage (small addition — just persist last N periods of Ratio/Momentum coordinates per instrument).
