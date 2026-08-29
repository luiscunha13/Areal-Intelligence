-- models/intermediate/int_price_returns.sql
-- ────────────────────────────────────────────
-- Computes return metrics for every ticker:
--   • 1d / 1m / 3m / 6m / 12m price returns (using adj_close)
--   • 20-day rolling volatility (annualised)
--   • 20-day rolling Sharpe approximation (excess return / volatility)
--   • Distance from 52-week high / low
--
-- Used downstream by ETF scoring and sector RRG.

with base as (
    select
        ticker,
        price_date,
        adj_close_price,
        etf_category,
        etf_sub_category
    from {{ ref('stg_prices') }}
),

lagged as (
    select
        ticker,
        price_date,
        adj_close_price,
        etf_category,
        etf_sub_category,

        -- Lagged prices for return calculation
        lag(adj_close_price, 1)  over w as price_1d_ago,
        lag(adj_close_price, 21) over w as price_1m_ago,
        lag(adj_close_price, 63) over w as price_3m_ago,
        lag(adj_close_price, 126) over w as price_6m_ago,
        lag(adj_close_price, 252) over w as price_12m_ago,

        -- Daily log return for vol calculation
        ln(adj_close_price / nullif(lag(adj_close_price, 1) over w, 0)) as log_ret_1d,

        -- 52-week range
        max(adj_close_price) over (partition by ticker order by price_date rows between 251 preceding and current row) as high_52w,
        min(adj_close_price) over (partition by ticker order by price_date rows between 251 preceding and current row) as low_52w

    from base
    window w as (partition by ticker order by price_date)
),

vol_calc as (
    select
        ticker,
        price_date,
        adj_close_price,
        etf_category,
        etf_sub_category,
        price_1d_ago,
        price_1m_ago,
        price_3m_ago,
        price_6m_ago,
        price_12m_ago,
        log_ret_1d,
        high_52w,
        low_52w,

        -- 20-day rolling daily volatility → annualise (×√252)
        stddev(log_ret_1d) over (
            partition by ticker order by price_date
            rows between 19 preceding and current row
        ) * sqrt(252) as volatility_20d_ann

    from lagged
),

returns as (
    select
        ticker,
        price_date,
        adj_close_price,
        etf_category,
        etf_sub_category,

        -- Returns
        case when price_1d_ago  > 0 then round(((adj_close_price - price_1d_ago)  / price_1d_ago  * 100)::numeric, 4) end as ret_1d,
        case when price_1m_ago  > 0 then round(((adj_close_price - price_1m_ago)  / price_1m_ago  * 100)::numeric, 4) end as ret_1m,
        case when price_3m_ago  > 0 then round(((adj_close_price - price_3m_ago)  / price_3m_ago  * 100)::numeric, 4) end as ret_3m,
        case when price_6m_ago  > 0 then round(((adj_close_price - price_6m_ago)  / price_6m_ago  * 100)::numeric, 4) end as ret_6m,
        case when price_12m_ago > 0 then round(((adj_close_price - price_12m_ago) / price_12m_ago * 100)::numeric, 4) end as ret_12m,

        -- Volatility (annualised)
        round((volatility_20d_ann * 100)::numeric, 4) as volatility_ann_pct,

        -- Simplified Sharpe: ret_12m / volatility (not risk-free adjusted — good enough for ranking)
        case
            when volatility_20d_ann > 0 and price_12m_ago > 0
            then round(
                (((adj_close_price - price_12m_ago) / price_12m_ago) / volatility_20d_ann)::numeric,
                4
            )
        end as sharpe_approx_1y,

        -- 52-week position (0 = at low, 1 = at high)
        case
            when high_52w > low_52w
            then round(((adj_close_price - low_52w) / (high_52w - low_52w))::numeric, 4)
        end as pct_52w_range,

        round(high_52w::numeric, 4) as high_52w,
        round(low_52w::numeric, 4) as low_52w,

        now() as computed_at

    from vol_calc
)

select * from returns
