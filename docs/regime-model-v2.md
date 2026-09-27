# Macro Regime Engine v2 — Design Specification

## 0. What changes from v1 and why

Three structural fixes drive this redesign:

1. **Momentum replaces level as the primary regime axis.** The classic macro quadrant (Goldilocks / Overheat / Stagflation / Slowdown) is defined by whether growth and inflation are *accelerating or decelerating* — not by their absolute level. A Growth score of 65 means something completely different if it fell from 85 last quarter versus rose from 45. Levels still matter, but as an *intensity* layer, not the primary classifier.
2. **All 6 dimensions are used, all the time.** Rates, Liquidity, and Credit/Risk no longer sit idle outside the regime logic — they become a **Financial Conditions Amplifier** that scales confidence and severity, so nothing you compute is wasted.
3. **Hard AND-thresholds are replaced with continuous quadrant scoring + a persistence filter.** No more regime that's almost always "Neutral/Transition" because four independent conditions rarely align simultaneously — and no more single-noisy-print regime flips.

---

## 1. Primary Axes: Growth Momentum × Inflation Momentum

Define trailing momentum for each dimension score (default window: 3-month change, configurable):

```
ΔGrowth    = Growth_score(t) − Growth_score(t − 3mo)
ΔInflation = Inflation_score(t) − Inflation_score(t − 3mo)
```

Recall from v1: **higher Inflation_score = inflation cooling toward target**, so `ΔInflation > 0` means disinflation is accelerating; `ΔInflation < 0` means inflation is reheating.

### The four quadrants

| | ΔInflation > 0 (cooling) | ΔInflation < 0 (heating) |
|---|---|---|
| **ΔGrowth > 0** (accelerating) | **Goldilocks** — growth accelerating, inflation cooling. Best regime for risk assets. | **Overheat** — growth accelerating, inflation heating. Early-cycle heat; commodities/value outperform, bonds struggle. |
| **ΔGrowth < 0** (decelerating) | **Slowdown** — growth decelerating, inflation cooling. Defensive rotation; duration/bonds do well. | **Stagflation** — growth decelerating, inflation heating. Worst regime; cash/gold/commodities, avoid duration and growth equities. |

This is a strict improvement over a level-only quadrant because it's **always classifiable** — there's no "doesn't meet any threshold" fallback. Every observation has a sign for ΔGrowth and a sign for ΔInflation, so every observation lands in exactly one quadrant.

### Handling near-zero momentum (avoiding false precision)

Raw sign-of-delta is noisy near zero. Use a dead-band:

```
if |ΔGrowth| < ε_g:  ΔGrowth treated as 0 → "Growth: Stable"
if |ΔInflation| < ε_i: ΔInflation treated as 0 → "Inflation: Stable"
```

When one or both axes are in the dead-band, report the regime as a **transitional label** ("Goldilocks → Stable Growth", "Stable / Watching Inflation") rather than forcing a hard quadrant call. `ε_g`, `ε_i` should be calibrated as roughly 0.5× the trailing standard deviation of the 3-month score delta, so the dead-band scales with each dimension's natural noise.

---

## 2. Intensity Layer: Levels Determine Severity Within the Quadrant

Once the quadrant is set by momentum, the **levels** of Growth_score and Inflation_score determine how severe that quadrant is:

```
Intensity = f(Growth_score, Inflation_score, quadrant)
```

Example for Stagflation quadrant:
- Growth_score > 45 and Inflation_score > 40 → "Mild Stagflation" (deceleration from a still-decent base)
- Growth_score < 30 → "Severe Stagflation" (deceleration into outright contraction territory)

This resolves the old problem where "Growth < 30 AND Credit < 30 AND Risk < 30" had to *all* fire simultaneously to ever call a recession. Now: momentum tells you the *direction* (Slowdown/Stagflation), level tells you *how bad* — decoupled, so each does the job it's actually good at.

---

## 3. Rates Overlay: Policy Stance Confirms or Contradicts the Read

The Rates dimension doesn't get its own quadrant axis — it acts as a **confirming overlay** on the Inflation axis, because real policy stance is what actually transmits inflation conditions into markets.

```
Policy_Stance = "Restrictive" if DFII10 (10Y real yield) is above its trailing 5Y median
                                AND FEDFUNDS − Inflation_YoY > 0 (positive real fed funds rate)
                = "Accommodative" otherwise
```

Interaction effect:
- **Overheat + Restrictive policy** → higher confidence this regime reverses soon (Fed actively fighting it); treat as *late* Overheat.
- **Overheat + Accommodative policy** → lower confidence of imminent reversal; treat as *early/sustained* Overheat — historically the more dangerous combination (policy behind the curve).
- **Stagflation + Restrictive policy** → policy has less room to cut and support growth without reigniting inflation — most dangerous combination for risk assets.
- **Stagflation + Accommodative policy** → suggests policy easing is already underway to offset growth weakness — somewhat less severe.

This gets surfaced as a qualifier string appended to the regime label, not a separate score.

---

## 4. Financial Conditions Amplifier (FCA): Liquidity + Credit + Risk

```
FCA = 0.35(Liquidity_score) + 0.35(Credit_score) + 0.30(Risk_score) − 50
```

Range roughly −50 to +50. This is where Liquidity, Credit, and Risk finally do real work instead of sitting parallel to the regime call:

