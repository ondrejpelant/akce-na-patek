"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { ChangeEvent } from "react";

const SORT_LABELS = {
  price: "Nejlevnější",
  price_per_l: "Cena za litr",
  discount: "Největší sleva",
} as const;

export default function SortAndFilter() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();

  const sort = (params.get("sort") ?? "price") as keyof typeof SORT_LABELS;
  const promo = params.get("promo") === "1";

  const update = (patch: Record<string, string | null>) => {
    const next = new URLSearchParams(params.toString());
    for (const [k, v] of Object.entries(patch)) {
      if (v == null) next.delete(k);
      else next.set(k, v);
    }
    next.delete("page");
    const s = next.toString();
    router.replace(s ? `${pathname}?${s}` : pathname, { scroll: false });
  };

  return (
    <div className="flex flex-wrap items-center gap-3 text-sm text-neutral-700">
      <label className="flex items-center gap-1.5">
        <span>Řadit:</span>
        <select
          value={sort}
          onChange={(e: ChangeEvent<HTMLSelectElement>) =>
            update({ sort: e.target.value === "price" ? null : e.target.value })
          }
          className="rounded border border-neutral-300 bg-white px-1.5 py-1"
        >
          {Object.entries(SORT_LABELS).map(([v, label]) => (
            <option key={v} value={v}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <label className="flex items-center gap-1.5">
        <input
          type="checkbox"
          checked={promo}
          onChange={(e) => update({ promo: e.target.checked ? "1" : null })}
          className="h-4 w-4 accent-rose-600"
        />
        <span>Jen akce</span>
      </label>
    </div>
  );
}
