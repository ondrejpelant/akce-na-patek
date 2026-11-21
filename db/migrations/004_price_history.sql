-- 004_price_history.sql — Akce na pátek
-- Price history for the product-detail sparkline (M6).
-- Run in the Neon SQL editor as the database owner (same as 001–003).

-- One row per SCD2 price version of a matched store item.
create or replace view v_price_history as
select sp.product_id,
       sp.store_id,
       p.price_type,
       p.price_source,
       p.price_czk,
       p.promo_from,
       p.promo_to,
       p.valid_from,
       p.valid_to
from price p
join store_product sp on sp.id = p.store_product_id
where sp.product_id is not null;

-- Lowest price that was valid on each day, per product (last 90 days).
-- Same validity rules as v_store_offer_today: regular prices always count,
-- promo/loyalty prices only inside their promo_from..promo_to window.
create or replace view v_daily_best_price as
select h.product_id,
       d::date as day,
       min(h.price_czk) as best_price
from v_price_history h
cross join lateral generate_series(
    greatest(h.valid_from::date, current_date - 89),
    least(case when h.valid_to = 'infinity' then current_date
               else (h.valid_to - interval '1 microsecond')::date end,
          current_date),
    interval '1 day'
) d
where h.price_type = 'regular'
   or d::date between coalesce(h.promo_from, d::date) and coalesce(h.promo_to, d::date)
group by h.product_id, d::date;

grant select on v_price_history, v_daily_best_price to web_ro;
