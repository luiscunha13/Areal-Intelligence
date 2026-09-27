# Macro Engine Scores & Overview Technical Breakdown

**Generated Date**: August 16, 2026  
**Analysis Target Date**: August 14, 2026  
**Engine Version**: Macro Regime Engine v2.0 (with Sub-Dimension Divergence Diagnostics)

---

## 1. Dashboard Overview & Headline Results

The **Scores & Overview** module aggregates 47 macro time series into 6 normalized dimension scores, a Financial Conditions Amplifier (FCA), a Policy Stance overlay, and a composite macro score.

### Headline Summary Table

| Metric | Output Value | Description / Interpretation |
| :--- | :--- | :--- |
| **Market Regime** | **Slowdown (Restrictive policy)** | Growth decelerating with cooling inflation under restrictive interest rates |
| **Primary Quadrant** | **Slowdown** | $\Delta\text{Growth} \le -2.5$, $\Delta\text{Inflation} \ge +2.5$ |
| **Severity Level** | **Slowdown** | Growth level ($45.0$) remains above deep contraction threshold ($<35.0$) |
| **Policy Stance Overlay** | **Restrictive** | 10Y Real TIPS ($2.39\%$) $> 1.50\%$ historical restrictive cutoff |
| **Overall Composite Score** | **55.3 / 100** | Neutral-to-slight expansionary baseline score |
| **Signal Confidence** | **90.0%** *(Needs Recalibration)* | High clarity based on current momentum formula multiplier ($\times 4.0$) |
| **Financial Conditions (FCA)**| **+12.4 (Neutral)** | $0.35(\text{Liquidity}) + 0.35(\text{Credit}) + 0.30(\text{Risk}) - 50 = +12.4$ |

---

## 2. Dimensional Macro Scores & Raw Indicator Calculus

Each dimension score is bounded between $0.0$ and $100.0$, where $50.0$ represents baseline historical neutrality.

### Dimension 1: Growth Score ($45.0 / 100$)
**Calculus**: Arithmetic mean of normalized indicator percentiles and score penalties.

$$\text{Growth Score} = \frac{28.7 + 35.1 + 55.8 + 81.6 + 21.5 + 37.0 + 100.0 + 0.1}{8} = 45.0$$

| Indicator Name | Series ID | Observation Date | Raw Value | Transformation / Calculus | Component Score | Signal Group |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Real GDP | `GDPC1` | 2026-04-01 | $24,270.6$ B | 4-Qtr YoY: $+2.10\%$ $\rightarrow$ Percentile Rank | **28.7** | Coincident |
| Industrial Production | `INDPRO` | 2026-06-01 | $102.64$ | 12-Mo YoY: $+1.14\%$ $\rightarrow$ Percentile Rank | **35.1** | Coincident |
| Real Retail Sales | `RSAFS` | 2026-07-01 | $\$763,602$ M | 12-Mo YoY: $+5.01\%$ $\rightarrow$ Percentile Rank | **55.8** | Coincident |
| Unemployment Rate | `UNRATE` | 2026-07-01 | $4.10\%$ | Inverted Percentile ($100.0 - 18.4\%$) | **81.6** | Lagging / Calm |
| Nonfarm Payrolls | `PAYEMS` | 2026-07-01 | $158,858$ K | 12-Mo YoY: $+0.20\%$ $\rightarrow$ Percentile Rank | **21.5** | **Leading / Weak** |
| Building Permits | `PERMIT` | 2026-06-01 | $1,374$ K | 12-Mo YoY: $-1.79\%$ $\rightarrow$ Percentile Rank | **37.0** | Leading / Weak |
| Sahm Rule Indicator | `SAHMREALTIME` | 2026-07-01 | $-0.03\%$ | Penalty: $\max(0, 100 - (\text{raw}/0.5) \times 50)$ | **100.0** | Lagging / Calm |
| Michigan Sentiment | `UMCSENT` | 2026-06-01 | $49.50$ | Level Percentile Rank | **0.1** | **Leading / Severe** |

---

### Dimension 2: Inflation Score ($78.5 / 100$)
**Calculus**: Measures distance of inflation metrics from the Federal Reserve's $2.0\%$ target. Higher score = inflation cooling toward target.

