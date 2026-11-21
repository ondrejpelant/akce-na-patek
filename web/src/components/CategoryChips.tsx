import Link from "next/link";
import { CATEGORIES, type CategorySlug } from "@/lib/categories";

type Props = {
  active: CategorySlug | null;
  params: URLSearchParams;
};

function withCategory(params: URLSearchParams, slug: CategorySlug | null): string {
  const next = new URLSearchParams(params.toString());
  if (slug) next.set("cat", slug);
  else next.delete("cat");
  next.delete("page");
  const s = next.toString();
  return s ? `/?${s}` : "/";
}

export default function CategoryChips({ active, params }: Props) {
  return (
    <div className="-mx-4 overflow-x-auto px-4">
      <div className="flex min-w-max gap-2 py-1">
        <Chip href={withCategory(params, null)} active={active === null}>
          Vše
        </Chip>
        {CATEGORIES.map((c) => (
          <Chip key={c.slug} href={withCategory(params, c.slug)} active={active === c.slug}>
            {c.name}
          </Chip>
        ))}
      </div>
    </div>
  );
}

function Chip({
  href,
  active,
  children,
}: {
  href: string;
  active: boolean;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      scroll={false}
      className={
        active
          ? "rounded-full bg-neutral-900 px-3 py-1 text-sm font-medium text-white"
          : "rounded-full border border-neutral-300 bg-white px-3 py-1 text-sm text-neutral-800 hover:border-neutral-500"
      }
    >
      {children}
    </Link>
  );
}
