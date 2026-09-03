select
    {{ dbt_utils.generate_surrogate_key(['customer_id']) }} as customer_key,
    customer_id,
    first_name,
    last_name,
    email,
    phone,
    city,
    country,
    customer_segment,
    dbt_valid_from                            as valid_from,
    coalesce(dbt_valid_to, '9999-12-31')      as valid_to,
    (dbt_valid_to is null)                    as is_current
from {{ ref('snap_customers') }}