/**
 * Kategorie pro mřížku a filtr. Musí zůstat v synchronu s db/migrations/003_seed.sql
 * (slug + name). Pokud přibyde kategorie v DB, přidej ji sem taky.
 */

export type CategorySlug =
  | "rum"
  | "vodka"
  | "gin"
  | "whisky"
  | "brandy"
  | "likery"
  | "bylinne"
  | "palenky"
  | "tequila"
  | "ostatni";

export const CATEGORIES: { slug: CategorySlug; name: string }[] = [
  { slug: "rum", name: "Rum" },
  { slug: "vodka", name: "Vodka" },
  { slug: "gin", name: "Gin" },
  { slug: "whisky", name: "Whisky" },
  { slug: "brandy", name: "Koňak & brandy" },
  { slug: "likery", name: "Likéry" },
  { slug: "bylinne", name: "Bylinné" },
  { slug: "palenky", name: "Pálenky" },
  { slug: "tequila", name: "Tequila" },
  { slug: "ostatni", name: "Ostatní" },
];

export const CATEGORY_NAMES: Record<CategorySlug, string> = Object.fromEntries(
  CATEGORIES.map((c) => [c.slug, c.name]),
) as Record<CategorySlug, string>;
