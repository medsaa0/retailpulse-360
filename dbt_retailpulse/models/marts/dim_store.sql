select
    {{ dbt_utils.generate_surrogate_key(['store_id']) }} as store_key,
    store_id,
    store_name,
    city,
    region,
    opening_date,
    is_active
from {{ ref('stg_stores') }}