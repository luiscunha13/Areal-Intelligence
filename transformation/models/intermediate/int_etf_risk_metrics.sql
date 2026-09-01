-- models/intermediate/int_etf_risk_metrics.sql
-- ─────────────────────────────────────────────────
-- Computes risk metrics for every ETF vs the SPY benchmark:
--   • Beta (1Y rolling, vs SPY daily log returns)
--   • Correlation (1Y rolling, vs SPY)
--   • Max Drawdown (1Y rolling, peak-to-trough)
--   • Sortino Ratio (1Y, downside deviation denominator)
--
-- Requires at least 252 trading days of price history per ticker.

with spy_returns as (
    select
        price_date,
        ln(adj_close_price / nullif(lag(adj_close_price, 1) over (order by price_date), 0)) as spy_log_ret
    from {{ ref('stg_prices') }}
    where ticker = 'SPY'
),

etf_returns as (
    select
        ticker,
        price_date,
        adj_close_price,
        -- Daily log return
        ln(adj_close_price / nullif(lag(adj_close_price, 1) over w, 0)) as etf_log_ret,
        -- Running max for drawdown calc (252-day window)
        max(adj_close_price) over (
            partition by ticker order by price_date
            rows between 251 preceding and current row
        ) as running_max_252
    from {{ ref('stg_prices') }}
    where ticker != 'SPY'
    window w as (partition by ticker order by price_date)
),

joined as (
    select
        e.ticker,
        e.price_date,
        e.adj_close_price,
        e.etf_log_ret,
        e.running_max_252,
        s.spy_log_ret,
        -- Drawdown from 252-day running max
        case
            when e.running_max_252 > 0
            then round(((e.adj_close_price - e.running_max_252) / e.running_max_252 * 100)::numeric, 4)
        end as drawdown_pct,
        -- Downside daily return (only negative log rets, zero otherwise) for Sortino
        case when e.etf_log_ret < 0 then e.etf_log_ret else 0 end as downside_ret
    from etf_returns e
    join spy_returns s on s.price_date = e.price_date
),

risk_calc as (
    select
        ticker,
        price_date,

        -- Max Drawdown 1Y: minimum drawdown_pct over the last 252 rows
        round(
            min(drawdown_pct) over (
                partition by ticker order by price_date
                rows between 251 preceding and current row
            )::numeric,
        4) as max_drawdown_1y,

        -- Beta: cov(etf, spy) / var(spy) over 252 days
        -- Using covar_pop and var_pop window functions
        case
            when var_pop(spy_log_ret) over (
                partition by ticker order by price_date
                rows between 251 preceding and current row
            ) > 0
            then round(
                (covar_pop(etf_log_ret, spy_log_ret) over (
                    partition by ticker order by price_date
                    rows between 251 preceding and current row
                ) /
                var_pop(spy_log_ret) over (
                    partition by ticker order by price_date
                    rows between 251 preceding and current row
                ))::numeric,
            4)
        end as beta_vs_spy,

        -- Correlation vs SPY over 252 days
        round(
            corr(etf_log_ret, spy_log_ret) over (
                partition by ticker order by price_date
                rows between 251 preceding and current row
            )::numeric,
        4) as corr_vs_spy,

        -- Sortino Ratio: annualised return / downside deviation
        -- Downside deviation = stddev of only negative daily returns × √252
        case
            when stddev_pop(downside_ret) over (
                partition by ticker order by price_date
                rows between 251 preceding and current row
            ) > 0
            then round(
                (
                    -- Annualised 12m return (simple)
                    (first_value(adj_close_price) over (
                        partition by ticker order by price_date desc
                        rows between current row and current row
                    ) / nullif(lag(adj_close_price, 252) over (
                        partition by ticker order by price_date
                    ), 0) - 1)
                    /
                    -- Annualised downside deviation
                    (stddev_pop(downside_ret) over (
                        partition by ticker order by price_date
                        rows between 251 preceding and current row
                    ) * sqrt(252))
                )::numeric,
            4)
        end as sortino_ratio

    from joined
)

select * from risk_calc
