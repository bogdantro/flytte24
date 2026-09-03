"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { Logo } from "./Logo";
import { MobileMenu, type NavLink } from "./MobileMenu";

const NAV_LINKS: NavLink[] = [
  { href: "/blogg", label: "Blogg" },
  { href: "/byraer", label: "Byråer" },
  { href: "/partner", label: "For flyttebyråer" },
];

export function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={cn(
        "sticky top-0 z-40 px-6 transition-colors sm:px-10",
        scrolled ? "bg-bg/85 backdrop-blur-md" : "bg-transparent",
      )}
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between py-4">
        <Link href="/" aria-label="Kobly hjem" className="no-underline">
          <Logo />
        </Link>
        <button
          type="button"
          aria-label="Meny"
          onClick={() => setMenuOpen(true)}
          className="rounded-full px-4 py-2 text-sm font-medium text-ink transition-colors hover:bg-ink/5 lg:hidden"
        >
          Meny
        </button>
        <nav className="hidden items-center gap-2 lg:flex">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="inline-flex items-center rounded-full px-4 py-2 text-sm font-medium text-ink transition-colors hover:bg-ink/5"
            >
              {link.label}
            </Link>
          ))}
          <Link
            href="/wizard"
            className="inline-flex items-center rounded-full bg-brand px-4 py-2 text-sm font-medium text-brand-ink transition-colors hover:bg-brand/90"
          >
            Få 3 tilbud gratis
          </Link>
        </nav>
      </div>
      <MobileMenu
        open={menuOpen}
        onClose={() => setMenuOpen(false)}
        links={NAV_LINKS}
      />
    </header>
  );
}
