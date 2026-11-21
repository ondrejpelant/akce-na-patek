import { renderAppIcon } from "@/lib/appIcon";

const VARIANTS: Record<string, { size: number; maskable: boolean }> = {
  "192": { size: 192, maskable: false },
  "512": { size: 512, maskable: false },
  "maskable-512": { size: 512, maskable: true },
};

export function generateStaticParams() {
  return Object.keys(VARIANTS).map((variant) => ({ variant }));
}

export async function GET(_req: Request, { params }: RouteContext<"/pwa-icon/[variant]">) {
  const { variant } = await params;
  const v = VARIANTS[variant];
  if (!v) return new Response("Not found", { status: 404 });
  return renderAppIcon(v.size, { maskable: v.maskable });
}
