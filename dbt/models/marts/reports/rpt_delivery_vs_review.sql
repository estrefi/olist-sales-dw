-- Review scores by how late the delivery was (delivered orders with a review)
with delivered as (
    select
        review_score,
        datediff(cast(delivered_at as date), estimated_delivery_date) as days_late
    from {{ ref('fct_orders') }}
    where order_status = 'delivered'
      and delivered_at is not null
      and review_score is not null
)
select
    case
        when days_late <= 0 then '1. On time or early'
        when days_late <= 3 then '2. 1-3 days late'
        when days_late <= 7 then '3. 4-7 days late'
        else '4. 8+ days late'
    end                                                        as delivery_bucket,
    count(*)                                                   as orders,
    round(avg(review_score), 2)                                as avg_review_score,
    round(avg(case when review_score = 1 then 1.0 else 0.0 end), 3) as share_1_star
from delivered
group by 1
