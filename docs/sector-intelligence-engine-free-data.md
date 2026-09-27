# Sector & Industry Intelligence Engine — Free-Data Edition

## 0. What changes from the paid-data version

Everything price-derived (RS-Ratio, RS-Momentum, Trend, Risk, Breadth, Trajectory) is **100% free either way** — it only ever needed OHLCV, which is free at daily granularity. The real changes are in the fundamentals layer:

| Factor | Paid version | Free version |
|---|---|---|
| Revision Breadth (4.1) | Continuous analyst up/down revision counts | **Replaced**: Earnings Surprise Momentum (is the sector beating estimates by a growing or shrinking margin, from free historical surprise data) |
| Forward EPS Growth (4.2) | Consensus forward 12M EPS growth | **Replaced**: Trailing (TTM) EPS growth from filed financials |
| Revenue/Margin Trend (4.3) | — | **Unchanged** — fully free either way |
| Capex Growth (4.4) | — | **Unchanged** — fully free either way |
| Valuation Percentile (4.5) | Forward P/E vs. own 5-10Y history | **Improved, actually**: TTM P/E vs. own history — buildable today with years of backfill, since forward-estimate history isn't available free at any price point but trailing financials are public record going back as far as EDGAR has filings |
| Thematic Concentration (4.6) | Manual + eventual NLP | **Unchanged**, plus a genuinely free automatable proxy (EDGAR full-text search for theme-keyword frequency in filings) |

---

## 1. Free Data Sources — Master Table

| Data need | Source | Cost | Notes |
|---|---|---|---|
| Daily OHLCV (all tickers) | Yahoo Finance via `yfinance` (Python) | Free | Unofficial API, widely used, adjusted close + dividends + splits included. Add a fallback. |
| Daily OHLCV (backup/redundancy) | Stooq (`stooq.com`) | Free | Plain CSV download per ticker, no key needed, good long history |
| S&P 500 constituent list + GICS sector/sub-industry | Wikipedia "List of S&P 500 companies" | Free | Maintained table, includes ticker, GICS sector, GICS sub-industry, date added. Scrape the table directly. |
| Sector/Industry ETF holdings (weights) | Issuer product pages: State Street SPDR, iShares (BlackRock), VanEck | Free | All three publish full daily holdings as downloadable CSV/XLSX on the fund's own page, no login. This is your real-time, ground-truth constituent weight source — better than deriving weights yourself. |
| Company financial statements (revenue, margins, capex, balance sheet) | SEC EDGAR — `companyfacts` API | Free, no key | Structured XBRL data for every US public filer. Needs a CIK lookup + tag mapping (Section 4). |
| Earnings surprise history | Finnhub free tier | Free (rate-limited) | Actual vs. estimate EPS per reported quarter, historical. This is your best free proxy for sentiment/estimate trend. |
| Analyst recommendation trend | Finnhub free tier | Free (rate-limited) | Monthly Strong Buy/Buy/Hold/Sell/Strong Sell counts — coarse, but a real signal direction over time. |
| Macro dimension scores | Your existing macro engine | Already have | No change |

---

## 2. Level 1 + Level 2 Universe — Concrete Tickers

**Level 1 (unchanged, 11 GICS Sector SPDRs):** XLK, XLE, XLV, XLF, XLI, XLRE, XLB, XLP, XLY, XLU, XLC

**Level 2 (Industry Groups) — real, liquid, established ETFs:**

| Industry | Ticker | Issuer |
|---|---|---|
| Semiconductors | `SMH` (or `SOXX`) | VanEck / iShares |
| Software & Services | `IGV` (or `XSW`, equal-weight) | iShares / SPDR |
| Biotechnology | `XBI` (equal-weight, or `IBB` cap-weight) | SPDR / iShares |
| Pharmaceuticals | `PPH` | VanEck |
| Health Care Equipment | `IHI` | iShares |
| Banks | `KBE` (equal-weight) | SPDR |
| Regional Banks | `KRE` (equal-weight) | SPDR |
| Insurance | `KIE` (equal-weight) | SPDR |
| Capital Markets / Asset Managers | `KCE` (equal-weight) | SPDR |
| Homebuilders | `XHB` (broader) or `ITB` (pure-play) | SPDR / iShares |
| Aerospace & Defense | `ITA` (or `PPA`) | iShares / Invesco |
| Transportation | `IYT` | iShares |
| Retail | `XRT` (equal-weight) | SPDR |
| Oil & Gas Exploration & Production | `XOP` (equal-weight) | SPDR |
| Oil & Gas Equipment & Services | `OIH` | VanEck |
| Metals & Mining | `XME` (equal-weight) | SPDR |

