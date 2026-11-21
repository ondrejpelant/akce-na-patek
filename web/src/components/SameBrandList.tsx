import Link from "next/link";
import BottlePlaceholder from "./BottlePlaceholder";
import LoyaltyBadge from "./LoyaltyBadge";
import type { RelatedProduct } from "@/lib/queries";
import { formatCzk, formatPricePerL, formatVolume, sizedImage } from "@/lib/format";

export default function SameBrandList({
  brand,
  items,
}: {
  brand: string;
  items: RelatedProduct[];
}) {
  if (items.length === 0) return null;

  return (
    <section className="space-y-2">
      <h2 className="text-sm font-semibold text-neutral-800">Další {brand} v obchodech</h2>
      <ul className="divide-y divide-neutral-200 overflow-hidden rounded-lg border border-neutral-200 bg-white">
        {items.map((p) => (
          <li key={p.slug}>
            <Link href={`/p/${p.slug}`} className="flex items-center gap-3 p-2 hover:bg-neutral-50">
              <div className="h-12 w-12 shrink-0 overflow-hidden rounded bg-white">
                {p.image_url ? (
                  /* eslint-disable-next-line @next/next/no-img-element */
                  <img
                    src={sizedImage(p.image_url, 120)}
                    alt=""
                    loading="lazy"
                    referrerPolicy="no-referrer"
                    className="h-full w-full object-contain"
                  />
                ) : (
                  <BottlePlaceholder className="h-full w-full" />
                )}
              </div>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm text-neutral-900">
                  {p.brand} {p.name}
                </div>
                <div className="truncate text-xs text-neutral-500">
                  {formatVolume(p.volume_ml)} · {p.stores.join(", ")}
                </div>
              </div>
              <div className="shrink-0 text-right">
                <div
                  className={`text-sm font-semibold ${
                    p.best_price_type === "loyalty"
                      ? "text-violet-700"
                      : p.best_price_type === "promo"
                        ? "text-rose-700"
                        : "text-neutral-900"
                  }`}
                >
                  {formatCzk(p.best_price)}
                  {p.best_price_type === "loyalty" && <LoyaltyBadge loyaltyName={null} />}
                </div>
                <div className="text-[11px] text-neutral-500">{formatPricePerL(p.price_per_l)}</div>
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
