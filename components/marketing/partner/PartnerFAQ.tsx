"use client";

import { useState } from "react";
import { Plus, Minus } from "lucide-react";

const faqs = [
  {
    q: "Hva koster det å være partner?",
    a: "Det er gratis å bli partner og motta leads. Du betaler kun en liten andel per jobb du faktisk vinner — ingen oppstartskostnad eller månedsabonnement.",
  },
  {
    q: "Hvilke krav stiller dere til byråene?",
    a: "Vi krever norsk organisasjonsnummer, gyldig forsikring, dokumentert flytteerfaring og positive kundeanmeldelser. Vi følger opp kvaliteten kontinuerlig.",
  },
  {
    q: "Kan jeg si nei til en lead?",
    a: "Ja. Du ser hver forespørsel før du svarer, og kan takke nei uten konsekvenser. Du styrer selv hvor mange jobber du vil ta.",
  },
  {
    q: "Hvor mange leads kan jeg forvente?",
    a: "Det varierer med område og kapasitet. Bedrifter i Oslo, Bergen og Trondheim får i snitt 15–40 forespørsler i måneden. Vi gir deg konkrete estimater for ditt område når du søker.",
  },
  {
    q: "Hvor raskt får jeg første lead?",
    a: "Etter godkjent søknad får du tilgang til neste matching-runde. De fleste partnere mottar første forespørsel innen en uke.",
  },
];

export function PartnerFAQ() {
  const [open, setOpen] = useState<number | null>(null);

  return (
    <section className="px-6 py-20 sm:px-10 sm:py-28 lg:py-32">
      <div className="mx-auto max-w-4xl">
        <h2 className="text-3xl font-semibold leading-[1.1] text-ink sm:text-[42px]">
          Ofte stilte spørsmål
        </h2>
        <ul className="mt-10 border-t border-line sm:mt-14">
          {faqs.map((item, i) => {
            const isOpen = open === i;
            return (
              <li key={item.q} className="border-b border-line">
                <button
                  type="button"
                  onClick={() => setOpen(isOpen ? null : i)}
                  aria-expanded={isOpen}
                  className="flex w-full items-center justify-between gap-6 py-6 text-left"
                >
                  <span className="text-base font-medium text-ink sm:text-lg">
                    {item.q}
                  </span>
                  <span className="inline-flex h-6 w-6 shrink-0 items-center justify-center text-ink/60">
                    {isOpen ? (
                      <Minus className="h-5 w-5" />
                    ) : (
                      <Plus className="h-5 w-5" />
                    )}
                  </span>
                </button>
                {isOpen ? (
                  <p className="max-w-2xl pr-10 pb-6 text-base leading-relaxed text-ink-muted">
                    {item.a}
                  </p>
                ) : null}
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
