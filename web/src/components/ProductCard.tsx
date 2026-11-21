import Link from "next/link";
import BottlePlaceholder from "./BottlePlaceholder";
import LoyaltyBadge from "./LoyaltyBadge";
import type { ProductCard as Card } from "@/lib/queries";
import {
  discountPercent,
  formatCzk,
  formatPricePerL,
  formatPromoTo,
  formatVolume,
  sizedImage,
} from "@/lib/format";

export default function ProductCard({ card }: { card: Card }) {
  const discount = discountPercent(card.best_price, card.regular_czk);
  const isLoyalty = card.best_price_type === "loyalty";
  const priceTone = isLoyalty
    ? "text-violet-700"
    : card.best_price_type === "promo"
      ? "text-rose-700"
      : "text-neutral-900";

  const promoLabel = formatPromoTo(card.promo_to);

  return (
    <Link
      href={`/p/${card.slug}`}
      className="group flex flex-col gap-1 rounded-lg border border-neutral-200 bg-white p-2 transition hover:shadow-sm"
    >
      <div className="relative aspect-square overflow-hidden rounded-md bg-neutral-50">
        {discount != null && (
          <span className="absolute left-1.5 top-1.5 rounded bg-rose-600 px-1.5 py-0.5 text-xs font-semibold text-white">
            {discount} %
          </span>
        )}
        {card.image_url ? (
          /* eslint-disable-next-line @next/next/no-img-element */
          <img
            src={sizedImage(card.image_url, 300)}
            alt=""
            loading="lazy"
            referrerPolicy="no-referrer"
            className="h-full w-full object-contain p-2"
          />
        ) : (
          <BottlePlaceholder category={card.category_slug} className="h-full w-full" />
        )}
      </div>

      <div className={`text-base font-bold leading-tight ${priceTone}`}>
        {formatCzk(card.best_price)}
        {isLoyalty && <LoyaltyBadge loyaltyName={card.best_loyalty_name} />}
      </div>

      <div className="text-xs text-neutral-700">
        <span className="font-medium capitalize">{card.best_store}</span>
        {promoLabel && <span className="text-neutral-500"> · {promoLabel}</span>}
      </div>

      <div className="truncate text-sm text-neutral-800">
        {card.brand} {card.name}
      </div>

      <div className="text-xs text-neutral-500">
        {formatVolume(card.volume_ml)} · {formatPricePerL(card.price_per_l)}
        {card.store_count > 1 && ` · ${card.store_count} obch.`}
      </div>
    </Link>
  );
}
