# Economic Analysis Platform
## Complete Architecture, Data Model, Analytics & Analyst Intelligence Specification

**Document type:** Technical/Product Architecture Report  
**Scope:** Consolidated specification based on the original `company-data-model.md`, `enhancements2.txt`, and the subsequent architecture extensions.

---

# 1. Executive Summary

This document defines the target architecture for a comprehensive economic and equity-analysis platform.

The original design established a normalized company data layer, resilient ingestion, point-in-time financial integrity, derived fundamental analytics, relative valuation, ownership and insider data, embeddings, and a pre-indexed screener snapshot.

The extended design preserves that architecture and adds the main capabilities required for a more complete analyst workflow:

- Segment and geographic analysis
- Historical analyst estimates and revisions
- Earnings surprises
- Management guidance and revisions
- Capital allocation analysis
- Stock-based compensation and dilution
- Detailed debt structure
- Historical valuation context
- Historical market performance and risk
- Management analysis
- Competitive/business-model analysis
- Corporate catalysts and events
- Industry and macro context
- Data provenance
- Configurable scoring
- Investment-thesis generation

The strategic objective is therefore not simply to create a stock screener.

The target is a **structured company intelligence engine** capable of answering:

> What is this company, how is it performing, how does it compare with peers and its own history, what does the market expect, what is management communicating, what are the risks and catalysts, and why does the company deserve or not deserve investment attention?

---

# 2. Product Vision

## 2.1 From Screener to Company Intelligence Engine

The platform should evolve through several stages:

