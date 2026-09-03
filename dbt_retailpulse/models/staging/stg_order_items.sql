with source as (
    select * from {{ source('raw', 'order_items_raw') }}
),

deduplicated as (
    select
        *,
        row_number() over (
            -- clé composée : order_id + order_item_id (voir docs/02_sources_donnees.md)
            partition by order_id, order_item_id
            order by updated_at desc
        ) as row_num
    from source
)

select
    order_item_id,
    order_id,
    product_id,
    quantity::number(10, 0)             as quantity,
    unit_price::number(12, 2)           as unit_price,
    unit_cost::number(12, 2)            as unit_cost,
    discount_percentage::number(8, 4)   as discount_percentage,
    created_at::timestamp_ntz           as created_at,
    updated_at::timestamp_ntz           as updated_at
from deduplicated
where row_num = 1