$$\text{Inflation Score} = \frac{73.9 + 90.7 + 74.3 + 93.2 + 60.2}{5} = 78.5$$

| Indicator Name | Series ID | Observation Date | Raw Value | Metric / Formula | Component Score |
| :--- | :--- | :--- | :--- | :--- | :--- |
| CPI Inflation | `CPIAUCSL` | 2026-07-01 | $332.81$ | YoY $+3.30\%$ $\rightarrow$ $\max(0, 100 - |3.30\% - 2.0\%| \times 2000)$ | **73.9** |
| Core CPI Inflation | `CPILFESL` | 2026-07-01 | $336.79$ | YoY $+2.47\%$ $\rightarrow$ $\max(0, 100 - |2.47\% - 2.0\%| \times 2000)$ | **90.7** |
| Core PCE Inflation | `PCEPILFE` | 2026-06-01 | $130.27$ | YoY $+3.29\%$ $\rightarrow$ $\max(0, 100 - |3.29\% - 2.0\%| \times 2000)$ | **74.3** |
| 10Y Breakeven | `T10YIE` | 2026-08-14 | $2.27\%$ | Rate $2.27\%$ $\rightarrow$ $\max(0, 100 - |2.27\% - 2.0\%| \times 2500)$ | **93.2** |
| PPI Final Demand | `PPIFIS` | 2026-07-01 | $156.56$ | YoY $+4.66\%$ $\rightarrow$ $\max(0, 100 - |4.66\% - 2.0\%| \times 1500)$ | **60.2** |

---

### Dimension 3: Interest Rates Score ($21.2 / 100$)
**Calculus**: Arithmetic mean of yield curve slope percentile and inverted real yield percentile.

$$\text{Rates Score} = \frac{37.7 + 4.6}{2} = 21.2$$

| Indicator Name | Series ID | Observation Date | Raw Value | Transformation / Calculus | Component Score |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Yield Curve Spread | `DGS10 - DGS2` | 2026-08-14 | $+0.48\%$ ($48$ bps) | Spread Percentile Rank | **37.7** |
| 10Y TIPS Real Yield | `DFII10` | 2026-08-13 | $2.39\%$ | Inverted Percentile ($100.0 - 95.4\%$) | **4.6** |

---

### Dimension 4: Liquidity Score ($55.2 / 100$)
**Calculus**: Arithmetic mean of liquidity YoY percentiles and inverted financial condition indices.

$$\text{Liquidity Score} = \frac{29.0 + 33.7 + 68.2 + 90.1}{4} = 55.2$$

| Indicator Name | Series ID | Observation Date | Raw Value | Transformation / Calculus | Component Score | Sub-Category |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Fed Net Liquidity | `WALCL - WTREGEN - RRP` | 2026-08-14 | $\$5,795.76$ B | 52-Wk YoY: $-1.31\%$ $\rightarrow$ Percentile Rank | **29.0** | Monetary Plumbing (Tight) |
| M2 Money Supply | `M2SL` | 2026-06-01 | $\$23,155.20$ B | 12-Mo YoY: $+5.53\%$ $\rightarrow$ Percentile Rank | **33.7** | Money Supply (Tight) |
| Chicago Fed NFCI | `NFCI` | 2026-08-07 | $-0.5490$ | Inverted Percentile ($100.0 - 31.8\%$) | **68.2** | Market Stress (Calm) |
| St. Louis Fed Stress | `STLFSI4` | 2026-08-07 | $-0.7709$ | Inverted Percentile ($100.0 - 9.9\%$) | **90.1** | Market Stress (Calm) |

---

### Dimension 5: Credit Spreads Score ($91.1 / 100$)
**Calculus**: Inverted percentile rank of High Yield Option-Adjusted Spreads.

$$\text{Credit Score} = 100.0 - \text{PercentileRank}(\text{BAMLH0A0HYM2}) = 100.0 - 8.9\% = 91.1$$

