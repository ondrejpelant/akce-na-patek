-- 002_views.sql — Akce na pátek
-- Serving layer. Refresh mv_current_price after each update run.

-- 1) current prices per item (materialized; refreshed by the scraper)
create materialized view mv_current_price as
select sp.product_id, sp.store_id, sp.id as store_product_id, sp.url, sp.last_seen_at,
       p.price_type, p.price_source, p.price_czk, p.regular_czk,
       p.promo_from, p.promo_to, p.observed_at
from store_product sp
join price p on p.store_product_id = sp.id and p.valid_to = 'infinity'
where sp.product_id is not null;

create unique index ux_mv_current_price on mv_current_price (store_product_id, price_type);
create index ix_mv_current_price_product on mv_current_price (product_id);
create index ix_mv_current_price_store on mv_current_price (store_id);

-- 2) today's offer: one (lowest) price per product × store
-- Date checks against current_date live in the plain view so freshness holds between refreshes.
create view v_store_offer_today as
select *
from (
  select c.product_id, c.store_id, c.store_product_id, c.url, c.last_seen_at,
         c.price_type, c.price_source, c.price_czk, c.regular_czk,
         c.promo_from, c.promo_to, c.observed_at,
         row_number() over (
           partition by c.product_id, c.store_id
           order by c.price_czk,
                    case c.price_type when 'promo' then 1 when 'regular' then 2 else 3 end
         ) as rn
  from mv_current_price c
  where (c.price_type = 'regular'
         or current_date between coalesce(c.promo_from, current_date)
                             and coalesce(c.promo_to,   current_date))
) x
where rn = 1;

-- 3) grid card: lowest price across stores (loyalty included; UI differentiates visually)
create view v_product_card as
select pr.id, pr.slug, pr.brand, pr.name, pr.volume_ml, pr.image_url, pr.search_text,
       c.slug as category_slug,
       best.price_czk  as best_price,
       best.price_type as best_price_type,      -- 'loyalty' → UI shows color + ⓘ
       best.regular_czk,
       best.promo_to,
       s.code          as best_store,
       s.loyalty_name  as best_loyalty_name,
       round(best.price_czk / pr.volume_ml * 1000, 2) as price_per_l,
       cnt.store_count
from product pr
join category c on c.id = pr.category_id
join lateral (
  select o.* from v_store_offer_today o
  where o.product_id = pr.id
  order by o.price_czk
  limit 1
) best on true
join store s on s.id = best.store_id
join lateral (
  select count(*) as store_count
  from v_store_offer_today o where o.product_id = pr.id
) cnt on true;

-- 4) freshness per store (banner)
create view v_data_freshness as
select s.code, s.name,
       max(r.finished_at) filter (where r.status in ('ok','partial')) as last_ok_at
from store s
left join scrape_run r on r.store_id = s.id
where s.is_active
group by s.code, s.name;
