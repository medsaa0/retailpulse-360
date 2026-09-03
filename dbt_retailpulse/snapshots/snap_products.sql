{% snapshot snap_products %}

{{
    config(
        target_schema='intermediate',
        unique_key='product_id',
        strategy='timestamp',
        updated_at='updated_at',
    )
}}

select * from {{ ref('stg_products') }}

{% endsnapshot %}