```text
Stock Screener
      ↓
Fundamental Analysis Platform
      ↓
Company Intelligence Platform
      ↓
Equity Research Platform
      ↓
AI Investment Research Platform

The screener is therefore an interface on top of a much larger data and analytics infrastructure.

A mature version should allow queries such as:

Find semiconductor companies with:


- improving FCF margins
- ROIC above industry median
- positive EPS estimate revisions
- valuation below their 5-year median
- strong insider buying
- manageable leverage

It should then explain why each company qualifies.

3. Core Design Principles
3.1 Single Source of Truth

There must be one normalized company data layer.

The screener, classification engine, analytics engine and scoring system should consume the same normalized data.

                 NORMALIZED DATA
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
    Screener       Analytics     Classification
        │              │              │
        └──────────────┼──────────────┘
                       ↓
                   Scoring

This prevents different components from calculating or sourcing the same concept differently.

3.2 API Resilience First

External free APIs should never be treated as operational databases.

The platform should cache raw payloads before parsing them.

External API
     ↓
Raw Cache
     ↓
Parser
     ↓
Validator
     ↓
Normalized Data

The cache protects against:

Rate limits
Temporary outages
Schema changes
Network failures
Repeated requests
Historical reproducibility problems
3.3 Point-in-Time Integrity

The platform must distinguish between:

Fiscal period

and:

Filing/publication date

Example:

Fiscal period: Q2 2026
Period end: 2026-06-30
Filing date: 2026-08-05

The system must not allow an analysis dated July 1 to use information that only became public on August 5.

This is essential for:

Backtesting
Historical screening
Factor research
Signal evaluation
Avoiding forward-looking data leakage
3.4 Historical Data Must Be Preserved

Do not overwrite historical values with today's values.

The platform should retain:

Financial history
Valuation history
Estimate history
Ownership history
Insider transactions
Filings
Guidance
Events
Embeddings

This makes it possible to answer:

What did the market know at that time?

and:

How did the investment thesis change?

3.5 Normalized Storage + Denormalized Serving

The normalized database is the source of truth.

The user-facing screener should use a materialized snapshot.

Normalized tables
       ↓
Nightly / scheduled analytics jobs
       ↓
company_snapshot
       ↓
Fast screener queries

This avoids expensive joins during every user request.

4. High-Level Architecture
                         EXTERNAL DATA
                              │
             ┌────────────────┼────────────────┐
             │                │                │
            SEC            Market           Other
           EDGAR          Providers         Sources
             │                │                │
             └────────────────┼────────────────┘
                              ↓
                    INGESTION / CACHE
                              ↓
                   NORMALIZED DATA LAYER
                              ↓
                    DERIVED ANALYTICS
                              ↓
             ┌────────────────┼────────────────┐
             │                │                │
          Valuation        Fundamentals      Market
             │                │                │
             └────────────────┼────────────────┘
                              ↓
                    CONTEXT / BENCHMARKS
                              ↓
                    SCORING & RANKING
                              ↓
             ┌────────────────┼────────────────┐
             │                │                │
         Screener        Research UI       AI Analyst
             │                │                │
             └────────────────┼────────────────┘
                              ↓
                     INVESTMENT THESIS
5. Data Source Strategy

The original design focuses on free data sources.

Primary sources include:

SEC EDGAR XBRL
SEC Form 4
yfinance
FINRA
Stooq where appropriate
Public company filings

The architecture should allow additional providers to be introduced later without changing the normalized schema.

This is important because free sources have limitations, particularly around:

Historical analyst estimates
Intraday market data
Options data
Complete consensus histories
Some qualitative datasets

The normalized layer should therefore abstract the source from the application.

6. Data Pipeline
6.1 Ingestion Layer

Responsibilities:

Identify required data.
Check internal cache.
Fetch external data only when necessary.
Store raw payload.
Validate payload.
Parse into normalized structures.
Record source metadata.
Detect schema/data anomalies.
6.2 Raw Cache

Example:

CREATE TABLE raw_data_cache (
    endpoint VARCHAR(100) NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    fetch_date DATE NOT NULL,
    raw_payload JSONB NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (endpoint, ticker, fetch_date)
);

The raw payload should not be discarded after parsing.

It provides:

Reprocessing capability
Debugging
Historical provenance
Recovery from parser bugs
Protection from external API changes
7. Core Company Data Model

The platform should organize data by how frequently it changes.

7.1 Company Identity
companies

Fields:

ticker
CIK
name
exchange
currency
country
HQ
GICS sector
GICS industry
SIC
IPO date
employee count
business description

The company table should contain slow-changing information.

8. Market Data
8.1 Daily Price Table
company_price_daily

Core fields:

Date
Open
High
Low
Close
Adjusted close
Volume
Market capitalization
Shares

Market cap can be derived from:

Price × Shares

where appropriate.

8.2 Derived Market Metrics

Add:

Performance
1D
1W
1M
3M
6M
YTD
1Y
3Y
5Y
Risk
Volatility
Downside volatility
Maximum drawdown
Sharpe
Sortino
Beta
Correlation to benchmark
Momentum
20D return
50D return
100D return
200D return
Distance from moving averages
Distance from 52-week high/low
Relative strength
Relative performance

Compare:

Company
vs S&P 500
vs Sector
vs Industry
9. Financial Statements
9.1 Income Statement

The normalized financial layer should contain:

Revenue
COGS
Gross profit
Operating expenses
R&D
SG&A
Operating income
Interest expense
Taxes
Net income
Diluted EPS
9.2 Balance Sheet

Include:

Cash
Short-term investments
Accounts receivable
Inventory
Accounts payable
Current assets
Current liabilities
PP&E
Goodwill
Intangibles
Short-term debt
Long-term debt
Total assets
Total liabilities
Shareholders' equity
9.3 Cash Flow

Include:

Operating cash flow
CapEx
Depreciation and amortization
Stock-based compensation
Dividends
Share repurchases
Acquisitions where identifiable
10. Fundamental Analytics

The platform should derive TTM and historical metrics.

Profitability
Gross margin
Operating margin
EBITDA margin
Net margin
ROE
ROA
ROIC
Cash Flow
FCF
FCF margin
FCF conversion
OCF / Net Income
Liquidity
Current ratio
Quick ratio
Leverage
Net debt
Debt / EBITDA
Net debt / EBITDA
Debt / Equity
Interest coverage
Working Capital
DSO
DIO
DPO
Cash conversion cycle
Financial Distress
Altman Z-score
Debt maturity risk
11. Cash Flow Quality

Free cash flow is a central quality anchor.

FCFF
FCFF = Operating Cash Flow - CapEx
FCF Margin
FCF Margin =
(Operating Cash Flow - CapEx) / Revenue
FCF Conversion
FCF Conversion =
(Operating Cash Flow - CapEx) / Net Income

Potential red flag:

Net income increasing
+
Operating cash flow declining

or persistently weak FCF conversion.

12. Capital Efficiency
ROIC
ROIC =
Operating Income × (1 - Effective Tax Rate)
/
(Short-Term Debt + Long-Term Debt + Equity - Cash)
Cash Conversion Cycle
CCC =
DSO + DIO - DPO

These metrics should be available both as absolute values and relative percentiles.

13. Segment-Level Financials

This is a major extension.

A consolidated company number is not always sufficient.

The platform should determine:

Which business is driving growth?

Add:

company_segments

Potential fields:

Segment name
Segment type
Revenue
Operating income
Assets
CapEx
Revenue growth
Operating margin
Contribution to company growth

Example:

Company
├── Cloud
│   ├── Revenue
│   ├── Growth
│   └── Margin
├── Advertising
│   ├── Revenue
│   ├── Growth
│   └── Margin
└── Hardware
    ├── Revenue
    ├── Growth
    └── Margin
14. Geographic Analysis

Add:

company_geography

Potential fields:

Geography
Revenue
Operating income
Revenue growth
Revenue share
Geographic concentration

This can expose:

Geographic concentration
Currency exposure
Regional growth
Regional deterioration
15. Valuation Engine
Core Multiples

Calculate:

P/E TTM
Forward P/E
P/S
P/B
EV/EBITDA
FCF yield
PEG
Relative Valuation

Compare with:

Sector median
Industry median
Market median

Examples:

Relative P/E =
Company P/E / Sector Median P/E
Relative P/S =
Company P/S / Sector Median P/S
16. Historical Valuation Context

Peer comparison is not enough.

The system should also compare a company against its own historical valuation.

For example:

Current P/E       = 31
5Y Median P/E     = 25
90th Percentile   = 33

This enables:

Historical valuation percentile
Historical P/E percentile
Historical EV/EBITDA percentile
Historical FCF yield percentile
Historical P/S percentile
Historical margin percentile
Historical growth percentile

This is one of the most useful additions for investment analysis.

17. Industry Benchmarking

Maintain:

industry_benchmarks

At:

Sector level
Industry level

Potential benchmark metrics:

Median P/E
Median forward P/E
Median P/S
Median P/B
Median EV/EBITDA
Median operating margin
Median FCF margin
Median ROIC
Median leverage

Also maintain:

Number of companies
Percentile distributions
Historical benchmark values
18. Analyst Estimates

Current snapshot estimates should include:

Forward EPS
Revenue growth
Earnings growth
Target price
Consensus rating

But the long-term model should also maintain estimate history.

19. Estimate Revision Engine

Create historical estimate observations.

Potential fields:

Estimate date
Fiscal period
EPS estimate
Revenue estimate
EBITDA estimate
Target price
Analyst count

Derive:

30-day revision
90-day revision
180-day revision
Upward revisions
Downward revisions
Estimate acceleration
Target-price revision
Estimate dispersion

This can become one of the most important forward-looking signals.

20. Earnings Surprise Engine

Store:

Actual EPS
Consensus EPS
EPS surprise
Actual revenue
Consensus revenue
Revenue surprise

Derive:

Beat rate
Miss rate
Average surprise
Surprise consistency
Consecutive beats
Surprise trend

A strong signal can be:

Revenue beat
+
EPS beat
+
Guidance raised
21. Management Guidance

Guidance should be stored independently.

Potential fields:

Metric
Period
Current low
Current high
Current midpoint
Previous low
Previous high
Previous midpoint
Filing date

Derived:

Guidance raised
Guidance lowered
Guidance maintained
Guidance midpoint change
Guidance trend
22. Ownership

Maintain:

company_ownership

Fields:

Institutional ownership
Insider ownership
Short interest
Date

Ownership should be treated as time-series data rather than a permanent company attribute.

23. Insider Transactions

Maintain:

company_insider_transactions

Fields:

Filer
Role
Transaction date
Filing date
Transaction type
Shares
Price
Total value

Derived signals:

Net insider buying
Net insider selling
Insider buying intensity
Number of buyers
Number of sellers
Recent insider activity
Insider activity relative to historical baseline

Insider activity should be interpreted carefully because not every sale has the same informational meaning as an open-market purchase.

24. Capital Allocation

The platform should analyze how management deploys generated cash.

Track:

FCF
 ├── CapEx
 ├── Acquisitions
 ├── Buybacks
 ├── Dividends
 ├── Debt repayment
 └── Cash accumulation

Derived metrics:

Dividend yield
Dividend growth
Payout ratio
Buyback yield
Net buyback yield
Total shareholder yield
CapEx / Revenue
R&D / Revenue
Acquisition spending
Debt repayment
Cash accumulation
25. Stock-Based Compensation and Dilution

Explicitly track:

Basic shares
Diluted shares
Shares outstanding
Share count growth
Share count reduction
SBC
SBC / Revenue
SBC / FCF
SBC / Net Income

This is particularly important for technology companies.

The platform should distinguish:

EPS growth caused by business performance

from:

EPS growth amplified by share count reduction
26. Debt Structure

The basic leverage model should be expanded later into instrument-level debt.

Potential fields:

Debt instrument
Principal
Maturity date
Interest rate
Fixed/floating
Currency
Filing date

Derived:

Debt maturity wall
Near-term refinancing risk
Fixed/floating exposure
Average debt cost
Debt concentration
27. Business Model and Competitive Analysis

The qualitative layer should use company filings and embeddings.

Existing semantic inputs:

10-K Item 1
10-K Item 1A
8-K material events

Add structured classifications such as:

Subscription exposure
Recurring revenue
Transaction revenue
Advertising
Marketplace
Hardware
Services
Licensing
Consumption-based revenue

Competitive features may include:

Market share
Switching costs
Network effects
Brand strength
IP
Cost advantages
Regulatory barriers
Competitive intensity

These fields can be extracted or classified automatically where reliable.

28. Embeddings and Semantic Intelligence

Maintain versioned embeddings.

company_embeddings

Store:

Company
Filing date
Source section
Embedding vector
Model/version

Important source sections:

Item 1     → Business
Item 1A    → Risk Factors

Potential applications:

Semantic peer discovery
Business-model similarity
Risk similarity
Business-model pivot detection
Change detection over time
Similar-company discovery

Embeddings should never replace structured financial features.

They should complement them.

29. Management Intelligence

Potential future management layer:

CEO
CFO
Tenure
Insider ownership
Compensation
Guidance accuracy
ROIC trajectory
Capital allocation track record
Acquisition history
Shareholder dilution

Potential management score:

Capital allocation
+
Guidance accuracy
+
ROIC trajectory
+
Insider alignment
+
Dilution discipline
+
Acquisition quality

This should be a later-stage feature because several components require reliable qualitative extraction.

30. Corporate Events

Create a unified event system.

Event categories:

Earnings
Guidance
Dividend
Buyback
Acquisition
Divestiture
Product launch
Regulatory decision
Lawsuit
CEO change
CFO change
Credit rating
Capital raise
Debt issue

Each event should contain:

Event date
Announcement date
Source
Event type
Description
Company impact classification
Optional structured values
31. Catalyst Engine

The event layer should eventually support:

What can move this company over the next 30/60/90 days?

Examples:

Earnings
Product launches
Regulatory decisions
M&A
Buybacks
Debt refinancing
Major contract announcements
Management changes

This turns static analysis into forward-looking research.

32. Risk Engine

Risk should combine quantitative and qualitative information.

Quantitative
Leverage
Interest coverage
Altman Z
Volatility
Drawdown
Customer concentration
Supplier concentration
Geographic concentration
Qualitative
Regulatory risk
Competitive risk
Technology risk
Litigation
Business-model risk
Macro sensitivity

The result should be an interpretable risk profile rather than one opaque number.

33. Macro and Industry Context

Later-stage data should connect companies to their broader environment.

Industry
Industry growth
Industry margins
Industry valuation
Cyclicality
Commodity exposure
Competitive intensity
Macro
Interest rates
Inflation
GDP
Employment
Commodity prices
Oil
Copper
Natural gas
FX
Yield curve

The platform should eventually identify relationships such as:

Company
   ↓
Industry
   ↓
Macro drivers
34. Technical / Market Context

Technical metrics should be an additional context layer.

Potential metrics:

Moving averages
RSI
Momentum
Volatility
52-week positioning
Relative strength
Drawdown

Do not make technical analysis the foundation of the platform.

Its purpose is to complement fundamental analysis.

35. Options Data — Future Layer

Potential future data:

Implied volatility
IV percentile
Put/call ratio
Open interest
Options volume
Skew
Expected move

This is lower priority than:

Financials
Estimates
Guidance
Segments
Valuation
Capital allocation
36. Data Provenance

Every important data point should eventually have:

value
source
source_document
period_end
fiscal_period
filing_date
reported_date
retrieved_date

This should be treated as a first-class architectural concern.

It allows:

Auditability
Debugging
Reproducibility
Historical research
Backtesting
Trust
37. Data Quality Layer

A mature ingestion pipeline should validate:

Financial consistency

Examples:

Assets ≈ Liabilities + Equity
FCF = OCF - CapEx
Temporal consistency
Filing date must not precede period end incorrectly
Future data must not appear in historical snapshots
Source consistency
Multiple source values should be compared where possible
Unexpected changes should trigger warnings
Missing data

Missing values should remain explicit.

Do not silently replace unavailable financial data with zero.

38. Derived Analytics Layer

The derived layer should contain calculations that can be reproduced from normalized data.

Examples:

company_metrics_ttm
company_valuation_daily
industry_benchmarks
company_percentiles_daily

Derived values should not become the source of truth.

The normalized data remains authoritative.

39. Percentile Engine

Percentiles should exist at multiple levels.

Market-relative

Company vs entire investable universe.

Sector-relative

Company vs sector.

Industry-relative

Company vs industry.

Company-history-relative

Company vs its own historical distribution.

This creates a much richer context than raw values.

40. Scoring Engine

The initial four-pillar framework:

QUALITY       35%
VALUATION     30%
GROWTH        20%
RISK          15%
Quality
ROIC
FCF conversion
Operating margin
Accrual quality
Valuation
Relative P/E
Relative EV/EBITDA
FCF yield
PEG
Growth
Revenue CAGR
EPS CAGR
Forward growth
Risk
Altman Z
Net debt / EBITDA
Interest coverage
Customer concentration
41. Configurable Scoring

The default score should not be the only score.

Users should eventually be able to define:

Value investor
Growth investor
Quality investor
Dividend investor
Low-risk investor
Custom strategy

Users should be able to:

Change weights
Enable/disable factors
Change universes
Change benchmark groups
Save profiles
42. Explainable Scores

Never expose only:

Score = 84

Instead:

Composite: 84


Quality:       93
Growth:        79
Valuation:     61
Risk:          96
Momentum:      74

Then show the drivers.

Example:

Positive:
+ ROIC improving
+ FCF growth accelerating
+ EPS estimates rising
+ Net debt declining


Negative:
- Valuation above historical median
- Gross margin declining

The platform should make every score explainable.

43. Company Snapshot

The user-facing screener should consume:

company_snapshot

This should contain the latest relevant values:

Company identity
Market data
Valuation
Fundamental metrics
Estimates
Ownership
Risk
Scores
Key concentration metrics

It should be:

Flat
Indexed
Fast to query
Rebuilt by scheduled jobs
44. Suggested Indexing Strategy

Important indexes include:

ticker
sector
industry
market_cap
PE
forward_PE
relative_PE
ROIC
FCF_margin
quality_score
growth_score
valuation_score
risk_score

Additional indexes should be introduced based on actual query patterns.

Do not over-index every field.

45. AI / Analyst Interface

The AI layer should sit above structured and unstructured data.

Example questions:

Why did this company score highly?


What changed in the last 90 days?


Why is the stock expensive?


Is the company's cash flow improving?


What are the biggest risks?


Which segment is driving growth?


Are analyst estimates improving?


Is management raising guidance?


How does the company compare with competitors?


What would invalidate the investment thesis?

The AI should retrieve structured facts and source documents rather than inventing conclusions.

46. Investment Thesis Engine

The final research layer should generate a structured thesis.

Example:

Investment Profile
Quality:        91
Growth:         74
Valuation:      62
Financial Risk: 95
Momentum:       68
Positive Factors
ROIC improving
FCF growth accelerating
EPS estimates revised upward
Debt declining
Negative Factors
Valuation above historical median
Margin pressure
Concentration risk
Catalysts
Upcoming earnings
Product launch
Buyback
Risks
Regulation
Competition
Margin compression
Geographic exposure

The system should always connect conclusions to measurable evidence.

47. Target Data Architecture

A mature database should conceptually contain:

companies


company_price_daily


company_financials_quarterly


company_segments


company_geography


company_valuation_daily


company_historical_percentiles


company_estimates


company_estimate_history


company_earnings


company_guidance


company_ownership


company_insider_transactions


company_capital_allocation


company_debt


company_events


company_metrics_ttm


company_market_metrics


company_risk_metrics


industry_benchmarks


company_percentiles_daily


company_embeddings


company_snapshot


company_scores

Not every table needs to be implemented immediately.

The model should grow incrementally.

48. Build Priorities
Phase 1 — Resilient Foundation

Implement:

Raw cache
Company identity
Price data
Market cap
Sector
Basic screener

Outcome:

Functional company screener.

Phase 2 — Fundamental Engine

Implement:

SEC XBRL ingestion
Income statement
Balance sheet
Cash flow
TTM calculations
FCF
ROIC
Margins
Leverage
Quality metrics

Outcome:

Fundamental analysis screener.

Phase 3 — Valuation and Relative Context

Implement:

Forward estimates
Valuation multiples
Industry benchmarks
Sector-relative metrics
Historical valuation accumulation
Percentiles

Outcome:

Relative valuation and historical valuation analysis.

Phase 4 — Ownership and Scoring

Implement:

Institutional ownership
Insider ownership
Form 4
Insider signals
Four-pillar score
Configurable scoring architecture
Materialized snapshot

Outcome:

Ranking and stock-selection engine.

Phase 5 — Analyst Context

Implement:

Segment data
Geographic data
Earnings surprises
Guidance
Capital allocation
SBC/dilution
Detailed debt
Historical estimate revisions where available

Outcome:

Analyst-grade company analysis.

Phase 6 — Qualitative Intelligence

Implement:

Business model classification
Risk-factor embeddings
Business embeddings
Competitive analysis
Management analysis
Semantic peer discovery
Business-model change detection

Outcome:

Company intelligence engine.

Phase 7 — Events and Context

Implement:

Corporate event engine
Catalyst engine
Industry data
Macro context
Market regime context

Outcome:

Forward-looking research platform.

Phase 8 — AI Research Interface

Implement:

Natural-language queries
Company explanations
Comparative research
Investment thesis generation
Risk analysis
Change detection
Source-linked answers

Outcome:

AI-assisted equity research platform.

49. Priority Matrix
Capability	Importance	Implementation Priority
Financial statements	Critical	Immediate
Price data	Critical	Immediate
Valuation	Critical	Immediate
FCF / ROIC	Critical	Immediate
Peer benchmarks	High	Early
Point-in-time integrity	Critical	Immediate
Segment data	Very high	High
Earnings surprises	Very high	High
Guidance	Very high	High
Estimate revisions	Very high	High
Capital allocation	High	High
SBC / dilution	High	High
Historical valuation	Very high	High
Insider transactions	High	Medium
Management analysis	Medium	Later
Competitive analysis	High	Later
Events	High	Medium
Macro	Medium	Later
Options	Low/medium	Later
News sentiment	Medium	Later
Alternative data	Low initially	Later
50. What the Final Platform Should Be Able to Answer

A complete platform should answer five categories of questions.

50.1 What is the company?
What does it do?
What are its segments?
Where does revenue come from?
Who are its customers?
What are its major risks?
What is its business model?
50.2 How is the company performing?
Is revenue growing?
Are margins expanding?
Is ROIC improving?
Is FCF growing?
Is leverage improving?
Is dilution occurring?
50.3 How does the company compare?
Is it cheaper than peers?
Is it more profitable?
Is growth superior?
Is leverage lower?
Is its valuation high relative to history?
50.4 What does the market expect?
What are analyst estimates?
Are estimates rising?
Has the company been beating expectations?
Is guidance improving?
What is the target price?
What is implied by the valuation?
50.5 What could happen next?
Upcoming earnings
Guidance
Product events
Regulatory decisions
M&A
Macro exposure
Industry changes
Key risks
Catalysts
51. Final Strategic Assessment

The architecture should not become an enormous database containing every possible metric simply because the metric exists.

Every data point should have a purpose.

The most valuable relationship is:

Historical performance
        ↓
Current fundamentals
        ↓
Market valuation
        ↓
Analyst expectations
        ↓
Management guidance
        ↓
Business / competitive context
        ↓
Catalysts and risks
        ↓
Investment thesis

This creates an analytical chain rather than a collection of disconnected statistics.

52. Final Product Definition

The target product can be summarized as:

A normalized, point-in-time, company intelligence platform that combines financial statements, market data, valuation, expectations, ownership, business information, events and contextual data to provide explainable company analysis, screening, ranking and AI-assisted investment research.

The core architecture should remain:

External Sources
      ↓
Raw Cache
      ↓
Normalized Data
      ↓
Derived Metrics
      ↓
Historical Context
      ↓
Peer Comparison
      ↓
Scoring
      ↓
Signals
      ↓
Research Interface
      ↓
AI Analyst

The screener is therefore only the first visible application.

The underlying data model becomes the foundation for:

Quantitative stock selection
Fundamental research
Factor research
Historical backtesting
Company classification
Peer discovery
Risk analysis
Catalyst identification
Investment-thesis generation
AI-assisted equity research
53. Final Recommended Principle

The platform should optimize for:

Data integrity > breadth

Historical context > isolated metrics

Explainability > opaque scores

Normalized source of truth > duplicated pipelines

Point-in-time correctness > convenience

Analytical relationships > raw data volume

The objective is not to collect every available data point.

The objective is to build a system where the collected data can reliably answer the questions an analyst actually asks.
