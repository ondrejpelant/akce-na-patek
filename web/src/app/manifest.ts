import type { MetadataRoute } from "next";
import { APP_COLOR } from "@/lib/appIcon";

// No service worker on purpose (06 Frontend/UI specifikace.md): the manifest
// only lets the phone add a home-screen icon that opens without browser chrome.
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Akce na pátek",
    short_name: "Akce na pátek",
    description: "Kde je dnes alkohol nejlevnější.",
    lang: "cs",
    start_url: "/",
    scope: "/",
    display: "standalone",
    background_color: "#ffffff",
    theme_color: APP_COLOR,
    icons: [
      { src: "/pwa-icon/192", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/pwa-icon/512", sizes: "512x512", type: "image/png", purpose: "any" },
      { src: "/pwa-icon/maskable-512", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
}
