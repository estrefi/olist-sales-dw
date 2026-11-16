-- Customers grouped by first-purchase month: how many ordered again N months later?
with orders as (
    select f.customer_key, date_trunc('month', f.date_key) as order_month
    from {{ ref('fct_orders') }} f
    where f.order_status not in ('canceled', 'unavailable')
),
firsts as (
    select customer_key, min(order_month) as cohort_month
    from orders
    group by customer_key
),
activity as (
    select distinct
        f.cohort_month,
        cast(months_between(o.order_month, f.cohort_month) as int) as months_since_first,
        o.customer_key
    from orders o
    join firsts f using (customer_key)
),
sizes as (
    select cohort_month, count(*) as cohort_size from firsts group by cohort_month
)
select
    a.cohort_month,
    a.months_since_first,
    count(*)                                   as active_customers,
    s.cohort_size,
    round(count(*) / s.cohort_size, 4)         as retention_rate
from activity a
join sizes s using (cohort_month)
group by a.cohort_month, a.months_since_first, s.cohort_size
