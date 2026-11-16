select
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    o.order_status,
    o.order_purchase_timestamp                as purchased_at,
    cast(o.order_purchase_timestamp as date)  as purchase_date,
    o.order_approved_at                       as approved_at,
    o.order_delivered_carrier_date            as shipped_at,
    o.order_delivered_customer_date           as delivered_at,
    cast(o.order_estimated_delivery_date as date) as estimated_delivery_date,
    datediff(o.order_delivered_customer_date, o.order_purchase_timestamp) as days_to_deliver,
    case
        when o.order_delivered_customer_date is null then null
        else cast(o.order_delivered_customer_date as date) > cast(o.order_estimated_delivery_date as date)
    end as is_late,
    o.is_carrier_before_approval,
    o.is_delivered_before_carrier
from {{ source('silver', 'orders') }} o
left join {{ source('silver', 'customers') }} c using (customer_id)
