# Datové dotazy (web)

Web nemá vlastní API — **React Server Components čtou DB přímo** (Drizzle + `@neondatabase/serverless`, role `web_ro`). Cache: `export const revalidate = 3600` + on-demand revalidace, kterou na konci zavolá `aktualizuj.bat` (`/api/revalidate?token=...`).

## Mřížka
```sql
select id, slug, brand, name, volume_ml, image_url, best_price, best_price_type,
       regular_czk, best_store, price_per_l, store_count
from v_product_card
where ($1::text is null or category_slug = $1)
  and ($2::text is null or search_text % f_norm($2) or search_text like '%' || f_norm($2) || '%')
  and ($3::boolean is not true or best_price_type <> 'regular')
order by
  case when $2 is not null then similarity(search_text, f_norm($2)) end desc nulls last,
  best_price asc
limit 48 offset $4;
```
(Řazení dle `sort` parametru: `price` | `price_per_l` | `discount` = `1 - best_price/regular_czk`.)

## Detail
```sql
select s.code, s.name, s.logo_url, s.loyalty_name,
       o.price_type, o.price_source, o.price_czk, o.regular_czk, o.promo_to, o.url, o.observed_at
from v_store_offer_today o
join store s on s.id = o.store_id
where o.product_id = $1
order by o.price_czk;
```

## Stáří dat (banner)
```sql
select min(last_ok_at) as oldest, max(last_ok_at) as newest from v_data_freshness;
```

## Route handlery
- `POST /api/revalidate?token=` — `revalidatePath('/')`, token z env `REVALIDATE_TOKEN`.
- `GET /api/health` — `select 1`, pro rychlou kontrolu.
