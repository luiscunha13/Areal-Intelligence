-- models/marts/etfs/mart_etf_scores.sql
-- ────────────────────────────────────────
-- Multi-factor ETF scoring model.
-- Computes a composite score for every ETF on every date using:
--   • Momentum (1m, 3m, 6m, 12m) — weighted sum
--   • Risk-adjusted return (Sharpe approximation)
--   • Volatility penalty
--
-- Rankings are computed:
--   • Overall rank (across all ETFs)
--   • Category rank (within each category: sector, factor, etc.)
--
-- Weights sourced from scoring_weights.yaml (hardcoded here as SQL constants —
-- override by modifying this model when weights change).

with returns as (
    select
        ticker,
        price_date,
        etf_category,
        etf_sub_category,
        ret_1m,
        ret_3m,
        ret_6m,
        ret_12m,
        sharpe_approx_1y,
        volatility_ann_pct,
        pct_52w_range,
        high_52w,
        low_52w
    from {{ ref('int_price_returns') }}
    where price_date >= current_date - interval '{{ var("lookback_years") }} years'
),

-- Compute percentile ranks cross-sectionally per date (within each date, rank all ETFs)
cross_sectional as (
    select
        ticker,
        price_date,
        etf_category,
        etf_sub_category,
        ret_1m,
        ret_3m,
        ret_6m,
        ret_12m,
        sharpe_approx_1y,
        volatility_ann_pct,
        pct_52w_range,
        high_52w,
        low_52w,

        -- Percentile ranks (0-100) per date — used for normalization
        percent_rank() over (partition by price_date order by ret_1m  nulls last) * 100 as pct_rank_1m,
        percent_rank() over (partition by price_date order by ret_3m  nulls last) * 100 as pct_rank_3m,
        percent_rank() over (partition by price_date order by ret_6m  nulls last) * 100 as pct_rank_6m,
        percent_rank() over (partition by price_date order by ret_12m nulls last) * 100 as pct_rank_12m,
        percent_rank() over (partition by price_date order by sharpe_approx_1y nulls last) * 100 as pct_rank_sharpe,
        -- Volatility: LOWER is better → invert
        percent_rank() over (partition by price_date order by volatility_ann_pct desc nulls last) * 100 as pct_rank_vol

    from returns
    where ret_12m is not null  -- need at least 12m of data
),

scored as (
    select
        ticker,
        price_date,
        etf_category,
        etf_sub_category,
        ret_1m,
        ret_3m,
        ret_6m,
        ret_12m,
        sharpe_approx_1y,
        volatility_ann_pct,
        pct_52w_range,
        high_52w,
        low_52w,

        -- Composite score: weighted percentile ranks
        -- Weights: 1m=10%, 3m=20%, 6m=30%, 12m=25%, sharpe=10%, vol=5%
        round(
            pct_rank_1m   * 0.10
            + pct_rank_3m   * 0.20
            + pct_rank_6m   * 0.30
            + pct_rank_12m  * 0.25
            + pct_rank_sharpe * 0.10
            + pct_rank_vol  * 0.05,
        2) as composite_score,

        -- Classification thresholds
        case
            when (pct_rank_1m * 0.10 + pct_rank_3m * 0.20 + pct_rank_6m * 0.30
                  + pct_rank_12m * 0.25 + pct_rank_sharpe * 0.10 + pct_rank_vol * 0.05) >= 80
                then 'strong_buy'
            when (pct_rank_1m * 0.10 + pct_rank_3m * 0.20 + pct_rank_6m * 0.30
                  + pct_rank_12m * 0.25 + pct_rank_sharpe * 0.10 + pct_rank_vol * 0.05) >= 60
                then 'buy'
            when (pct_rank_1m * 0.10 + pct_rank_3m * 0.20 + pct_rank_6m * 0.30
                  + pct_rank_12m * 0.25 + pct_rank_sharpe * 0.10 + pct_rank_vol * 0.05) >= 40
                then 'neutral'
            when (pct_rank_1m * 0.10 + pct_rank_3m * 0.20 + pct_rank_6m * 0.30
                  + pct_rank_12m * 0.25 + pct_rank_sharpe * 0.10 + pct_rank_vol * 0.05) >= 20
                then 'underperform'
            else 'avoid'
        end as classification

    from cross_sectional
),

ranked as (
    select
        ticker,
        price_date,
        etf_category,
        etf_sub_category,
        ret_1m,
        ret_3m,
        ret_6m,
        ret_12m,
        sharpe_approx_1y,
        volatility_ann_pct,
        pct_52w_range,
        high_52w,
        low_52w,
        composite_score,
        classification,

        -- Overall rank (all ETFs on this date)
        rank() over (partition by price_date order by composite_score desc) as rank_overall,
        -- Category rank (e.g. within "sector" ETFs)
        rank() over (partition by price_date, etf_category order by composite_score desc) as rank_category,

        now()       as computed_at,
        'dbt_v1.0'  as scoring_version

    from scored
)

select * from ranked
