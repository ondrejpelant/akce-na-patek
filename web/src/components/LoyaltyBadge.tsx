/**
 * Jednoduché označení věrnostní ceny.
 * Fáze 2 vymění za popover s vysvětlením (viz 06 Frontend/UI specifikace.md).
 */
export default function LoyaltyBadge({ loyaltyName }: { loyaltyName: string | null }) {
  return (
    <span
      className="ml-1 inline-flex h-4 w-4 items-center justify-center rounded-full border border-violet-400 text-[10px] font-semibold text-violet-700"
      aria-label={
        loyaltyName
          ? `Cena platí jen s věrnostní kartou ${loyaltyName}`
          : "Cena platí jen s věrnostní kartou"
      }
      title={
        loyaltyName
          ? `Cena platí jen s věrnostní kartou ${loyaltyName}`
          : "Cena platí jen s věrnostní kartou"
      }
    >
      i
    </span>
  );
}
