import { fetchFreshness } from "@/lib/queries";
import { relativeTimeSince } from "@/lib/format";

const STALE_AFTER_HOURS = 48;

export default async function FreshnessBanner() {
  let newest: Date | null = null;
  try {
    const f = await fetchFreshness();
    newest = f.newest;
  } catch {
    // DB unreachable (e.g. local dev without .env.local) — stay silent.
    return null;
  }

  if (!newest) {
    return (
      <div className="border-b border-amber-200 bg-amber-50 px-4 py-1.5 text-center text-xs text-amber-900">
        Zatím nejsou žádná data. Spusť aktualizaci.
      </div>
    );
  }

  // Server component is already dynamic (reads Neon); time at request time is fine here.
  // eslint-disable-next-line react-hooks/purity
  const now = Date.now();
  const stale = (now - newest.getTime()) / 3_600_000 > STALE_AFTER_HOURS;

  return (
    <div
      className={
        stale
          ? "border-b border-amber-200 bg-amber-50 px-4 py-1.5 text-center text-xs text-amber-900"
          : "border-b border-neutral-100 bg-neutral-50 px-4 py-1.5 text-center text-xs text-neutral-600"
      }
    >
      Data {relativeTimeSince(newest)}
      {stale && " — spusť aktualizaci"}
    </div>
  );
}
