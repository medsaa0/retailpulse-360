with source as (
    select * from {{ source('raw', 'orders_raw') }}
),

deduplicated as (
    select
        *,
        row_number() over (
            partition by order_id
            order by updated_at desc
        ) as row_num
    from source
)

select
    order_id,
    customer_id,
    store_id,
    channel,
    order_status,
    order_date::timestamp_ntz  as order_date,
    currency,
    payment_method,
    created_at::timestamp_ntz  as created_at,
    updated_at::timestamp_ntz  as updated_at
from deduplicated
where row_num = 1