-- models/marts/sectors/mart_sector_scores.sql
-- ─────────────────────────────────────────────
-- Relative Rotation Graph (RRG) scoring for GICS sector ETFs.
-- Computes dual-horizon RS-Ratio and RS-Momentum vs SPY benchmark.
--
-- RS-Ratio  = relative strength level (is this sector outperforming SPY?)
-- RS-Momentum = rate of change of RS-Ratio (is outperformance accelerating?)
--
-- Horizons:
--   tactical_50d  — 50-day lookback (short-term rotation signals)
--   strategic_260d — 260-day lookback (secular trend positioning)
--
-- RRG Quadrants:
--   RS-Ratio > 100, RS-Momentum > 100 → LEADING   (outperforming + accelerating)
--   RS-Ratio < 100, RS-Momentum > 100 → IMPROVING  (underperforming but turning up)
--   RS-Ratio > 100, RS-Momentum < 100 → WEAKENING  (outperforming but decelerating)
--   RS-Ratio < 100, RS-Momentum < 100 → LAGGING    (underperforming + decelerating)

with sector_prices as (
    select ticker, price_date, adj_close_price
    from {{ ref('stg_prices') }}
    where ticker != 'SPY'
),

spy as (
    select price_date, adj_close_price as spy_close
    from {{ ref('stg_prices') }}
    where ticker = 'SPY'
),

-- Relative price = sector / SPY (normalized to 100 at start of window)
relative as (
    select
        s.ticker,
        s.price_date,
        s.adj_close_price,
        b.spy_close,
        s.adj_close_price / nullif(b.spy_close, 0) * 100 as relative_price
    from sector_prices s
    join spy b on b.price_date = s.price_date
),

-- Compute RS-Ratio and RS-Momentum for both horizons using rolling SMA
rrg_features as (
    select
        ticker,
        price_date,
        relative_price,

        -- Row number per ticker (used to enforce warmup period below)
        row_number() over (
            partition by ticker order by price_date
        ) as rn,

        -- Tactical (50d) horizon: 10-day SMA over 50-day SMA
        avg(relative_price) over (
            partition by ticker order by price_date
            rows between 49 preceding and current row
        ) as rp_sma_50,
        avg(relative_price) over (
            partition by ticker order by price_date
            rows between 9 preceding and current row
        ) as rp_sma_10,

        -- Strategic (260d) horizon: 50-day SMA over 260-day SMA
        avg(relative_price) over (
            partition by ticker order by price_date
            rows between 259 preceding and current row
        ) as rp_sma_260,
        avg(relative_price) over (
            partition by ticker order by price_date
            rows between 49 preceding and current row
        ) as rp_sma_50_strategic

    from relative
),

-- RS-Ratio = current relative price / its SMA (normalized to 100)
-- RS-Momentum = short SMA / long SMA of relative price (normalized to 100)
rs_calculated as (
    select
        ticker,
        price_date,
        rn,

        -- Tactical 50d (50-day baseline, 10-day momentum) — only valid after 50-row warmup
        case when rp_sma_50  > 0 and rn >= 50  then round(relative_price / rp_sma_50  * 100, 4) end as rs_ratio_tactical,
        case when rp_sma_50  > 0 and rn >= 50  then round(rp_sma_10     / rp_sma_50   * 100, 4) end as rs_momentum_tactical,

        -- Strategic 260d (260-day baseline, 50-day momentum) — only valid after 260-row warmup
        case when rp_sma_260 > 0 and rn >= 260 then round(relative_price / rp_sma_260 * 100, 4) end as rs_ratio_strategic,
        case when rp_sma_260 > 0 and rn >= 260 then round(rp_sma_50_strategic / rp_sma_260 * 100, 4) end as rs_momentum_strategic

    from rrg_features
),

-- Pivot to long format: one row per (ticker, date, horizon)
long_format as (
    select ticker, price_date, 'tactical_50d'   as horizon,
           rs_ratio_tactical   as rs_ratio,
           rs_momentum_tactical as rs_momentum
    from rs_calculated
    where rs_ratio_tactical is not null

    union all

    select ticker, price_date, 'strategic_260d' as horizon,
           rs_ratio_strategic,
           rs_momentum_strategic
    from rs_calculated
    where rs_ratio_strategic is not null
),

classified as (
    select
        ticker,
        price_date,
        horizon,
        rs_ratio,
        rs_momentum,

        -- RRG Quadrant
        case
            when rs_ratio >= 100 and rs_momentum >= 100 then 'leading'
            when rs_ratio <  100 and rs_momentum >= 100 then 'improving'
            when rs_ratio >= 100 and rs_momentum <  100 then 'weakening'
            when rs_ratio <  100 and rs_momentum <  100 then 'lagging'
        end as rrg_quadrant,

        -- Composite score: normalize RS-Ratio + RS-Momentum distance from 100
        round(
            (rs_ratio - 100) * 0.5 + (rs_momentum - 100) * 0.5,
        4) as composite_score

    from long_format
),

ranked as (
    select
        ticker,
        price_date,
        horizon,
        rs_ratio,
        rs_momentum,
        rrg_quadrant,
        composite_score,

        rank() over (
            partition by price_date, horizon
            order by composite_score desc
        ) as rank,

        now()       as computed_at,
        'dbt_v1.0'  as scoring_version

    from classified
)

select * from ranked
