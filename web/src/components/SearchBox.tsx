"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

const DEBOUNCE_MS = 300;

export default function SearchBox() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  // Mount-time init: if the user later navigates back/forward or clears the
  // search from elsewhere, the input shows the stale local value until next
  // keystroke — acceptable trade-off (there is no "clear search" UI anyway).
  const [value, setValue] = useState(() => params.get("q") ?? "");

  // Debounced push to URL — server component re-renders on URL change.
  useEffect(() => {
    const t = setTimeout(() => {
      const current = params.get("q") ?? "";
      if (value === current) return;
      const next = new URLSearchParams(params.toString());
      if (value.trim()) {
        next.set("q", value.trim());
      } else {
        next.delete("q");
      }
      next.delete("page"); // reset pagination on new search
      router.replace(`${pathname}?${next.toString()}`, { scroll: false });
    }, DEBOUNCE_MS);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return (
    <div className="relative">
      <input
        type="search"
        inputMode="search"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Hledat (finlandia, koňak…)"
        aria-label="Hledat"
        className="w-full rounded-lg border border-neutral-300 bg-white px-9 py-2 text-base outline-none focus:border-neutral-500"
      />
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        className="pointer-events-none absolute left-2.5 top-2.5 h-5 w-5 text-neutral-400"
        aria-hidden="true"
      >
        <circle cx="11" cy="11" r="7" />
        <path d="M21 21l-4.3-4.3" />
      </svg>
    </div>
  );
}
