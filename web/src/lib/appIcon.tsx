import { ImageResponse } from "next/og";

export const APP_COLOR = "#be123c";

/**
 * App icon: white bottle (same outline as BottlePlaceholder) on the brand
 * rose. `maskable` keeps the bottle inside the 80 % safe zone Android crops to.
 */
export function renderAppIcon(size: number, { maskable = false } = {}) {
  const inner = Math.round(size * (maskable ? 0.6 : 0.78));
  const radius = maskable ? 0 : Math.round(size * 0.22);

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: APP_COLOR,
          borderRadius: radius,
        }}
      >
        <svg width={inner} height={inner} viewBox="0 0 120 180">
          <rect x="52" y="20" width="16" height="22" fill="#ffffff" />
          <rect x="48" y="38" width="24" height="8" fill="#ffffff" />
          <path
            d="M44 54 Q44 46 60 46 Q76 46 76 54 L82 70 Q86 80 86 100 L86 158 Q86 166 78 166 L42 166 Q34 166 34 158 L34 100 Q34 80 38 70 Z"
            fill="#ffffff"
          />
          <rect x="40" y="100" width="40" height="38" fill={APP_COLOR} />
        </svg>
      </div>
    ),
    { width: size, height: size },
  );
}
