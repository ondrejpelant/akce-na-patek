const CZK = new Intl.NumberFormat("cs-CZ", {
  style: "currency",
  currency: "CZK",
  maximumFractionDigits: 2,
});

const DATE_SHORT = new Intl.DateTimeFormat("cs-CZ", {
  day: "numeric",
  month: "numeric",
});

const DATE_FULL = new Intl.DateTimeFormat("cs-CZ", {
  day: "numeric",
  month: "numeric",
  year: "numeric",
});

export const formatCzk = (n: number) => CZK.format(n);

/** Ask the store CDN for a smaller rendition where it supports one.
 *  Tesco's media API takes ?w=<px>; other URLs are returned unchanged. */
export const sizedImage = (url: string, width: number): string => {
  try {
    const u = new URL(url);
    if (u.hostname === "digitalcontent.api.tesco.com") {
      u.searchParams.set("w", String(width));
      return u.toString();
    }
  } catch {
    // not a URL — fall through
  }
  return url;
};

export const formatPricePerL = (n: number) =>
  `${CZK.format(n)}/l`.replace("Kč", "Kč"); // keep as-is; separate helper makes it swappable

export const formatVolume = (ml: number): string => {
  if (ml >= 1000 && ml % 1000 === 0) return `${ml / 1000} l`;
  if (ml >= 1000) return `${(ml / 1000).toString().replace(".", ",")} l`;
  return `${ml} ml`;
};

export const formatPromoTo = (iso: string | null): string | null =>
  iso ? `do ${DATE_SHORT.format(new Date(iso))}` : null;

export const formatObservedDate = (iso: string): string =>
  DATE_FULL.format(new Date(iso));

/** Returns a signed integer percent (-25 for 25 % off). */
export const discountPercent = (
  promo: number,
  regular: number | null,
): number | null => {
  if (!regular || regular <= 0 || promo >= regular) return null;
  return -Math.round((1 - promo / regular) * 100);
};

export const relativeTimeSince = (date: Date | null): string => {
  if (!date) return "nikdy";
  const diffMs = Date.now() - date.getTime();
  const minutes = Math.round(diffMs / 60_000);
  if (minutes < 1) return "právě teď";
  if (minutes < 60) return `před ${minutes} min`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `před ${hours} h`;
  const days = Math.round(hours / 24);
  if (days < 7) return `před ${days} dny`;
  return DATE_FULL.format(date);
};
