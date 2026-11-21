import Link from "next/link";
import { notFound } from "next/navigation";
import BottlePlaceholder from "@/components/BottlePlaceholder";
import LoyaltyBadge from "@/components/LoyaltyBadge";
import PriceSparkline from "@/components/PriceSparkline";
import SameBrandList from "@/components/SameBrandList";
import {
  fetchActiveStoreNames,
  fetchOffers,
  fetchPriceHistory,
  fetchProduct,
  fetchSameBrand,
  type StoreOffer,
} from "@/lib/queries";
import { CATEGORY_NAMES } from "@/lib/categories";
import {
  discountPercent,
  formatCzk,
  formatObservedDate,
  formatPromoTo,
  formatVolume,
  relativeTimeSince,
  sizedImage,
} from "@/lib/format";

export const instant = false;

const STALE_AFTER_MS = 2 * 24 * 3_600_000;

export default async function ProductPage({ params }: PageProps<"/p/[slug]">) {
  const { slug } = await params;
  // Rendered per request (reads live DB), so request time is the right "now".
  // eslint-disable-next-line react-hooks/purity
  const now = Date.now();
  const product = await fetchProduct(slug);
  if (!product) notFound();

  const [offers, history, stores, sameBrand] = await Promise.all([
    fetchOffers(product.id),
    fetchPriceHistory(product.id),
    fetchActiveStoreNames(),
    fetchSameBrand(product.id, product.brand),
  ]);
  const lowest = offers[0];
  const storesWithPrice = new Set(offers.map((o) => o.store_id));
  const storesWithout = stores.filter((s) => !storesWithPrice.has(s.id)).map((s) => s.name);

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <Link href="/" className="text-sm text-neutral-600 hover:text-neutral-900">
        ← Zpět
      </Link>

      <div className="space-y-3">
        <div className="mx-auto aspect-square w-full max-w-xs overflow-hidden rounded-lg bg-white">
          {product.image_url ? (
            /* eslint-disable-next-line @next/next/no-img-element */
            <img
              src={sizedImage(product.image_url, 600)}
              alt={`${product.brand} ${product.name}`}
              referrerPolicy="no-referrer"
              className="h-full w-full object-contain p-2"
            />
          ) : (
            <BottlePlaceholder category={product.category_slug} className="h-full w-full" />
          )}
        </div>
        <div>
          <h1 className="text-xl font-semibold leading-tight">
            {product.brand} {product.name}
          </h1>
          <div className="mt-1 text-sm text-neutral-600">
            {formatVolume(product.volume_ml)}
            {product.abv != null && ` · ${product.abv} %`}
            {` · ${CATEGORY_NAMES[product.category_slug]}`}
          </div>
          {lowest && (
            <div className="mt-3 text-sm text-neutral-600">
              Nejlevněji dnes:{" "}
              <span className="font-semibold text-neutral-900">
                {formatCzk(lowest.price_czk)}
              </span>{" "}
              v{" "}
              <span className="font-semibold capitalize text-neutral-900">
                {lowest.name}
              </span>
              {lowest.price_type === "loyalty" && (
                <LoyaltyBadge loyaltyName={lowest.loyalty_name} />
              )}
            </div>
          )}
        </div>
      </div>

      {offers.length === 0 ? (
        <div className="rounded-lg border border-dashed border-neutral-300 bg-neutral-50 p-8 text-center text-sm text-neutral-600">
          Žádný obchod zatím cenu nenabízí.
        </div>
      ) : (
        <ul className="divide-y divide-neutral-200 overflow-hidden rounded-lg border border-neutral-200 bg-white">
          {offers.map((offer, idx) => (
            <OfferRow
              key={`${offer.store_id}-${offer.price_type}`}
              offer={offer}
              highlighted={idx === 0}
              now={now}
            />
          ))}
        </ul>
      )}

      {storesWithout.length > 0 && (
        <p className="text-xs text-neutral-500">
          Bez ceny: {storesWithout.join(", ")} — tento produkt jsme v jejich nabídce zatím
          neviděli (nebo jejich ceny nestahujeme).
        </p>
      )}

      <SameBrandList brand={product.brand} items={sameBrand} />

      <PriceSparkline points={history} />

      {offers.length > 0 && (
        <p className="text-center text-xs text-neutral-500">
          Aktualizováno {relativeTimeSince(new Date(offers[0].observed_at))} · ceny bez záruky
        </p>
      )}
    </div>
  );
}

function OfferRow({
  offer,
  highlighted,
  now,
}: {
  offer: StoreOffer;
  highlighted: boolean;
  now: number;
}) {
  const discount = discountPercent(offer.price_czk, offer.regular_czk);
  const promoLabel = formatPromoTo(offer.promo_to);
  const isLoyalty = offer.price_type === "loyalty";

  const priceClass = isLoyalty
    ? "text-violet-700"
    : offer.price_type === "promo"
      ? "text-rose-700"
      : "text-neutral-900";

  const subtitle =
    offer.price_type === "regular"
      ? offer.price_source === "leaflet_regular"
        ? `Běžná cena (z letáku, k ${formatObservedDate(offer.observed_at)})`
        : offer.price_source === "manual"
          ? "Běžná cena (ruční zápis)"
          : "Běžná cena"
      : isLoyalty
        ? `${offer.loyalty_name ?? "Věrnostní karta"}${promoLabel ? ` · ${promoLabel}` : ""}`
        : promoLabel
          ? `Akce · ${promoLabel}`
          : "Akce";
  // Tesco is refreshed one listing per run, so its prices can be days old.
  const observed = new Date(offer.observed_at);
  const showObserved =
    offer.price_source !== "leaflet_regular" &&
    now - observed.getTime() > STALE_AFTER_MS;
  const fullSubtitle = showObserved
    ? `${subtitle} · ověřeno ${formatObservedDate(offer.observed_at)}`
    : subtitle;

  const content = (
    <div className={`flex items-center justify-between gap-3 p-3 ${highlighted ? "bg-amber-50" : ""}`}>
      <div className="min-w-0">
        <div className="font-medium capitalize text-neutral-900">{offer.name}</div>
        <div className="text-xs text-neutral-600">{fullSubtitle}</div>
      </div>
      <div className="flex shrink-0 flex-col items-end">
        <div className={`text-base font-bold ${priceClass}`}>
          {formatCzk(offer.price_czk)}
          {isLoyalty && <LoyaltyBadge loyaltyName={offer.loyalty_name} />}
        </div>
        {discount != null && offer.regular_czk != null && (
          <div className="text-xs text-neutral-500">
            <s>{formatCzk(offer.regular_czk)}</s> · {discount} %
          </div>
        )}
      </div>
    </div>
  );

  return (
    <li>
      {offer.url ? (
        <a href={offer.url} target="_blank" rel="noopener noreferrer" className="block hover:bg-neutral-50">
          {content}
        </a>
      ) : (
        content
      )}
    </li>
  );
}
