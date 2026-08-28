-- models/intermediate/int_macro_features.sql
-- ────────────────────────────────────────────
-- Computes analytical features for every macro series:
--   • MoM 1m / 3m change (momentum)
--   • YoY change
--   • 2-year rolling z-score
--   • 5-year rolling z-score
--   • Trend label (rising / falling / stable)
--
-- These are the inputs consumed by the regime scoring engine.

with base as (
    select
        series_id,
        obs_date,
        obs_value
    from {{ ref('stg_macro_observations') }}
),

lagged as (
    select
        series_id,
        obs_date,
        obs_value,

        -- Lag values for momentum / YoY calculations
        lag(obs_value, 1)  over w as val_lag_1m,
        lag(obs_value, 3)  over w as val_lag_3m,
        lag(obs_value, 12) over w as val_lag_12m,

        -- Rolling stats for z-score (approx monthly = 24 obs = 2yr, 60 = 5yr)
        avg(obs_value) over (partition by series_id order by obs_date rows between 23 preceding and current row) as mean_2y,
        stddev(obs_value) over (partition by series_id order by obs_date rows between 23 preceding and current row) as std_2y,

        avg(obs_value) over (partition by series_id order by obs_date rows between 59 preceding and current row) as mean_5y,
        stddev(obs_value) over (partition by series_id order by obs_date rows between 59 preceding and current row) as std_5y

    from base
    window w as (partition by series_id order by obs_date)
),

features as (
    select
        series_id,
        obs_date,
        obs_value,

        -- Momentum
        case when val_lag_1m  != 0 then round((obs_value - val_lag_1m)  / abs(val_lag_1m)  * 100, 4) end as value_mom_1m,
        case when val_lag_3m  != 0 then round((obs_value - val_lag_3m)  / abs(val_lag_3m)  * 100, 4) end as value_mom_3m,
        case when val_lag_12m != 0 then round((obs_value - val_lag_12m) / abs(val_lag_12m) * 100, 4) end as value_yoy,

        -- Z-scores (nullify when std = 0 to avoid division by zero)
        case when std_2y > 0 then round((obs_value - mean_2y) / std_2y, 4) end as z_score_2y,
        case when std_5y > 0 then round((obs_value - mean_5y) / std_5y, 4) end as z_score_5y,

        -- Trend label (3m momentum threshold = ±1%)
        case
            when val_lag_3m is null then 'unknown'
            when (obs_value - val_lag_3m) / nullif(abs(val_lag_3m), 0) * 100 >  1.0 then 'rising'
            when (obs_value - val_lag_3m) / nullif(abs(val_lag_3m), 0) * 100 < -1.0 then 'falling'
            else 'stable'
        end as trend,

        now() as computed_at,
        'dbt_v1.0' as scoring_version

    from lagged
)

select * from features
