"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function SiteHeader() {
  const pathname = usePathname();

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-rule">
      <Link
        href="/"
        aria-label="trawler, back to the field"
        onClick={(event) => {
          // The result state lives on "/", so a same-route Link is a no-op.
          // Dispatch a reset instead of letting the router ignore the click.
          if (pathname === "/") {
            event.preventDefault();
            window.dispatchEvent(new Event("trawler:reset"));
            window.scrollTo({ top: 0, behavior: "smooth" });
          }
        }}
        className="wordmark text-xl"
      >
        trawler<span className="text-signal">.</span>
      </Link>

      <nav className="flex items-center gap-6 text-sm">
        <Link
          href="/supported-sites"
          className={`transition-colors hover:text-ink ${
            pathname === "/supported-sites" ? "text-ink" : "text-muted"
          }`}
        >
          Supported sites
        </Link>
      </nav>
    </header>
  );
}
