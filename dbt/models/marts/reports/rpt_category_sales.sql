-- Revenue per product category, at item grain (no double-counting)
select
    p.category,
    count(*)                     as items_sold,
    count(distinct i.order_id)   as orders,
    sum(i.price)                 as revenue,
    round(avg(i.price), 2)       as avg_item_price
from {{ ref('fct_order_items') }} i
join {{ ref('dim_product') }} p on p.product_key = i.product_key
where i.order_status not in ('canceled', 'unavailable')
group by p.category
