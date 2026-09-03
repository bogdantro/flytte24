"use client";

import { useState } from "react";
import { Plus, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

const faqs = [
  {
    q: "Hva koster det å bruke Kobly?",
    a: "Det er helt gratis og uforpliktende å få tilbud gjennom Kobly. Du betaler kun for selve flyttejobben — direkte til byrået du velger.",
  },
  {
    q: "Hvor mange byråer kontaktes?",
    a: "Vi kobler deg med tre håndplukkede, kvalitetssjekkede byråer i ditt område. Slik kan du sammenligne pris og tjenester før du bestemmer deg.",
  },
  {
    q: "Hvor lang tid tar det før jeg får tilbud?",
    a: "De fleste mottar tilbud på e-post innen 24 timer etter at forespørselen er sendt inn.",
  },
  {
    q: "Hvordan velger Kobly hvilke byråer som passer for meg?",
    a: "Vi matcher basert på adresse, type flytting (privat, bedrift, internasjonal), boligtype og ønsket dato. Bare byråer med dokumentert erfaring og gode kundeanmeldelser blir koblet på.",
  },
  {
    q: "Er jeg forpliktet til å velge ett av byråene?",
    a: "Nei. Du velger selv om du vil bruke et av byråene som tar kontakt, eller takke nei. Det er helt uforpliktende.",
  },
];

export function FAQ() {
  const [open, setOpen] = useState<number | null>(null);

  return (
    <section className="px-6 py-20 sm:px-10 sm:py-28 lg:py-40">
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
                  <span
                    className={cn(
                      "inline-flex h-6 w-6 shrink-0 items-center justify-center text-ink/60 transition-transform",
                      isOpen && "rotate-180",
                    )}
                  >
                    {isOpen ? (
                      <Minus className="h-5 w-5" />
                    ) : (
                      <Plus className="h-5 w-5" />
                    )}
                  </span>
                </button>
                {isOpen ? (
                  <p className="max-w-2xl pb-6 pr-10 text-base leading-relaxed text-ink-muted">
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
