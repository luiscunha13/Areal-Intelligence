-- models/marts/macro/mart_market_regimes.sql
-- ─────────────────────────────────────────────
-- Classifies market regime for each date using the v2 momentum engine:
--
--   Growth momentum  = 3m momentum of INDPRO (Industrial Production)
--   Inflation momentum = 3m momentum of CPIAUCSL (CPI)
--   FCA (Financial Conditions Amplifier) = composite of NFCI + HY Spread z-scores
--
-- Quadrant matrix:
--   growth↑ inflation↓ → GOLDILOCKS   (best for equities)
--   growth↑ inflation↑ → REFLATION    (cyclicals, commodities)
--   growth↓ inflation↑ → STAGFLATION  (hard assets, short duration)
--   growth↓ inflation↓ → DEFLATION    (treasuries, defensive)
--
-- Also outputs policy_stance (restrictive / neutral / accommodative)
-- based on the Fed Funds rate z-score.

with growth as (
    select
        obs_date,
        value_mom_3m as growth_momentum,
        z_score_2y   as growth_z
    from {{ ref('int_macro_features') }}
    where series_id = 'INDPRO'
),

inflation as (
    select
        obs_date,
        value_mom_3m as inflation_momentum,
        z_score_2y   as inflation_z
    from {{ ref('int_macro_features') }}
    where series_id = 'CPIAUCSL'
),

nfci as (
    select obs_date, obs_value as nfci_value
    from {{ ref('stg_macro_observations') }}
    where series_id = 'NFCI'
),

hy_spread as (
    select obs_date, z_score_2y as hy_z
    from {{ ref('int_macro_features') }}
    where series_id = 'BAMLH0A0HYM2'
),

fed_funds as (
    select obs_date, z_score_5y as ff_z
    from {{ ref('int_macro_features') }}
    where series_id = 'FEDFUNDS'
),

joined as (
    select
        g.obs_date,
        g.growth_momentum,
        g.growth_z,
        i.inflation_momentum,
        i.inflation_z,
        n.nfci_value,
        h.hy_z,
        f.ff_z,

        -- Financial Conditions Amplifier: average of NFCI + HY spread z-score
        -- Positive = tight conditions (bearish), Negative = loose (bullish)
        round(
            coalesce((n.nfci_value + coalesce(h.hy_z, 0)) / 2.0, n.nfci_value, 0),
        4) as fca_score

    from growth g
    left join inflation i on i.obs_date = g.obs_date
    left join nfci n      on n.obs_date = g.obs_date
    left join hy_spread h on h.obs_date = g.obs_date
    left join fed_funds f on f.obs_date = g.obs_date
    where g.growth_momentum is not null
      and i.inflation_momentum is not null
),

classified as (
    select
        obs_date,
        round(growth_momentum, 4)    as growth_momentum,
        round(inflation_momentum, 4) as inflation_momentum,
        round(fca_score, 4)          as fca_score,
        round(coalesce(ff_z, 0), 4)  as policy_z,

        -- Regime quadrant
        case
            when growth_momentum >= 0 and inflation_momentum <= 0 then 'goldilocks'
            when growth_momentum >= 0 and inflation_momentum >  0 then 'reflation'
            when growth_momentum <  0 and inflation_momentum >  0 then 'stagflation'
            when growth_momentum <  0 and inflation_momentum <= 0 then 'deflation'
        end as quadrant,

        -- Policy stance: based on Fed Funds 5yr z-score
        case
            when ff_z is null then 'unknown'
            when ff_z >  0.5  then 'restrictive'
            when ff_z < -0.5  then 'accommodative'
            else 'neutral'
        end as policy_stance,

        -- Confidence: inversely related to how close to zero both momenta are
        round(
            least(abs(growth_momentum), 5) / 5.0 * 0.5
            + least(abs(inflation_momentum), 5) / 5.0 * 0.5,
        4) as confidence,

        now()        as computed_at,
        'dbt_v1.0'   as scoring_version

    from joined
)

select * from classified
order by obs_date desc
