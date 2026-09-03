import Link from "next/link";
import { ArrowRight } from "lucide-react";

export function PartnerHero() {
  return (
    <section className="px-6 pt-8 pb-12 sm:px-10 sm:pt-12 sm:pb-16 lg:pt-28 lg:pb-32">
      <div className="mx-auto max-w-6xl">
        <div className="flex flex-col items-start text-left lg:max-w-3xl">
          <p className="text-sm font-medium tracking-[0.04em] text-ink-muted">
            For flyttebyråer
          </p>
          <h1 className="mt-3 text-balance text-[2.5rem] font-semibold leading-[1.05] text-ink sm:text-[3rem] lg:mt-4 lg:text-[3.75rem] lg:leading-[1.05] xl:text-[4.5rem]">
            Få flere kunder uten
            <br className="hidden sm:inline" /> å konkurrere på pris
          </h1>
          <p className="mt-6 max-w-2xl text-base text-ink-muted sm:text-lg">
            Kobly sender kvalitetssjekkede leads direkte til ditt byrå. Du
            velger selv hvilke jobber du tar, og betaler kun for jobbene du
            faktisk vinner.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link
              href="#bli-partner"
              className="inline-flex items-center gap-2 rounded-full bg-brand px-6 py-3.5 text-sm font-medium text-brand-ink transition-colors hover:bg-brand/90 sm:text-base"
            >
              Bli partner
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="#hvordan"
              className="inline-flex items-center rounded-full px-5 py-3.5 text-sm font-medium text-ink ring-1 ring-line transition-colors hover:bg-ink/5 sm:text-base"
            >
              Slik fungerer det
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
