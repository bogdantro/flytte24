import Link from "next/link";
import { ArrowRight } from "lucide-react";

export function PartnerCTA() {
  return (
    <section
      id="bli-partner"
      className="px-6 py-20 sm:px-10 sm:py-28 lg:py-40"
    >
      <div className="mx-auto max-w-6xl">
        <div className="rounded-[14px] bg-surface-soft px-8 py-14 ring-1 ring-line sm:px-12 sm:py-16 lg:px-16 lg:py-20">
          <div className="flex flex-col items-start gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-2xl">
              <h2 className="text-3xl font-semibold leading-[1.1] text-ink sm:text-4xl lg:text-[44px]">
                Bli en av Norges
                <br className="hidden lg:inline" /> mest foretrukne byråer
              </h2>
              <p className="mt-4 text-base text-ink-muted sm:text-lg">
                Søk om partnerskap i dag. Vi tar kontakt innen kort tid for å
                vurdere søknaden.
              </p>
            </div>
            <Link
              href="mailto:partner@kobly.no?subject=Søknad om partnerskap"
              className="inline-flex items-center gap-2 rounded-full bg-brand px-6 py-4 text-base font-medium text-brand-ink transition-colors hover:bg-brand/90"
            >
              Send søknad
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
