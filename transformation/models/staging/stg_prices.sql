-- models/staging/stg_prices.sql
-- ─────────────────────────────
-- Cleans and casts raw OHLCV price data.
-- Joins with the ETF catalog to attach category metadata.

with source as (
    select * from {{ source('raw', 'prices') }}
),

catalog as (
    select ticker, category, sub_category, benchmark, gics_sector
    from {{ source('raw', 'etfs') }}
),

deduped as (
    select
        ticker,
        date,
        open,
        high,
        low,
        close,
        adj_close,
        volume,
        source,
        fetched_at,
        row_number() over (
            partition by ticker, date
            order by fetched_at desc
        ) as rn
    from source
    where close is not null
      and adj_close is not null
      and close > 0
),

cleaned as (
    select
        d.ticker,
        d.date::date            as price_date,
        d.open::numeric         as open_price,
        d.high::numeric         as high_price,
        d.low::numeric          as low_price,
        d.close::numeric        as close_price,
        d.adj_close::numeric    as adj_close_price,
        d.volume::bigint        as volume,
        d.source                as data_source,
        d.fetched_at,
        -- Catalog metadata
        c.category              as etf_category,
        c.sub_category          as etf_sub_category,
        c.benchmark,
        c.gics_sector
    from deduped d
    left join catalog c on c.ticker = d.ticker
    where d.rn = 1
)

select * from cleaned
