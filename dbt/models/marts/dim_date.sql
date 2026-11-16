-- A calendar covering the whole Olist period, one row per day.
with days as (
    select explode(sequence(date'2016-09-01', date'2018-12-31', interval 1 day)) as date_day
)
select
    date_day                          as date_key,
    year(date_day)                    as year,
    quarter(date_day)                 as quarter,
    month(date_day)                   as month,
    date_format(date_day, 'MMMM')     as month_name,
    date_trunc('month', date_day)     as month_start,
    weekofyear(date_day)              as week_of_year,
    date_format(date_day, 'EEEE')     as weekday_name,
    dayofweek(date_day) in (1, 7)     as is_weekend
from days
