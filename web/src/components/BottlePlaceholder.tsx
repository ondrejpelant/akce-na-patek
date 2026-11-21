import type { CategorySlug } from "@/lib/categories";

type Props = {
  category?: CategorySlug;
  className?: string;
};

// Simple monochrome bottle outline per category. Colour tints kept within the
// same family so grids stay calm. Fill colours are CSS-variable-safe for dark
// mode later (M6).
const TINTS: Record<CategorySlug, string> = {
  rum: "#92400e",
  vodka: "#0369a1",
  gin: "#0f766e",
  whisky: "#b45309",
  brandy: "#9a3412",
  likery: "#be185d",
  bylinne: "#15803d",
  palenky: "#854d0e",
  tequila: "#ca8a04",
  ostatni: "#525252",
};

export default function BottlePlaceholder({ category, className }: Props) {
  const tint = category ? TINTS[category] : TINTS.ostatni;

  return (
    <svg
      viewBox="0 0 120 180"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Obrázek lahve"
      className={className}
    >
      <rect width="120" height="180" fill="#f5f5f5" />
      {/* neck */}
      <rect x="52" y="20" width="16" height="22" fill={tint} opacity="0.9" />
      {/* collar */}
      <rect x="48" y="38" width="24" height="8" fill={tint} />
      {/* body */}
      <path
        d="M44 54 Q44 46 60 46 Q76 46 76 54 L82 70 Q86 80 86 100 L86 158 Q86 166 78 166 L42 166 Q34 166 34 158 L34 100 Q34 80 38 70 Z"
        fill={tint}
        opacity="0.85"
      />
      {/* label */}
      <rect x="40" y="100" width="40" height="38" fill="#fafafa" opacity="0.95" />
    </svg>
  );
}
