select
    {{ dbt_utils.generate_surrogate_key(['oi.order_id', 'oi.order_item_id']) }} as order_item_key,
    oi.order_id,
    oi.order_item_id,
    dp.product_key,
    o.order_date::date                                as order_date_key,

    oi.quantity,
    oi.unit_price,
    oi.unit_cost,
    oi.discount_percentage,
    oi.quantity * oi.unit_price
        * (1 - oi.discount_percentage)                as net_revenue,
    oi.quantity * oi.unit_cost                          as total_cost,
    (oi.quantity * oi.unit_price * (1 - oi.discount_percentage))
        - (oi.quantity * oi.unit_cost)                    as gross_margin

from {{ ref('stg_order_items') }} oi
inner join {{ ref('stg_orders') }} o
    on oi.order_id = o.order_id
left join {{ ref('dim_product') }} dp
    on oi.product_id = dp.product_id
    and o.order_date >= dp.valid_from
    and o.order_date <  dp.valid_to