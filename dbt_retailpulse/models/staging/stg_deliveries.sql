with source as (
    select * from {{ source('raw', 'deliveries_raw') }}
),

deduplicated as (
    select
        *,
        row_number() over (
            partition by delivery_id
            order by event_timestamp desc
        ) as row_num
    from source
)

select
    delivery_id,
    order_id,
    carrier,
    delivery_status,
    -- ces colonnes sont STRING en RAW (l'API renvoie du texte) : cast explicite ici
    try_to_timestamp_ntz(event_timestamp)      as event_timestamp,
    try_to_date(shipping_date)                 as shipping_date,
    try_to_date(expected_delivery_date)        as expected_delivery_date,
    try_to_date(actual_delivery_date)          as actual_delivery_date,
    destination_city
from deduplicated
where row_num = 1