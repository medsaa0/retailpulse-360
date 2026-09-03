select
    {{ dbt_utils.generate_surrogate_key(['product_id']) }} as product_key,
    product_id,
    product_name,
    category,
    subcategory,
    brand,
    unit_price,
    unit_cost,
    is_active,
    dbt_valid_from                        as valid_from,
    coalesce(dbt_valid_to, '9999-12-31')  as valid_to,
    (dbt_valid_to is null)                as is_current
from {{ ref('snap_products') }}