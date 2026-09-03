import Image from "next/image";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

function NumberBadge({ n }: { n: number }) {
  return (
    <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-brand text-sm font-semibold text-brand-ink">
      {n}
    </span>
  );
}

const steps = [
  {
    n: 1,
    title: "Fyll ut skjema",
    body: "Svar på noen enkle spørsmål. Tar under to minutter.",
    art: "/images/howitworks-1-skjema.png",
    artW: 1102,
    artH: 1036,
  },
  {
    n: 2,
    title: "Vi kobler deg med de beste",
    body: "Tre kvalitetssjekkede byråer kobles med din flytting.",
    art: "/images/howitworks-2-match.png",
    artW: 730,
    artH: 694,
  },
  {
    n: 3,
    title: "Velg tilbud",
    body: "Sammenlign, velg ditt byrå, og avtal resten direkte med dem.",
    art: "/images/howitworks-3-velg.png",
    artW: 1698,
    artH: 1556,
  },
];

export function HowItWorks() {
  return (
    <section className="px-6 py-20 sm:px-10 sm:py-28 lg:py-40">
      <div className="mx-auto max-w-6xl">
        <h2 className="text-3xl font-semibold text-ink sm:text-[42px] sm:leading-[1.1] lg:text-center">
          Slik fungerer det
        </h2>
        <ol className="mt-10 grid gap-4 sm:mt-14 md:grid-cols-3 md:gap-6">
          {steps.map((step) => (
            <li
              key={step.n}
              className="relative flex flex-col rounded-[14px] bg-surface-soft p-6 sm:p-7 lg:aspect-[4/5] lg:p-8"
            >
              <span className="absolute left-6 top-6 inline-flex lg:left-8 lg:top-8">
                <NumberBadge n={step.n} />
              </span>

              <div className="flex items-center justify-center pt-10 lg:flex-1 lg:pt-0">
                <Image
                  src={step.art}
                  alt=""
                  aria-hidden
                  width={step.artW}
                  height={step.artH}
                  className="h-auto w-full max-w-[140px] object-contain mix-blend-multiply lg:max-w-[200px]"
                />
              </div>

              <div className="mt-6 lg:mt-0 lg:flex lg:min-h-[150px] lg:flex-col lg:justify-start">
                <h3 className="text-2xl font-semibold tracking-tight text-ink lg:text-[28px] lg:leading-tight">
                  {step.title}
                </h3>
                <p className="mt-3 text-base text-ink-muted">
                  {step.body}
                </p>
              </div>
            </li>
          ))}
        </ol>
        <div className="mt-12 flex justify-center sm:mt-16">
          <Link
            href="/wizard"
            className="inline-flex items-center gap-2 rounded-full bg-brand px-7 py-4 text-base font-medium text-brand-ink transition-colors hover:bg-brand/90"
          >
            Få 3 tilbud gratis
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </section>
  );
}
