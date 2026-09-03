with source as (
    select * from {{ source('raw', 'products_raw') }}
),

deduplicated as (
    select
        *,
        row_number() over (
            partition by product_id
            order by updated_at desc
        ) as row_num
    from source
)

select
    product_id,
    product_name,
    category,
    subcategory,
    brand,
    unit_price::number(12, 2)  as unit_price,
    unit_cost::number(12, 2)   as unit_cost,
    active::boolean            as is_active,
    created_at::timestamp_ntz  as created_at,
    updated_at::timestamp_ntz  as updated_at
from deduplicated
where row_num = 1