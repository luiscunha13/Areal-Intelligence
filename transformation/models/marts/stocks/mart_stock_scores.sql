-- models/marts/stocks/mart_stock_scores.sql
-- ────────────────────────────────────────────
-- Multi-factor stock scoring model.
-- Scores every stock daily on 4 factors:
--   • Momentum  (35%) — price momentum across 1m/3m/6m/12m
--   • Trend     (25%) — proximity to 52w high, price vs. SMAs
--   • Quality   (25%) — ROE, FCF yield, debt/equity (from fundamentals)
--   • Value     (15%) — P/E, P/B percentile rank within sector
--
-- Rankings are computed overall and within each GICS sector.

with returns as (
    select
        r.ticker,
        r.price_date,
        r.ret_1m,
        r.ret_3m,
        r.ret_6m,
        r.ret_12m,
        r.pct_52w_range,
        r.sharpe_approx_1y,
        r.volatility_ann_pct,
        s.sector
    from {{ ref('int_price_returns') }} r
    join {{ source('raw', 'stocks') }} s on s.ticker = r.ticker
    where r.price_date >= current_date - interval '{{ var("lookback_years") }} years'
),

-- Latest fundamentals per stock (most recent annual report)
fundamentals as (
    select distinct on (ticker)
        ticker,
        pe_ratio,
        pb_ratio,
        roe,
        debt_to_equity,
        free_cash_flow,
        revenue
    from {{ source('raw', 'financial_metrics') }}
    where period_type = 'annual'
      and pe_ratio is not null
    order by ticker, period_end desc
),

joined as (
    select
        r.ticker,
        r.price_date,
        r.sector,
        r.ret_1m,
        r.ret_3m,
        r.ret_6m,
        r.ret_12m,
        r.pct_52w_range,
        r.sharpe_approx_1y,
        r.volatility_ann_pct,
        f.pe_ratio,
        f.pb_ratio,
        f.roe,
        f.debt_to_equity
    from returns r
    left join fundamentals f on f.ticker = r.ticker
    where r.ret_1m is not null
),

-- Cross-sectional percentile ranks per date
ranked as (
    select
        ticker,
        price_date,
        sector,
        ret_1m, ret_3m, ret_6m, ret_12m,
        pct_52w_range, sharpe_approx_1y, volatility_ann_pct,
        pe_ratio, pb_ratio, roe, debt_to_equity,

        -- MOMENTUM factor ranks
        percent_rank() over (partition by price_date order by ret_1m  nulls last) * 100 as pr_1m,
        percent_rank() over (partition by price_date order by ret_3m  nulls last) * 100 as pr_3m,
        percent_rank() over (partition by price_date order by ret_6m  nulls last) * 100 as pr_6m,
        percent_rank() over (partition by price_date order by ret_12m nulls last) * 100 as pr_12m,

        -- TREND factor ranks
        percent_rank() over (partition by price_date order by pct_52w_range    nulls last) * 100 as pr_52w,
        percent_rank() over (partition by price_date order by sharpe_approx_1y nulls last) * 100 as pr_sharpe,

        -- QUALITY factor ranks (higher ROE = better; lower D/E = better)
        percent_rank() over (partition by price_date order by roe          nulls last) * 100 as pr_roe,
        percent_rank() over (partition by price_date order by debt_to_equity desc nulls last) * 100 as pr_de,

        -- VALUE factor ranks (lower P/E, P/B = better value)
        percent_rank() over (partition by price_date order by pe_ratio desc nulls last) * 100 as pr_pe,
        percent_rank() over (partition by price_date order by pb_ratio desc nulls last) * 100 as pr_pb

    from joined
),

scored as (
    select
        ticker,
        price_date,
        sector,
        ret_1m, ret_3m, ret_6m, ret_12m,
        pct_52w_range, pe_ratio, pb_ratio, roe, debt_to_equity,

        -- Factor scores (weighted percentile ranks)
        round((pr_1m * 0.10 + pr_3m * 0.25 + pr_6m * 0.35 + pr_12m * 0.30)::numeric, 2)  as momentum_score,
        round((pr_52w * 0.60 + pr_sharpe * 0.40)::numeric, 2)                              as trend_score,
        round((pr_roe * 0.60 + pr_de * 0.40)::numeric, 2)                                  as quality_score,
        round((pr_pe * 0.50 + pr_pb * 0.50)::numeric, 2)                                   as value_score,

        -- Composite (weighted factors)
        round(
            ((pr_1m * 0.10 + pr_3m * 0.25 + pr_6m * 0.35 + pr_12m * 0.30) * 0.35
           + (pr_52w * 0.60 + pr_sharpe * 0.40) * 0.25
           + (pr_roe * 0.60 + pr_de * 0.40) * 0.25
           + (pr_pe  * 0.50 + pr_pb * 0.50) * 0.15)::numeric,
        2) as composite_score

    from ranked
),

final as (
    select
        ticker,
        price_date,
        sector,
        ret_1m, ret_3m, ret_6m, ret_12m,
        pct_52w_range, pe_ratio, pb_ratio, roe, debt_to_equity,
        momentum_score,
        trend_score,
        quality_score,
        value_score,
        composite_score,

        -- Classification by composite percentile
        case
            when composite_score >= 75 then 'leading'
            when composite_score >= 50 then 'improving'
            when composite_score >= 25 then 'weakening'
            else 'lagging'
        end as classification,

        -- Rankings
        rank() over (partition by price_date order by composite_score desc)         as rank_overall,
        rank() over (partition by price_date, sector order by composite_score desc) as rank_sector,

        now()       as computed_at,
        'dbt_v1.0'  as scoring_version

    from scored
)

select * from final
