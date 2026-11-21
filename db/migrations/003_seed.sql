-- 003_seed.sql — Akce na pátek
-- Seed data for stores and categories. Idempotent.

insert into store (code, name, website, loyalty_name) values
  ('tesco',    'Tesco',    'https://nakup.itesco.cz', 'Clubcard'),
  ('billa',    'Billa',    'https://www.billa.cz',    'BILLA Klub'),
  ('albert',   'Albert',   'https://www.albert.cz',   'Můj Albert'),
  ('lidl',     'Lidl',     'https://www.lidl.cz',     'Lidl Plus'),
  ('kaufland', 'Kaufland', 'https://www.kaufland.cz', 'Kaufland Card'),
  ('penny',    'Penny',    'https://www.penny.cz',    null)
on conflict (code) do nothing;

-- MVP = spirits only; wine/sparkling/beer are phase 2.
insert into category (slug, name, sort_order) values
  ('rum',      'Rum',                10),
  ('vodka',    'Vodka',               20),
  ('gin',      'Gin',                 30),
  ('whisky',   'Whisky',              40),
  ('brandy',   'Koňak a brandy',      50),
  ('likery',   'Likéry',              60),
  ('bylinne',  'Bylinné',             70),
  ('palenky',  'Pálenky',             80),
  ('tequila',  'Tequila a mezcal',    90),
  ('ostatni',  'Ostatní lihoviny',   100)
on conflict (slug) do nothing;

-- Roles. Run AFTER setting the passwords manually in Neon UI:
--   create role etl_rw login password '...';
--   create role web_ro login password '...';
-- Then grant the privileges below.
--
-- grant select, insert, update, delete on all tables in schema public to etl_rw;
-- grant usage, select on all sequences in schema public to etl_rw;
-- grant select on mv_current_price, v_store_offer_today, v_product_card,
--                 v_data_freshness, store, category, product to web_ro;
