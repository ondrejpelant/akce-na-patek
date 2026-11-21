import { renderAppIcon } from "@/lib/appIcon";

export const size = { width: 180, height: 180 };
export const contentType = "image/png";

// iOS applies its own rounded mask, so render a full-bleed square.
export default function AppleIcon() {
  return renderAppIcon(size.width, { maskable: true });
}
