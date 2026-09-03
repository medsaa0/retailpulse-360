{% snapshot snap_customers %}

{{
    config(
        target_schema='intermediate',
        unique_key='customer_id',
        strategy='timestamp',
        updated_at='updated_at',
    )
}}

select * from {{ ref('stg_customers') }}

{% endsnapshot %}