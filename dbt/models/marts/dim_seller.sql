select
    s.seller_id              as seller_key,
    s.seller_zip_code_prefix as zip_code_prefix,
    s.seller_city            as city,
    s.seller_state           as state,
    g.lat,
    g.lng
from {{ ref('stg_sellers') }} s
left join {{ ref('stg_geolocation') }} g on g.zip = s.seller_zip_code_prefix