| Indicator Name | Series ID | Observation Date | Raw Value | Transformation / Calculus | Component Score |
| :--- | :--- | :--- | :--- | :--- | :--- |
| High Yield OAS | `BAMLH0A0HYM2` | 2026-08-13 | $2.71\%$ ($271$ bps)| Inverted Percentile ($100.0 - 8.9\%$) | **91.1** |

---

### Dimension 6: Market Risk Score ($37.2 / 100$)
**Calculus**: Arithmetic mean of inverted VIX percentile and Copper/Gold ratio percentile.

$$\text{Risk Score} = \frac{70.7 + 3.6}{2} = 37.2$$

| Indicator Name | Series ID | Observation Date | Raw Value | Transformation / Calculus | Component Score | Sub-Category |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| CBOE VIX Index | `VIXCLS` | 2026-08-13 | $14.63$ | Inverted Percentile ($100.0 - 29.3\%$) | **70.7** | Equity Volatility (Calm) |
| Copper / Gold Ratio | `COPPER_GOLD` | 2026-06-01 | $81.79$ | Level Percentile Rank | **3.6** | Commodity Macro (Defensive) |

---

## 3. Step-by-Step Mathematical Calculations to Final Output

### Step A: Overall Composite Score
The Composite Score is a linear weighted sum of the 6 dimensions:

$$\text{Overall Score} = 0.30(\text{Growth}) + 0.20(\text{Inflation}) + 0.15(\text{Rates}) + 0.10(\text{Liquidity}) + 0.15(\text{Credit}) + 0.10(\text{Risk})$$

$$\text{Overall Score} = 0.30(45.0) + 0.20(78.5) + 0.15(21.2) + 0.10(55.2) + 0.15(91.1) + 0.10(37.2) = \mathbf{55.3}$$

---

### Step B: Financial Conditions Amplifier (FCA)
$$\text{FCA} = 0.35(\text{Liquidity}) + 0.35(\text{Credit}) + 0.30(\text{Risk}) - 50.0 = \mathbf{+12.4} \quad (\text{Neutral Status})$$

---

### Step C: Policy Stance Overlay
Evaluated using the 10-Year Real TIPS Yield (`DFII10`):

$$\text{Policy Stance} = \begin{cases} \text{Restrictive}, & \text{if } \text{DFII10} > 1.50\% \text{ or Rates Score} < 45.0 \\ \text{Accommodative}, & \text{otherwise} \end{cases}$$

Since $\text{DFII10} = 2.39\% > 1.50\%$, Policy Stance is **Restrictive**.

---

### Step D: Primary Macro Quadrant & Severity
Driven by 3-month trailing momentum deltas ($\Delta\text{Growth}$ and $\Delta\text{Inflation}$) relative to dead-band threshold $\epsilon = 2.5$:

* $\Delta\text{Growth} = 45.0 - 50.01 = \mathbf{-5.01}$ ($\le -2.5 \rightarrow \text{Decelerating}$)
* $\Delta\text{Inflation} = 78.5 - 50.05 = \mathbf{+28.45}$ ($\ge +2.5 \rightarrow \text{Cooling}$)

Quadrant Matrix lookup ($\Delta\text{Growth} < 0, \Delta\text{Inflation} > 0$) $\rightarrow$ **Slowdown**. Headline Label: **Slowdown (Restrictive policy)**.

---

## 4. Deep-Dive Review & Model Diagnostic Findings

### Finding 1: Cold-Start Fallback Bug Verification & Real Data Deltas
* **Verification**: We audited the database query logic in `pipeline.py`. When historical `MacroFeature` snapshots are not pre-generated for prior dates (e.g., May 2026), the query fallback returns `50.0` (neutral midpoint).
* **True Point-in-Time Calculation**: Calculating raw indicator history up to May 14, 2026 confirms the real May baseline was indeed **Growth = 50.0** and **Inflation = 50.0** due to initial synthetic historical seating in the test environment.
* **Impact**: While the direction of momentum ($\Delta\text{Growth} < 0$ and $\Delta\text{Inflation} > 0$) is mathematically verified, the absolute magnitude of $\Delta\text{Inflation} (+28.45)$ is inflated by the cold-start fallback.

---

### Finding 2: Model Calibration Issues & Recommended Fixes

