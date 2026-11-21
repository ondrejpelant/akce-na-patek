import Link from "next/link";
import { Suspense } from "react";
import ProductCard from "@/components/ProductCard";

// Home reads Neon per request; a pre-rendered snapshot would be stale the
// moment the scraper writes new prices. On-demand revalidation is handled by
// /api/revalidate, which the scraper POSTs to at the end of every update.
export const instant = false;

import SearchBox from "@/components/SearchBox";
import CategoryChips from "@/components/CategoryChips";
import SortAndFilter from "@/components/SortAndFilter";
import { CATEGORY_NAMES, type CategorySlug } from "@/lib/categories";
import { countGrid, fetchGrid, type GridFilters, type SortOrder } from "@/lib/queries";

const PAGE_SIZE = 48;
const VALID_CATS = new Set<CategorySlug>([
  "rum",
  "vodka",
  "gin",
  "whisky",
  "brandy",
  "likery",
  "bylinne",
  "palenky",
  "tequila",
  "ostatni",
]);

type SP = Awaited<PageProps<"/">["searchParams"]>;

function parseFilters(sp: SP): GridFilters {
  const q = typeof sp.q === "string" ? sp.q : undefined;
  const catRaw = typeof sp.cat === "string" ? sp.cat : undefined;
  const sortRaw = typeof sp.sort === "string" ? sp.sort : undefined;
  const promo = sp.promo === "1";
  const pageRaw = typeof sp.page === "string" ? parseInt(sp.page, 10) : 0;

  const category = catRaw && VALID_CATS.has(catRaw as CategorySlug)
    ? (catRaw as CategorySlug)
    : undefined;

  const sort: SortOrder | undefined =
    sortRaw === "price_per_l" || sortRaw === "discount" ? sortRaw : undefined;

  return {
    q,
    category,
    sort,
    promoOnly: promo,
    page: Number.isFinite(pageRaw) ? Math.max(0, pageRaw) : 0,
  };
}

export default async function Home({ searchParams }: PageProps<"/">) {
  const sp = await searchParams;
  const filters = parseFilters(sp);
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  if (filters.category) params.set("cat", filters.category);
  if (filters.sort) params.set("sort", filters.sort);
  if (filters.promoOnly) params.set("promo", "1");

  const [rows, total] = await Promise.all([fetchGrid(filters), countGrid(filters)]);
  const page = filters.page ?? 0;
  const shown = page * PAGE_SIZE + rows.length;
  const hasMore = shown < total;

  const nextPageParams = new URLSearchParams(params.toString());
  nextPageParams.set("page", String(page + 1));

  return (
    <div className="space-y-4">
      <div className="space-y-3">
        <SearchBox />
        <CategoryChips active={filters.category ?? null} params={params} />
        <Suspense fallback={null}>
          <SortAndFilter />
        </Suspense>
      </div>

      {rows.length === 0 ? (
        <EmptyState filters={filters} />
      ) : (
        <>
          <div className="text-xs text-neutral-500">
            {filters.category
              ? `${CATEGORY_NAMES[filters.category]} · `
              : ""}
            {total} {pluralise(total, ["produkt", "produkty", "produktů"])}
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
            {rows.map((card) => (
              <ProductCard key={card.id} card={card} />
            ))}
          </div>

          {hasMore && (
            <div className="pt-2 text-center">
              <Link
                href={`/?${nextPageParams.toString()}`}
                scroll={false}
                className="inline-block rounded-md border border-neutral-300 bg-white px-4 py-2 text-sm font-medium text-neutral-800 hover:border-neutral-500"
              >
                Načíst další
              </Link>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function EmptyState({ filters }: { filters: GridFilters }) {
  const hasFilter = !!(filters.q || filters.category || filters.promoOnly);
  return (
    <div className="rounded-lg border border-dashed border-neutral-300 bg-neutral-50 p-8 text-center text-sm text-neutral-600">
      {hasFilter
        ? "Nic nenalezeno. Zkus jiný název, nebo ten produkt není v žádné aktuální akci."
        : "Zatím tu nic není. Spusť aktualizaci dat."}
    </div>
  );
}

function pluralise(n: number, forms: [string, string, string]) {
  if (n === 1) return forms[0];
  if (n >= 2 && n <= 4) return forms[1];
  return forms[2];
}
