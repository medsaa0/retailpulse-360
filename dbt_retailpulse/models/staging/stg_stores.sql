with source as (
    select * from {{ source('raw', 'stores_raw') }}
),

deduplicated as (
    select
        *,
        row_number() over (
            partition by store_id
            order by updated_at desc
        ) as row_num
    from source
)

select
    store_id,
    store_name,
    city,
    region,
    opening_date::date         as opening_date,
    active::boolean            as is_active,
    created_at::timestamp_ntz  as created_at,
    updated_at::timestamp_ntz  as updated_at
from deduplicated
where row_num = 1