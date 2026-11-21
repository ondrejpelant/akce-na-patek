/**
 * Query functions over the serving views. See db/migrations/002_views.sql.
 * All functions run as role web_ro (SELECT-only).
 */

import { sql } from "./db";
import type { CategorySlug } from "./categories";

export type SortOrder = "price" | "price_per_l" | "discount";
export type PriceType = "regular" | "promo" | "loyalty";
export type PriceSource = "catalog" | "leaflet" | "leaflet_regular" | "manual";

export type ProductCard = {
  id: number;
  slug: string;
  brand: string;
  name: string;
  volume_ml: number;
  image_url: string | null;
  category_slug: CategorySlug;
  best_price: number;
  best_price_type: PriceType;
  regular_czk: number | null;
  promo_to: string | null; // YYYY-MM-DD
  best_store: string;
  best_loyalty_name: string | null;
  price_per_l: number;
  store_count: number;
};

export type StoreOffer = {
  store_id: number;
  code: string;
  name: string;
  logo_url: string | null;
  loyalty_name: string | null;
  price_type: PriceType;
  price_source: PriceSource;
  price_czk: number;
  regular_czk: number | null;
  promo_from: string | null;
  promo_to: string | null;
  url: string | null;
  observed_at: string; // ISO timestamp
};

export type ProductDetail = {
  id: number;
  slug: string;
  brand: string;
  name: string;
  volume_ml: number;
  abv: number | null;
  image_url: string | null;
  category_slug: CategorySlug;
};

export type FreshnessRow = {
  code: string;
  name: string;
  last_ok_at: string | null;
};

const PAGE_SIZE = 48;

// ---------------------------------------------------------------------------
// Grid
// ---------------------------------------------------------------------------

export type GridFilters = {
  q?: string;
  category?: CategorySlug;
  sort?: SortOrder;
  promoOnly?: boolean;
  page?: number; // zero-based
};

export async function fetchGrid(filters: GridFilters = {}): Promise<ProductCard[]> {
  const q = filters.q?.trim() || null;
  const category = filters.category || null;
  const sort: SortOrder = filters.sort || "price";
  const promoOnly = !!filters.promoOnly;
  const offset = Math.max(0, filters.page ?? 0) * PAGE_SIZE;

  // Note: the columns we read mirror v_product_card. Numeric columns come back
  // as strings from pg → cast on the TS side.
  const rows = (await sql`
    select
      id, slug, brand, name, volume_ml, image_url, category_slug,
      best_price, best_price_type, regular_czk, promo_to,
      best_store, best_loyalty_name, price_per_l, store_count
    from v_product_card
    where (${category}::text is null or category_slug = ${category})
      and (${q}::text is null
           or search_text % f_norm(${q})
           or search_text like '%' || f_norm(${q}) || '%')
      and (${promoOnly}::boolean is not true or best_price_type <> 'regular')
    order by
      case when ${sort} = 'price'        then best_price end asc,
      case when ${sort} = 'price_per_l'  then price_per_l end asc,
      case when ${sort} = 'discount' and regular_czk is not null
           then best_price::numeric / regular_czk end asc,
      best_price asc
    limit ${PAGE_SIZE} offset ${offset}
  `) as Record<string, unknown>[];

  return rows.map(toProductCard);
}

export async function countGrid(filters: GridFilters = {}): Promise<number> {
  const q = filters.q?.trim() || null;
  const category = filters.category || null;
  const promoOnly = !!filters.promoOnly;
  const rows = (await sql`
    select count(*)::int as n
    from v_product_card
    where (${category}::text is null or category_slug = ${category})
      and (${q}::text is null
           or search_text % f_norm(${q})
           or search_text like '%' || f_norm(${q}) || '%')
      and (${promoOnly}::boolean is not true or best_price_type <> 'regular')
  `) as { n: number }[];
  return rows[0]?.n ?? 0;
}

// ---------------------------------------------------------------------------
// Detail
// ---------------------------------------------------------------------------

export async function fetchProduct(slug: string): Promise<ProductDetail | null> {
  const rows = (await sql`
    select p.id, p.slug, p.brand, p.name, p.volume_ml, p.abv, p.image_url,
           c.slug as category_slug
    from product p
    join category c on c.id = p.category_id
    where p.slug = ${slug}
    limit 1
  `) as Record<string, unknown>[];
  if (!rows[0]) return null;
  const r = rows[0];
  return {
    id: Number(r.id),
    slug: String(r.slug),
    brand: String(r.brand),
    name: String(r.name),
    volume_ml: Number(r.volume_ml),
    abv: r.abv == null ? null : Number(r.abv),
    image_url: r.image_url == null ? null : String(r.image_url),
    category_slug: r.category_slug as CategorySlug,
  };
}