- **FCA > +15**: financial conditions are loose/supportive → amplifies upside regimes (Goldilocks, Overheat get higher confidence and asset-positive tilt), dampens downside regimes (a Slowdown with loose conditions is less likely to become a Stagflation/recession spiral).
- **FCA < −15**: financial conditions are tight/stressed → amplifies downside regimes, and critically, acts as an **early warning even inside upside quadrants** — e.g. Goldilocks with FCA falling sharply is the classic pre-2007 setup (growth still fine, inflation cooling, but credit/liquidity already cracking underneath). This is a case your v1 model structurally could not flag, since Liquidity/Credit only fed a parallel composite score that nothing else read.
- **−15 ≤ FCA ≤ +15**: neutral, no material amplification.

---

## 5. Regime Confidence (redesigned)

v1 confidence averaged all 6 dimensions' distance from 50 — which treats a strong Rates reading as just as informative as a strong Growth reading for regime *clarity*, when they're not playing the same role anymore.

```
Momentum_Clarity = (|ΔGrowth| + |ΔInflation|) / 2   [scaled 0-100]

FCA_Alignment = +1 if FCA direction agrees with quadrant's typical directional bias, 
                 0 if neutral, 
                −1 if FCA contradicts the quadrant (early-warning case above)

Confidence (%) = min(99, 40 + 0.5 × Momentum_Clarity + 8 × FCA_Alignment)
```

A confident Goldilocks call requires strong, clear momentum in the right direction *and* financial conditions that aren't quietly deteriorating underneath. A contradiction (strong momentum, hostile FCA) caps confidence rather than being ignored — this is the "smells off" signal a good regime engine should surface, not suppress.

---

## 6. Composite Severity Score (keep, but reframe)

Keep your existing weighted composite exactly as-is:

```
Composite = 0.30(Growth) + 0.20(Inflation) + 0.15(Rates) + 0.10(Liquidity) + 0.15(Credit) + 0.10(Risk)
```

But it's no longer competing with the regime label — it's the **strength readout within whatever quadrant is active**. Display pattern:

> **Regime: Overheat (Late-cycle, Restrictive policy)**
> Composite Strength: 71 / 100
> Confidence: 82%
> FCA: +9 (neutral-to-supportive)

This mirrors how professional macro desks actually talk: "we're in an overheat regime, and it's a strong one" — two separate statements, not one number trying to do both jobs.

---

## 7. Persistence Filter (prevents whipsaw)

Regimes shouldn't flip on a single data print. Maintain two states:

```
Candidate_Regime = quadrant computed today
Confirmed_Regime = quadrant that has been the Candidate for ≥ N consecutive trading days (default N = 10)
```

Only `Confirmed_Regime` drives the headline label and any downstream asset-tilt logic. `Candidate_Regime` can be shown as a small "regime watch" indicator ("Currently trending toward Stagflation — 4/10 days") so you get early warning without acting on noise.

---

## 8. Full Pipeline Diagram

```
Raw Indicators (47 series)
        |
        v
Percentile-Rank Normalization → 6 Dimension Scores (0-100)
        |
        +---------------------------+---------------------------+
        |                           |                           |
        v                           v                           v
  Growth + Inflation          Rates (overlay)          Liquidity+Credit+Risk
  3-month deltas                    |                    (FCA formula)
        |                           |                           |
        v                           |                           |
  Quadrant Classification <---------+                           |
  (Goldilocks/Overheat/                                         |
   Slowdown/Stagflation)                                        |
        |                                                       |
        +-------------------------- Confidence <-----------------+
        |                       (momentum clarity + FCA alignment)
        v
  Persistence Filter (N-day confirmation)
        |
        v
  Confirmed Regime Label + Composite Severity Score + Asset Tilt
```

---

## 9. Asset Tilt Reference Table

| Regime | Rates Overlay | Favored | Avoid |
|---|---|---|---|
| Goldilocks | Either | Growth equities, small caps, high-yield credit | Cash, short duration |
| Goldilocks + falling FCA | — | Reduce risk despite quadrant; treat as early warning | Adding new risk-on exposure |
| Overheat, Accommodative | Accommodative | Commodities, value/cyclicals, TIPS | Long duration bonds |
| Overheat, Restrictive | Restrictive | Short-duration, quality cyclicals | Speculative growth, long duration |
| Slowdown | Either | Duration/bonds, quality defensives, USD | Cyclicals, small caps |
| Stagflation, Accommodative | Accommodative | Gold, commodities, TIPS | Long-duration growth equities |
| Stagflation, Restrictive | Restrictive | Cash, gold, short-duration | Everything duration- or growth-sensitive |

---

## 10. Migration Notes (v1 → v2)

- Keep all 6 dimension score calculations as-is — no changes needed upstream.
- Add: rolling 3-month delta calc for Growth_score and Inflation_score (new, small addition).
- Add: `Policy_Stance` boolean from DFII10 + real fed funds (new, small addition).
- Add: FCA formula (new, trivial — reuses existing Liquidity/Credit/Risk scores).
- Replace: the 5-rule AND-threshold classifier → quadrant + dead-band logic.
- Replace: Confidence formula.
- Keep: Composite Score formula unchanged, just reframed in the UI as "Strength" rather than competing with the regime label.
- Add: persistence filter state (Candidate vs Confirmed regime) — needs a small amount of state storage (last N days of candidate regime), everything else is stateless/computed on demand.