**No clean pure-play ETF exists for:** Technology Hardware, Internet (media/platforms), and sub-slices of REITs (data-center, residential). For these, build a custom cap-weighted basket directly from the GICS sub-industry constituent list (Wikipedia table + EDGAR for financials) rather than forcing a fund that doesn't cleanly represent the industry. One candidate worth checking is `XWEB` (SPDR S&P Internet) — I have lower confidence on its current liquidity/AUM than the others above, so verify it's still actively traded with reasonable volume before relying on it; if not, custom-basket it.

**Note on all of these**: confirm current AUM and average volume before building against any of them — ETF providers do occasionally close or merge smaller funds, and a fund that was liquid two years ago isn't guaranteed to be liquid today. This is a five-minute check per ticker on the issuer's own page, worth doing once at build time.

---

## 3. Price-Derived Factors — No Changes Needed

RS-Ratio, RS-Momentum, Trend, Risk, Breadth, and Trajectory (Sections 2 and 5 of the paid-version spec) are computed identically — they only ever needed OHLCV, which `yfinance`/Stooq provide free at daily resolution going back 10+ years for virtually every liquid US ticker. Pull once, cache locally, update daily. Nothing in this layer changes.

---

## 4. SEC EDGAR — How to Actually Pull Fundamentals for Free

This is the piece that needs real explanation since it's the least plug-and-play of the free sources.

