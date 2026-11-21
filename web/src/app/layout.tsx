import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import { Suspense } from "react";
import FreshnessBanner from "@/components/FreshnessBanner";
import "./globals.css";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin", "latin-ext"],
});

export const metadata: Metadata = {
  title: "Akce na pátek",
  description: "Osobní srovnávač cen alkoholu v českých supermarketech.",
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="cs" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-white text-neutral-900">
        <header className="sticky top-0 z-10 border-b border-neutral-200 bg-white/90 backdrop-blur">
          <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3">
            <Link href="/" className="text-lg font-semibold">
              🍾 Akce na pátek
            </Link>
          </div>
          <Suspense fallback={null}>
            <FreshnessBanner />
          </Suspense>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-4">{children}</main>
        <footer className="border-t border-neutral-200 py-6 text-center text-xs text-neutral-500">
          Osobní nekomerční projekt. Ceny bez záruky, ověř v obchodě. Nadměrné pití škodí zdraví.
        </footer>
      </body>
    </html>
  );
}