1. **Confidence Formula Saturation**:
   - *Current Formula*: $\text{Clarity} = \min(100.0, (|\Delta\text{Growth}| + |\Delta\text{Inflation}|) \times 4.0)$.
   - *Issue*: Any combined delta $\ge 25.0$ saturates clarity to $100\%$, forcing Confidence into 3 discrete buckets ($82\%, 90\%, 98\%$).
   - *Fix*: Rescale multiplier to $\times 1.5$ or use $\text{Clarity} = \frac{|\Delta\text{Growth}| + |\Delta\text{Inflation}|}{2} \times 2.0$ to ensure smooth linear discrimination between weak and strong momentum signals.

2. **Policy Stance Redundancy**:
   - *Current Logic*: Checks `DFII10 > 1.5% OR Rates Score < 45.0`.
   - *Issue*: `Rates Score` already incorporates `DFII10`, creating internal circular dependency.
   - *Fix*: Replace with Real Fed Funds Rate vs Estimated Neutral Rate ($r^* \approx 0.75\%$): $\text{Real Fed Funds} = \text{FEDFUNDS} - \text{Core PCE YoY}$. If $\text{Real Fed Funds} > 1.25\%$, classify as Restrictive.

---

### Finding 3: Internal Sub-Dimension Divergences (What Averaging Hides)

1. **Labor Stall vs Unemployment Calm (Growth = 45.0)**:
   - `UNRATE` ($81.6$) and `SAHMREALTIME` ($100.0$) report robust labor stability.
   - `PAYEMS` ($21.5$) and `UMCSENT` ($0.1$) signal severe hiring contraction and consumer distress.
   - *Diagnosis*: Classic "low-churn, hiring freeze" labor market (no mass layoffs, but zero gross hiring).

2. **Liquidity Drain vs Financial Conditions Calm (Liquidity = 55.2)**:
   - Fed Net Liquidity ($29.0$) and M2 ($33.7$) indicate active balance sheet contraction.
   - NFCI ($68.2$) and Stress Index ($90.1$) indicate loose financial market conditions.
   - *Diagnosis*: Central bank liquidity drain occurring while secondary risk markets remain complacent.

3. **Volatility Calm vs Commodity Defensiveness (Risk = 37.2)**:
   - VIX ($70.7$) indicates low equity market volatility.
   - Copper/Gold ($3.6$) sits near multi-year lows, signalling deep global industrial weakness.
   - *Diagnosis*: Divergence between equity volatility complacency and physical economy safe-haven demand.

---

### Finding 4: Real-World Supply Shock Risk & Asset Recommendation Adjustment

* **Macro Context**: Recent July CPI inflation print ($3.4\%$ YoY) and elevated oil prices reflect supply-side pressures (e.g., Middle East/Iran geopolitical energy shocks) rather than demand expansion.
* **Duration Sensitivity Warning**: While standard Slowdown playbooks mandate **Overweight Long Duration**, supply-driven inflation shocks accompanied by hawkish Fed stance (live hike risks) can cause severe yield curve sell-offs.
* **Refined Asset Tilt Table**:

| Asset Category | Allocation Stance | Recommended Instruments | Avoided Instruments | Tactical Nuance / Warning |
| :--- | :--- | :--- | :--- | :--- |
| **Fixed Income** | **Neutral / Tactical Short Duration** | 2Y-5Y Treasuries, TIPS, Cash | Long-Duration Treasuries (20Y+) | **Caution on Long Duration**: Supply-shock inflation creates hawkish Fed rate hike risk |
| **Equities** | **Defensive Quality** | Healthcare, Consumer Staples, Utilities, High Free Cash Flow | Speculative Tech, Small-Caps, High-Beta | Focus on pricing power and defensive earnings balance sheets |
| **Commodities & Real Assets** | **Overweight** | Physical Gold, Energy, Broad Commodities | Long-Duration Equities | Effective hedge against supply-side geopolitical energy shocks |
| **Currencies & Cash** | **Overweight USD** | US Dollar (USD), Treasury Bills | Emerging Market FX | Safe-haven support under elevated real yields |