**Step 1 — Get the CIK (SEC's internal company ID) for each ticker:**
```
GET https://www.sec.gov/files/company_tickers.json
```
Free, no key, returns the full ticker→CIK mapping for all filers. Cache this and refresh occasionally (new listings get added).

**Step 2 — Pull structured financials per company:**
```
GET https://data.sec.gov/api/xbrl/companyfacts/CIK{10-digit zero-padded CIK}.json
```
Returns every XBRL-tagged fact the company has ever filed, across all their 10-Ks and 10-Qs — revenue, margins, capex, debt, EPS, all of it, going back years.

**Required header** — SEC's fair-access policy requires a descriptive `User-Agent` identifying your app and a real contact email, e.g. `User-Agent: YourAppName contact@youremail.com`. Requests without this get blocked. Keep requests to a few per second with backoff — SEC's stated ceiling is 10 req/sec, but for a personal project staying well under that is both polite and safer against throttling.

**Key XBRL tags you'll actually use:**

| Line item | Common tag(s) |
|---|---|
| Revenue | `us-gaap:Revenues` or `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax` (varies by filer — check both) |
| Operating income | `us-gaap:OperatingIncomeLoss` |
| Diluted EPS | `us-gaap:EarningsPerShareDiluted` |
| Capex | `us-gaap:PaymentsToAcquirePropertyPlantAndEquipment` |
| Cash & equivalents | `us-gaap:CashAndCashEquivalentsAtCarryingValue` |
| Long-term debt | `us-gaap:LongTermDebtNoncurrent` + `us-gaap:LongTermDebtCurrent` |

Tag naming isn't perfectly standardized across filers (a handful of companies use slightly different tags for the same concept), so build your parser to check 2-3 known variants per line item and fall back gracefully. A couple of open-source Python libraries (e.g. `edgartools`) wrap this XBRL-parsing complexity for you — worth checking their current state on PyPI before deciding whether to use the raw API directly or a wrapper.

**This solves 4.3 (Revenue/Margin Trend) and 4.4 (Capex Growth) completely for free**, with no degradation from the paid version — these were always based on filed financials, not estimates.

---

## 5. Fundamentals Layer — Free Reformulation

### 4.1 (replacement) — Earnings Surprise Momentum
```
Surprise_i(q) = (Actual_EPS − Estimate_EPS) / |Estimate_EPS|     [per constituent, per quarter]
SurpriseMomentum_s = trend of cap-weighted average Surprise_i across the trailing 4 reported quarters
                     (is the beat margin widening, narrowing, or flipping to misses)
```
Pull the actual/estimate history from Finnhub's free earnings-surprise endpoint. This isn't the same signal as continuous revision breadth — it only updates quarterly, at each earnings report, rather than daily — but it's a legitimate, free, forward-relevant proxy for "is the market's view of this sector's execution improving."

### 4.2 (replacement) — Trailing EPS Growth
```
TrailingEPSGrowth_s = cap-weighted YoY growth in TTM diluted EPS (from EDGAR, Section 4)
```
A lagging indicator compared to forward consensus growth, but fully free and exact (it's realized, not estimated).

### 4.3 — Revenue Growth & Margin Trend
Unchanged from the paid spec — fully sourced from EDGAR (Section 4), no substitution needed.

### 4.4 — Capex Growth
Unchanged from the paid spec — fully sourced from EDGAR (Section 4), no substitution needed.

### 4.5 (improved) — Trailing Valuation Percentile
```
TTM_Multiple_s(t) = Price_s(t) / TTM_EPS_s(t)     [or EV/EBITDA using EDGAR balance sheet data]
ValuationPercentile_s(t) = PercentileRank(TTM_Multiple_s(t) within its own trailing 5-10Y history)
```
Because TTM EPS is realized, filed, public data going back as far as EDGAR's records extend, **you can reconstruct 5-10 years of this multiple's history immediately** by pulling historical price and historical filed EPS together — you don't have to wait and accumulate it going forward the way the forward-multiple version required. This is a genuine advantage of the free version, not just a fallback.

### 4.6 — Thematic Revenue Concentration
Same manual-curation starting point as the paid spec (segment disclosures for the handful of companies that break out Cloud/AI revenue). One additional free, automatable proxy worth adding: EDGAR's full-text search (`efts.sec.gov/LATEST/search-index`) lets you count how often a theme keyword ("artificial intelligence," "generative AI") appears in a company's 10-K/10-Q filings over time — a rough but genuinely free signal of how central a theme is becoming to a company's own disclosed business, and how that's trending year over year.

### Scoring — same principle as before
```
Fundamentals Growth-Quality Score (0-100) =
    0.30(SurpriseMomentum) + 0.25(TrailingEPSGrowth) + 0.25(RevenueGrowth & MarginTrend) + 0.20(CapexGrowth)
```
Valuation Percentile and Thematic Concentration stay excluded from the blend and shown as standalone context, same reasoning as the paid spec — "expensive" isn't inherently bad, so don't let it cancel out a genuine growth-quality read.

---

## 6. Practical Build Notes

- **`yfinance` is unofficial.** It scrapes Yahoo Finance rather than using a sanctioned API, which means it can break without warning if Yahoo changes their page structure. Keep Stooq as a fallback path so a single point of failure doesn't take down your whole price pipeline.
- **Finnhub's free tier is rate-limited** (calls per minute) — for a universe of ~500 constituents plus ~35 sector/industry aggregates, you'll want to batch and cache rather than pull live on every page load. Update earnings-surprise and recommendation data weekly, not real-time — it only changes at quarterly earnings anyway.
- **EDGAR rate limits are per-IP, not per-key** (there's no key) — build in request throttling and caching from day one so a full-universe refresh doesn't hammer the endpoint.
- **Sequencing**: get OHLCV + constituent lists + ETF holdings working first (this alone rebuilds 100% of the Technical Score and fixes the RS bug from before). Layer in EDGAR fundamentals second (unlocks 4.3, 4.4, 4.5 immediately with backfilled history). Add Finnhub surprise/recommendation data last, since it's the most rate-limited and least critical-path piece.