export async function fetchOffers(productId: number): Promise<StoreOffer[]> {
  const rows = (await sql`
    select s.id as store_id, s.code, s.name, s.logo_url, s.loyalty_name,
           o.price_type, o.price_source, o.price_czk, o.regular_czk,
           o.promo_from, o.promo_to, o.url, o.observed_at
    from v_store_offer_today o
    join store s on s.id = o.store_id
    where o.product_id = ${productId}
    order by o.price_czk asc
  `) as Record<string, unknown>[];

  return rows.map((r) => ({
    store_id: Number(r.store_id),
    code: String(r.code),
    name: String(r.name),
    logo_url: r.logo_url == null ? null : String(r.logo_url),
    loyalty_name: r.loyalty_name == null ? null : String(r.loyalty_name),
    price_type: r.price_type as PriceType,
    price_source: r.price_source as PriceSource,
    price_czk: Number(r.price_czk),
    regular_czk: r.regular_czk == null ? null : Number(r.regular_czk),
    promo_from: r.promo_from == null ? null : String(r.promo_from),
    promo_to: r.promo_to == null ? null : String(r.promo_to),
    url: r.url == null ? null : String(r.url),
    observed_at: String(r.observed_at),
  }));
}

// ---------------------------------------------------------------------------
// Freshness banner
// ---------------------------------------------------------------------------

export type PricePoint = { day: string; price: number }; // day = YYYY-MM-DD

/**
 * Lowest valid price per day over the last 90 days (db/migrations/004).
 * Returns [] when the view is missing or web_ro lacks the grant, so the
 * detail page still renders before the migration is applied.
 */
export async function fetchPriceHistory(productId: number): Promise<PricePoint[]> {
  try {
    const rows = (await sql`
      select to_char(day, 'YYYY-MM-DD') as day, best_price
      from v_daily_best_price
      where product_id = ${productId}
      order by day
    `) as Record<string, unknown>[];
    return rows.map((r) => ({ day: String(r.day), price: Number(r.best_price) }));
  } catch (err) {
    console.warn("price history unavailable:", err instanceof Error ? err.message : err);
    return [];
  }
}

export type StatusRow = {
  code: string;
  name: string;
  is_active: boolean;
  last_started_at: string | null;
  last_finished_at: string | null;
  last_status: "running" | "ok" | "partial" | "failed" | null;
  last_items_found: number | null;
  last_items_changed: number | null;
  last_error: string | null;
  last_host: string | null;
};

export async function fetchStatus(): Promise<StatusRow[]> {
  const rows = (await sql`
    select
      s.code, s.name, s.is_active,
      r.started_at   as last_started_at,
      r.finished_at  as last_finished_at,
      r.status       as last_status,
      r.items_found  as last_items_found,
      r.items_changed as last_items_changed,
      r.error        as last_error,
      r.host         as last_host
    from store s
    left join lateral (
      select * from scrape_run
      where store_id = s.id
      order by started_at desc
      limit 1
    ) r on true
    order by s.code
  `) as Record<string, unknown>[];

  return rows.map((r) => ({
    code: String(r.code),
    name: String(r.name),
    is_active: Boolean(r.is_active),
    last_started_at: r.last_started_at == null ? null : String(r.last_started_at),
    last_finished_at: r.last_finished_at == null ? null : String(r.last_finished_at),
    last_status: (r.last_status ?? null) as StatusRow["last_status"],
    last_items_found: r.last_items_found == null ? null : Number(r.last_items_found),
    last_items_changed: r.last_items_changed == null ? null : Number(r.last_items_changed),
    last_error: r.last_error == null ? null : String(r.last_error),
    last_host: r.last_host == null ? null : String(r.last_host),
  }));
}

export async function fetchFreshness(): Promise<{ newest: Date | null; stores: FreshnessRow[] }> {
  const rows = (await sql`
    select code, name, last_ok_at
    from v_data_freshness
    order by name
  `) as Record<string, unknown>[];

  const stores: FreshnessRow[] = rows.map((r) => ({
    code: String(r.code),
    name: String(r.name),
    last_ok_at: r.last_ok_at == null ? null : String(r.last_ok_at),
  }));

  const times = stores
    .map((s) => s.last_ok_at)
    .filter((v): v is string => !!v)
    .map((v) => new Date(v).getTime());
  const newest = times.length ? new Date(Math.max(...times)) : null;
  return { newest, stores };
}

// ---------------------------------------------------------------------------

function toProductCard(r: Record<string, unknown>): ProductCard {
  return {
    id: Number(r.id),
    slug: String(r.slug),
    brand: String(r.brand),
    name: String(r.name),
    volume_ml: Number(r.volume_ml),
    image_url: r.image_url == null ? null : String(r.image_url),
    category_slug: r.category_slug as CategorySlug,
    best_price: Number(r.best_price),
    best_price_type: r.best_price_type as PriceType,
    regular_czk: r.regular_czk == null ? null : Number(r.regular_czk),
    promo_to: r.promo_to == null ? null : String(r.promo_to),
    best_store: String(r.best_store),
    best_loyalty_name: r.best_loyalty_name == null ? null : String(r.best_loyalty_name),
    price_per_l: Number(r.price_per_l),
    store_count: Number(r.store_count),
  };
}
