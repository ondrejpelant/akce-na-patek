import type { PricePoint } from "@/lib/queries";
import { formatCzk } from "@/lib/format";

const W = 320;
const H = 64;
const PAD = 4;

const DAY = new Intl.DateTimeFormat("cs-CZ", { day: "numeric", month: "numeric" });

/** Step line of the lowest daily price. Hidden until there are 2+ days. */
export default function PriceSparkline({ points }: { points: PricePoint[] }) {
  if (points.length < 2) return null;

  const prices = points.map((p) => p.price);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const span = max - min || 1;
  const x = (i: number) => PAD + (i / (points.length - 1)) * (W - 2 * PAD);
  const y = (v: number) => (max === min ? H / 2 : PAD + (1 - (v - min) / span) * (H - 2 * PAD));

  // Prices change in steps (one SCD2 row per change), so draw horizontal
  // then vertical segments rather than a smoothed line.
  let d = `M ${x(0)} ${y(prices[0])}`;
  for (let i = 1; i < points.length; i++) {
    d += ` H ${x(i)} V ${y(prices[i])}`;
  }

  const last = points[points.length - 1];
  const first = points[0];
  const label = `Nejnižší cena za posledních ${points.length} dní: od ${formatCzk(min)} do ${formatCzk(max)}`;

  return (
    <figure className="space-y-1">
      <figcaption className="flex items-baseline justify-between text-xs text-neutral-500">
        <span>Vývoj nejnižší ceny</span>
        <span>
          min {formatCzk(min)} · max {formatCzk(max)}
        </span>
      </figcaption>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="h-16 w-full"
        role="img"
        aria-label={label}
        preserveAspectRatio="none"
      >
        <path
          d={d}
          fill="none"
          stroke="#be123c"
          strokeWidth="2"
          strokeLinejoin="round"
          vectorEffect="non-scaling-stroke"
        />
        <circle cx={x(points.length - 1)} cy={y(last.price)} r="3" fill="#be123c" />
      </svg>
      <div className="flex justify-between text-[11px] text-neutral-400">
        <span>{DAY.format(new Date(first.day))}</span>
        <span>{DAY.format(new Date(last.day))}</span>
      </div>
    </figure>
  );
}
