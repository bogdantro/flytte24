import Link from "next/link";
import { ArrowRight, Mail } from "lucide-react";
import { Logo } from "./Logo";

export function Footer() {
  return (
    <footer className="relative overflow-hidden bg-brand text-brand-ink">
      <div className="mx-auto max-w-6xl px-6 pt-16 pb-8 sm:px-10 sm:pt-20 sm:pb-12 lg:pt-24">
        <div className="flex flex-col gap-10 lg:flex-row lg:items-start lg:justify-between lg:gap-16">
          <div className="max-w-md">
            <Logo tone="brand-ink" />
            <p className="mt-4 text-sm leading-relaxed text-brand-ink/70 sm:text-base">
              Vi finner det beste flyttebyrået for deg. Kobly kobler
              privatpersoner med kvalitetssjekkede byråer i hele Norge.
            </p>
            <Link
              href="/email-preview"
              className="mt-8 inline-flex items-center gap-2 rounded-full px-4 py-2.5 text-sm font-medium text-brand-ink/80 ring-1 ring-brand-ink/20 transition-colors hover:bg-brand-ink/10 hover:text-brand-ink"
            >
              <Mail className="h-4 w-4" />
              E-post
            </Link>
            <p className="mt-8 text-xs text-brand-ink/40">
              Kobly AS · © 2026
            </p>
          </div>
          <div className="rounded-[14px] bg-brand-ink/[0.06] p-6 ring-1 ring-brand-ink/15 lg:max-w-sm lg:p-8">
            <p className="text-lg text-brand-ink sm:text-xl">
              Klar for å flytte?
            </p>
            <p className="mt-2 text-sm text-brand-ink/60">
              Tre uforpliktende tilbud på under to minutter.
            </p>
            <Link
              href="/wizard"
              className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-full bg-brand-ink px-5 py-3 text-sm font-medium text-ink transition-colors hover:bg-brand-ink/90"
            >
              Få 3 tilbud gratis
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </div>
      <div
        aria-hidden
        className="select-none overflow-hidden pb-0"
      >
        <p
          className="block w-full text-center font-semibold leading-[0.85] tracking-[-0.04em] text-brand-ink/[0.08]"
          style={{ fontSize: "clamp(6rem, 28vw, 24rem)" }}
        >
          kobly
        </p>
      </div>
    </footer>
  );
}
