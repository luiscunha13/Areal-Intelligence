-- models/staging/stg_macro_observations.sql
-- ─────────────────────────────────────────
-- Cleans and casts raw macro observations.
-- Drops duplicates (keeping latest fetched_at per series+date).
-- This is the ONLY model that touches the raw macro_observations table.

with source as (
    select * from {{ source('raw', 'macro_observations') }}
),

deduped as (
    select
        series_id,
        date,
        value,
        source,
        fetched_at,
        run_id,
        row_number() over (
            partition by series_id, date
            order by fetched_at desc
        ) as rn
    from source
    where value is not null
),

cleaned as (
    select
        series_id,
        date::date                          as obs_date,
        value::numeric                      as obs_value,
        source                              as data_source,
        fetched_at,
        run_id
    from deduped
    where rn = 1
)

select * from cleaned
