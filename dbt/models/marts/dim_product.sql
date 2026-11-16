select
    product_id as product_key,
    category,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm,
    product_photos_qty
from {{ ref('stg_products') }}
