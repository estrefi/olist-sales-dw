-- Grain: one row per order. Items and payments are summed per order FIRST,
-- then joined, so nothing is double-counted.
with items as (
    select
        order_id,
        count(*)           as item_count,
        sum(price)         as items_value,
        sum(freight_value) as freight_value
    from {{ ref('stg_order_items') }}
    group by order_id
),
payments as (
    select
        order_id,
        sum(payment_value)        as payment_value,
        max(payment_installments) as max_installments,
        max_by(payment_type, payment_value) as main_payment_type
    from {{ ref('stg_payments') }}
    group by order_id
),
reviews as (
    select order_id, review_score
    from {{ ref('stg_reviews') }}
)
select
    o.order_id,
    o.customer_unique_id                    as customer_key,
    o.purchase_date                         as date_key,
    o.order_status,
    o.purchased_at,
    o.delivered_at,
    o.estimated_delivery_date,
    o.days_to_deliver,
    o.is_late,
    coalesce(i.item_count, 0)               as item_count,
    coalesce(i.items_value, 0)              as items_value,
    coalesce(i.freight_value, 0)            as freight_value,
    coalesce(i.items_value, 0) + coalesce(i.freight_value, 0) as order_value,
    p.payment_value,
    p.main_payment_type,
    p.max_installments,
    r.review_score,
    i.order_id is not null                  as has_items
from {{ ref('stg_orders') }} o
left join items    i using (order_id)
left join payments p using (order_id)
left join reviews  r using (order_id)
