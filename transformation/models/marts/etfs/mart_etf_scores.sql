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

risk as (
    select
        ticker,
        price_date,
        max_drawdown_1y,
        beta_vs_spy,
        corr_vs_spy,
        sortino_ratio
    from {{ ref('int_etf_risk_metrics') }}
    where price_date >= current_date - interval '{{ var("lookback_years") }} years'
),

-- Compute percentile ranks cross-sectionally per date (within each date, rank all ETFs)
cross_sectional as (
    select
        r.ticker,
        r.price_date,
        r.etf_category,
        r.etf_sub_category,
        r.ret_1m,
        r.ret_3m,
        r.ret_6m,
        r.ret_12m,
        r.sharpe_approx_1y,
        r.volatility_ann_pct,
        r.pct_52w_range,
        r.high_52w,
        r.low_52w,
        -- Risk metrics from int_etf_risk_metrics
        rk.max_drawdown_1y,
        rk.beta_vs_spy,
        rk.corr_vs_spy,
        rk.sortino_ratio,

        -- Percentile ranks (0-100) per date — used for normalization
        percent_rank() over (partition by r.price_date order by r.ret_1m  nulls last) * 100 as pct_rank_1m,
        percent_rank() over (partition by r.price_date order by r.ret_3m  nulls last) * 100 as pct_rank_3m,
        percent_rank() over (partition by r.price_date order by r.ret_6m  nulls last) * 100 as pct_rank_6m,
        percent_rank() over (partition by r.price_date order by r.ret_12m nulls last) * 100 as pct_rank_12m,
        percent_rank() over (partition by r.price_date order by r.sharpe_approx_1y nulls last) * 100 as pct_rank_sharpe,
        -- Volatility: LOWER is better → invert
        percent_rank() over (partition by r.price_date order by r.volatility_ann_pct desc nulls last) * 100 as pct_rank_vol

    from returns r
    left join risk rk on rk.ticker = r.ticker and rk.price_date = r.price_date
    where r.ret_1m is not null  -- need at least 1m of data
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
        -- Risk metrics
        max_drawdown_1y,
        beta_vs_spy,
        corr_vs_spy,
        sortino_ratio,

        -- Composite score: weighted percentile ranks with fallback coalescing
        -- Weights: 1m=10%, 3m=20%, 6m=30%, 12m=25%, sharpe=10%, vol=5%
        round(
            (coalesce(pct_rank_1m, 50.0) * 0.10
            + coalesce(pct_rank_3m, pct_rank_1m, 50.0) * 0.20
            + coalesce(pct_rank_6m, pct_rank_3m, pct_rank_1m, 50.0) * 0.30
            + coalesce(pct_rank_12m, pct_rank_6m, pct_rank_3m, pct_rank_1m, 50.0) * 0.25
            + coalesce(pct_rank_sharpe, pct_rank_1m, 50.0) * 0.10
            + coalesce(pct_rank_vol, 50.0) * 0.05)::numeric,
        2) as composite_score,

        -- Classification thresholds
        case
            when (coalesce(pct_rank_1m, 50.0) * 0.10 + coalesce(pct_rank_3m, pct_rank_1m, 50.0) * 0.20 + coalesce(pct_rank_6m, pct_rank_3m, pct_rank_1m, 50.0) * 0.30
                  + coalesce(pct_rank_12m, pct_rank_6m, pct_rank_3m, pct_rank_1m, 50.0) * 0.25 + coalesce(pct_rank_sharpe, pct_rank_1m, 50.0) * 0.10 + coalesce(pct_rank_vol, 50.0) * 0.05) >= 80
                then 'strong_buy'
            when (coalesce(pct_rank_1m, 50.0) * 0.10 + coalesce(pct_rank_3m, pct_rank_1m, 50.0) * 0.20 + coalesce(pct_rank_6m, pct_rank_3m, pct_rank_1m, 50.0) * 0.30
                  + coalesce(pct_rank_12m, pct_rank_6m, pct_rank_3m, pct_rank_1m, 50.0) * 0.25 + coalesce(pct_rank_sharpe, pct_rank_1m, 50.0) * 0.10 + coalesce(pct_rank_vol, 50.0) * 0.05) >= 60
                then 'buy'
            when (coalesce(pct_rank_1m, 50.0) * 0.10 + coalesce(pct_rank_3m, pct_rank_1m, 50.0) * 0.20 + coalesce(pct_rank_6m, pct_rank_3m, pct_rank_1m, 50.0) * 0.30
                  + coalesce(pct_rank_12m, pct_rank_6m, pct_rank_3m, pct_rank_1m, 50.0) * 0.25 + coalesce(pct_rank_sharpe, pct_rank_1m, 50.0) * 0.10 + coalesce(pct_rank_vol, 50.0) * 0.05) >= 40
                then 'neutral'
            when (coalesce(pct_rank_1m, 50.0) * 0.10 + coalesce(pct_rank_3m, pct_rank_1m, 50.0) * 0.20 + coalesce(pct_rank_6m, pct_rank_3m, pct_rank_1m, 50.0) * 0.30
                  + coalesce(pct_rank_12m, pct_rank_6m, pct_rank_3m, pct_rank_1m, 50.0) * 0.25 + coalesce(pct_rank_sharpe, pct_rank_1m, 50.0) * 0.10 + coalesce(pct_rank_vol, 50.0) * 0.05) >= 20
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
        -- Risk metrics
        max_drawdown_1y,
        beta_vs_spy,
        corr_vs_spy,
        sortino_ratio,
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
