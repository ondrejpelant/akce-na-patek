-- 001_init.sql — Akce na pátek
-- Initial schema. See "03 Data/Datový model.md" for rationale.
-- Run order: 001 -> 002 -> 003. Only forward migrations.

create extension if not exists pg_trgm;
create extension if not exists unaccent;

-- unaccent is not IMMUTABLE → wrap it so it can be used in indexes and generated columns.
create or replace function f_norm(t text) returns text
language sql immutable parallel safe as
$$ select lower(public.unaccent('public.unaccent', coalesce(t, ''))) $$;

create table store (
  id            smallserial primary key,
  code          text not null unique,          -- 'tesco','billa','albert','lidl','kaufland','penny'
  name          text not null,
  website       text not null,
  logo_url      text,
  loyalty_name  text,                          -- 'Clubcard','Můj Albert','BILLA Klub','Lidl Plus','Kaufland Card'
  is_active     boolean not null default true
);

create table category (
  id         smallserial primary key,
  slug       text not null unique,             -- 'rum','vodka',...
  name       text not null,
  sort_order smallint not null default 100
);

create table product (
  id          bigserial primary key,
  category_id smallint not null references category(id),
  brand       text not null,
  name        text not null,                   -- without volume, e.g. 'Vodka'
  volume_ml   integer not null check (volume_ml > 0),
  abv         numeric(4,1),                    -- % alcohol
  ean         text,
  image_url   text,
  slug        text not null unique,            -- 'finlandia-vodka-700ml'
  search_text text generated always as (f_norm(brand || ' ' || name)) stored,
  created_at  timestamptz not null default now(),
  unique (brand, name, volume_ml)
);
create index ix_product_search on product using gin (search_text gin_trgm_ops);
create index ix_product_category on product (category_id);

create table store_product (
  id            bigserial primary key,
  store_id      smallint not null references store(id),
  store_sku     text not null,                 -- source ID; for leaflets hash(norm_name + volume)
  product_id    bigint references product(id), -- NULL = unmatched
  raw_name      text not null,
  brand_guess   text,
  volume_ml     integer,
  abv           numeric(4,1),
  ean           text,
  url           text,
  image_url     text,
  source_kind   text not null check (source_kind in ('catalog','leaflet')),
  first_seen_at timestamptz not null default now(),
  last_seen_at  timestamptz not null default now(),
  unique (store_id, store_sku)
);
create index ix_sp_product on store_product (product_id);
create index ix_sp_unmatched on store_product (store_id) where product_id is null;

create table price (
  id               bigserial primary key,
  store_product_id bigint not null references store_product(id),
  price_type       text not null check (price_type in ('regular','promo','loyalty')),
  price_czk        numeric(10,2) not null check (price_czk > 0),
  regular_czk      numeric(10,2),              -- "before discount" price, when the source gives it
  promo_from       date,
  promo_to         date,
  valid_from       timestamptz not null default now(),
  valid_to         timestamptz not null default 'infinity',
  price_source     text not null check (price_source in ('catalog','leaflet','leaflet_regular','manual')),
  observed_at      timestamptz not null default now(), -- last time we saw / confirmed this price
  scrape_run_id    bigint
);
-- at most one current price of a given type per item
create unique index ux_price_current on price (store_product_id, price_type) where valid_to = 'infinity';
create index ix_price_sp on price (store_product_id);

create table scrape_run (
  id            bigserial primary key,
  store_id      smallint not null references store(id),
  started_at    timestamptz not null default now(),
  finished_at   timestamptz,
  status        text not null default 'running' check (status in ('running','ok','partial','failed')),
  items_found   integer,
  items_changed integer,
  host          text,                          -- PC name where the update ran
  error         text
);
create index ix_scrape_run_store on scrape_run (store_id, started_at desc);

create table stg_listing (                     -- raw data, 14-day retention
  id            bigserial primary key,
  scrape_run_id bigint not null references scrape_run(id),
  store_sku     text not null,
  payload       jsonb not null,                -- validated ScrapedItem
  raw           jsonb,                         -- exactly what the source returned (for debugging parsers)
  loaded_at     timestamptz not null default now()
);
create index ix_stg_listing_run on stg_listing (scrape_run_id);

create table match_candidate (
  store_product_id bigint not null references store_product(id),
  product_id       bigint not null references product(id),
  score            numeric(5,2) not null,      -- 0–100
  method           text not null,              -- 'ean','exact_norm','fuzzy'
  status           text not null default 'pending' check (status in ('pending','accepted','rejected')),
  created_at       timestamptz not null default now(),
  primary key (store_product_id, product_id)
);
create index ix_match_candidate_pending on match_candidate (status, score desc) where status = 'pending';
