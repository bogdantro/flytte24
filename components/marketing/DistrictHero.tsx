import Link from "next/link";
import { ArrowRight } from "lucide-react";
import type { District } from "@/lib/districts";
import { HeroCard } from "./HeroCard";

/**
 * Samme hero som bysidene, med bydelsinnhold. H1 beholder SEO-formuleringen
 * «Flyttebyrå i [Bydel] – få 3 tilbud gratis», og kartet i wizarden sentreres
 * på Oslo siden alle bydelene ligger der.
 */
export function DistrictHero({ district }: { district: District }) {
  return (
    <section className="px-6 pt-8 pb-12 sm:px-10 sm:pt-12 sm:pb-16 lg:pt-20 lg:pb-24">
      <div className="mx-auto grid max-w-6xl items-center gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:gap-16">
        <div className="flex flex-col items-start text-left">
          <p className="text-sm font-medium tracking-[0.04em] text-ink-muted">
            Flytting i {district.name}
          </p>
          <h1 className="mt-3 text-balance font-serif text-[2rem] font-semibold leading-[1.05] text-ink sm:text-[2.5rem] lg:mt-4 lg:text-[3rem] lg:leading-[1.05] xl:text-[3.5rem]">
            Flyttebyrå i {district.name} – få 3 tilbud gratis
          </h1>
          <p className="mt-6 max-w-2xl text-base text-ink-muted sm:text-lg">
            {district.lead}
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3 lg:hidden">
            <Link
              href="/wizard?by=oslo"
              className="inline-flex items-center gap-2 rounded-full bg-brand px-6 py-3.5 text-sm font-medium text-brand-ink transition-colors hover:bg-brand/90 sm:text-base"
            >
              Få 3 tilbud gratis
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/oslo"
              className="inline-flex items-center rounded-full px-5 py-3.5 text-sm font-medium text-ink ring-1 ring-line transition-colors hover:bg-ink/5 sm:text-base"
            >
              Se andre bydeler
            </Link>
          </div>
        </div>
        <div className="hidden lg:block">
          <HeroCard
            href="/wizard?by=oslo"
            body={`Vi kobler deg med 3 kvalitetssjekkede byråer som jobber i ${district.name}.`}
          />
        </div>
      </div>
    </section>
  );
}
