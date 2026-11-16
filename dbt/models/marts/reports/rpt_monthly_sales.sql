-- Revenue, orders and average order value per month (excluding canceled/unavailable)
select
    d.month_start,
    count(*)                         as orders,
    sum(f.order_value)               as revenue,
    round(avg(f.order_value), 2)     as avg_order_value,
    round(avg(case when f.is_late then 1.0 else 0.0 end), 3) as late_share
from {{ ref('fct_orders') }} f
join {{ ref('dim_date') }} d on d.date_key = f.date_key
where f.order_status not in ('canceled', 'unavailable')
group by d.month_start
