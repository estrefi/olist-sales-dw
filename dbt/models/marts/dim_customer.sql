-- One row per real person. Location = from their most recent order.
with customer_orders as (
    select
        o.customer_unique_id,
        o.purchased_at,
        c.customer_zip_code_prefix,
        c.customer_city,
        c.customer_state
    from {{ ref('stg_orders') }} o
    join {{ ref('stg_customers') }} c using (customer_id)
),
ranked as (
    select
        *,
        row_number() over (partition by customer_unique_id order by purchased_at desc) as rn,
        min(purchased_at) over (partition by customer_unique_id) as first_purchased_at,
        count(*) over (partition by customer_unique_id) as lifetime_orders
    from customer_orders
)
select
    customer_unique_id              as customer_key,
    customer_zip_code_prefix        as zip_code_prefix,
    customer_city                   as city,
    customer_state                  as state,
    cast(first_purchased_at as date) as first_order_date,
    lifetime_orders,
    lifetime_orders > 1             as is_repeat_customer
from ranked
where rn = 1
