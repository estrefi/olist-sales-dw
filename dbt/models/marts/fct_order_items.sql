-- Grain: one row per item sold. Use for revenue by product, category, seller.
select
    i.order_id,
    i.order_item_id,
    i.product_id             as product_key,
    i.seller_id              as seller_key,
    o.customer_unique_id     as customer_key,
    o.purchase_date          as date_key,
    o.order_status,
    i.price,
    i.freight_value,
    i.price + i.freight_value as item_total
from {{ ref('stg_order_items') }} i
join {{ ref('stg_orders') }} o using (order_id)
