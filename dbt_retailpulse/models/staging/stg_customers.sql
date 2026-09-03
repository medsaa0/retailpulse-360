with source as (
    select * from {{ source('raw', 'customers_raw') }}
),

deduplicated as (
    select
        *,
        row_number() over (
            partition by customer_id
            order by updated_at desc
        ) as row_num
    from source
)

select
    customer_id,
    first_name,
    last_name,
    email,
    phone,
    city,
    country,
    customer_segment,
    created_at::timestamp_ntz  as created_at,
    updated_at::timestamp_ntz  as updated_at
from deduplicated
where row_num = 1