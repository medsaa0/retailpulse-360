{{
    config(materialized='table')
}}

with spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2024-01-01' as date)",
        end_date="cast('2027-12-31' as date)"
    ) }}
)

select
    date_day                                as date_key,
    date_day,
    extract(year from date_day)             as year,
    extract(month from date_day)            as month,
    extract(day from date_day)              as day,
    extract(dayofweek from date_day)        as day_of_week,
    extract(quarter from date_day)          as quarter,
    (extract(dayofweek from date_day) in (0, 6)) as is_weekend
from spine