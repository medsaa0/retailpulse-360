select
    snapshot_date::date              as snapshot_date,
    store_id,
    product_id,
    available_quantity::number(10, 0) as available_quantity,
    reserved_quantity::number(10, 0)  as reserved_quantity,
    damaged_quantity::number(10, 0)   as damaged_quantity,
    reorder_threshold::number(10, 0)  as reorder_threshold
from {{ source('raw', 'inventory_raw') }}