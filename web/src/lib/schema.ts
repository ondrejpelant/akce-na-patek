/**
 * Drizzle schema mirroring db/migrations/001_init.sql + 002_views.sql.
 * Source of truth for the DB is the SQL migrations; this file only gives the
 * web TypeScript types and a query builder surface (role web_ro, SELECT only).
 */
import { sql } from "drizzle-orm";
import {
  bigserial,
  boolean,
  date,
  index,
  integer,
  numeric,
  pgTable,
  pgView,
  smallint,
  smallserial,
  text,
  timestamp,
} from "drizzle-orm/pg-core";

export const store = pgTable("store", {
  id: smallserial("id").primaryKey(),
  code: text("code").notNull().unique(),
  name: text("name").notNull(),
  website: text("website").notNull(),
  logoUrl: text("logo_url"),
  loyaltyName: text("loyalty_name"),
  isActive: boolean("is_active").notNull().default(true),
});

export const category = pgTable("category", {
  id: smallserial("id").primaryKey(),
  slug: text("slug").notNull().unique(),
  name: text("name").notNull(),
  sortOrder: smallint("sort_order").notNull().default(100),
});

export const product = pgTable(
  "product",
  {
    id: bigserial("id", { mode: "number" }).primaryKey(),
    categoryId: smallint("category_id").notNull(),
    brand: text("brand").notNull(),
    name: text("name").notNull(),
    volumeMl: integer("volume_ml").notNull(),
    abv: numeric("abv"),
    ean: text("ean"),
    imageUrl: text("image_url"),
    slug: text("slug").notNull().unique(),
    searchText: text("search_text"),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (t) => [index("ix_product_category").on(t.categoryId)],
);

// Views exposed to web_ro. Columns match 002_views.sql.
export const vProductCard = pgView("v_product_card", {
  id: bigserial("id", { mode: "number" }).primaryKey(),
  slug: text("slug").notNull(),
  brand: text("brand").notNull(),
  name: text("name").notNull(),
  volumeMl: integer("volume_ml").notNull(),
  imageUrl: text("image_url"),
  searchText: text("search_text"),
  categorySlug: text("category_slug").notNull(),
  bestPrice: numeric("best_price").notNull(),
  bestPriceType: text("best_price_type").notNull(),
  regularCzk: numeric("regular_czk"),
  promoTo: date("promo_to"),
  bestStore: text("best_store").notNull(),
  bestLoyaltyName: text("best_loyalty_name"),
  pricePerL: numeric("price_per_l"),
  storeCount: integer("store_count"),
}).existing();

export const vStoreOfferToday = pgView("v_store_offer_today", {
  productId: bigserial("product_id", { mode: "number" }).notNull(),
  storeId: smallint("store_id").notNull(),
  storeProductId: bigserial("store_product_id", { mode: "number" }).notNull(),
  url: text("url"),
  lastSeenAt: timestamp("last_seen_at", { withTimezone: true }),
  priceType: text("price_type").notNull(),
  priceSource: text("price_source").notNull(),
  priceCzk: numeric("price_czk").notNull(),
  regularCzk: numeric("regular_czk"),
  promoFrom: date("promo_from"),
  promoTo: date("promo_to"),
  observedAt: timestamp("observed_at", { withTimezone: true }),
}).existing();

export const vDataFreshness = pgView("v_data_freshness", {
  code: text("code").notNull(),
  name: text("name").notNull(),
  lastOkAt: timestamp("last_ok_at", { withTimezone: true }),
}).existing();

// Convenience: raw SQL helper for f_norm() so query code mirrors the DB function.
export const fNorm = (value: string) => sql<string>`f_norm(${value})`;
