"use client";

import Link from "next/link";
import { ArrowRight, X } from "lucide-react";
import { Logo } from "./Logo";
import { FullscreenOverlay } from "./FullscreenOverlay";

export type NavLink = { href: string; label: string };

export function MobileMenu({
  open,
  onClose,
  links,
}: {
  open: boolean;
  onClose: () => void;
  links: NavLink[];
}) {
  return (
    <FullscreenOverlay open={open} onClose={onClose} label="Meny">
      <div className="flex items-center justify-between px-6 py-4 sm:px-10">
        <Link href="/" aria-label="Kobly hjem" onClick={onClose}>
          <Logo />
        </Link>
        <button
          type="button"
          aria-label="Lukk meny"
          onClick={onClose}
          className="inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-medium text-ink transition-colors hover:bg-ink/5"
        >
          Lukk
          <X className="h-4 w-4" />
        </button>
      </div>
      <nav className="flex flex-1 flex-col justify-center px-6 sm:px-10">
        <ul className="flex flex-col gap-2">
          {links.map((link) => (
            <li key={link.href}>
              <Link
                href={link.href}
                onClick={onClose}
                className="block py-3 font-serif text-4xl font-semibold text-ink transition-colors hover:text-ink/70"
              >
                {link.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
      <div className="px-6 pb-10 sm:px-10">
        <Link
          href="/wizard"
          onClick={onClose}
          className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-brand px-7 py-4 text-base font-medium text-brand-ink transition-colors hover:bg-brand/90"
        >
          Få 3 tilbud gratis
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </FullscreenOverlay>
  );
}
