import Link from "next/link";
import { notFound } from "next/navigation";
import BottlePlaceholder from "@/components/BottlePlaceholder";
import LoyaltyBadge from "@/components/LoyaltyBadge";
import PriceSparkline from "@/components/PriceSparkline";
import { fetchOffers, fetchPriceHistory, fetchProduct, type StoreOffer } from "@/lib/queries";
import { CATEGORY_NAMES } from "@/lib/categories";
import {
  discountPercent,
  formatCzk,
  formatObservedDate,
  formatPromoTo,
  formatVolume,
  relativeTimeSince,
} from "@/lib/format";

export const instant = false;

export default async function ProductPage({ params }: PageProps<"/p/[slug]">) {
  const { slug } = await params;
  const product = await fetchProduct(slug);
  if (!product) notFound();

  const [offers, history] = await Promise.all([
    fetchOffers(product.id),
    fetchPriceHistory(product.id),
  ]);
  const lowest = offers[0];

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <Link href="/" className="text-sm text-neutral-600 hover:text-neutral-900">
        ← Zpět
      </Link>

      <div className="flex gap-4">
        <div className="h-32 w-32 shrink-0 overflow-hidden rounded-lg bg-neutral-50 sm:h-40 sm:w-40">
          {product.image_url ? (
            /* eslint-disable-next-line @next/next/no-img-element */
            <img
              src={product.image_url}
              alt=""
              className="h-full w-full object-contain p-3"
            />
          ) : (
            <BottlePlaceholder category={product.category_slug} className="h-full w-full" />
          )}
        </div>
        <div className="flex flex-1 flex-col justify-center">
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
            <OfferRow key={offer.store_id} offer={offer} highlighted={idx === 0} />
          ))}
        </ul>
      )}

      <PriceSparkline points={history} />

      {offers.length > 0 && (
        <p className="text-center text-xs text-neutral-500">
          Aktualizováno {relativeTimeSince(new Date(offers[0].observed_at))} · ceny bez záruky
        </p>
      )}
    </div>
  );
}

function OfferRow({ offer, highlighted }: { offer: StoreOffer; highlighted: boolean }) {
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

  const content = (
    <div className={`flex items-center justify-between gap-3 p-3 ${highlighted ? "bg-amber-50" : ""}`}>
      <div className="min-w-0">
        <div className="font-medium capitalize text-neutral-900">{offer.name}</div>
        <div className="text-xs text-neutral-600">{subtitle}</div>
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
