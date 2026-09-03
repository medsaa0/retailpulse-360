select
    return_id,
    order_id,
    order_item_id,
    product_id,
    returned_quantity::number(10, 0)  as returned_quantity,
    return_reason,
    return_status,
    return_date::date                 as return_date,
    refund_amount::number(12, 2)      as refund_amount
from {{ source('raw', 'returns_raw') }}