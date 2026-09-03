select
    {{ dbt_utils.generate_surrogate_key(['o.order_id']) }}   as order_key,
    o.order_id,
    dc.customer_key,
    ds.store_key,
    o.order_date::date                                        as order_date_key,
    o.channel,
    o.order_status,
    o.currency,
    o.payment_method,

    coalesce(sum(oi.quantity * oi.unit_price
                 * (1 - oi.discount_percentage)), 0)          as gross_revenue,
    coalesce(sum(oi.quantity * oi.unit_cost), 0)               as total_cost,
    count(distinct oi.order_item_id)                            as item_count

from {{ ref('stg_orders') }} o
left join {{ ref('stg_order_items') }} oi
    on o.order_id = oi.order_id
left join {{ ref('dim_customer') }} dc
    on o.customer_id = dc.customer_id
    and o.order_date >= dc.valid_from
    and o.order_date <  dc.valid_to
left join {{ ref('dim_store') }} ds
    on o.store_id = ds.store_id

group by 1, 2, 3, 4, 5, 6, 7, 8, 9