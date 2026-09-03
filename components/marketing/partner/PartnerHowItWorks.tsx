function StepNumber({ n }: { n: number }) {
  return (
    <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-brand text-sm font-semibold text-brand-ink">
      {n}
    </span>
  );
}

const steps = [
  {
    n: 1,
    title: "Søk om partnerskap",
    body: "Fyll ut en kort søknad om bedriften din — område, kapasitet og dokumentasjon. Vi vurderer søknaden innen få dager.",
  },
  {
    n: 2,
    title: "Få leads automatisk",
    body: "Vi sender deg forespørsler som matcher kapasiteten din. Hver forespørsel inneholder fra-/til-adresse, beskrivelse og bilder.",
  },
  {
    n: 3,
    title: "Vinn jobber, betal per kontrakt",
    body: "Send tilbud direkte i systemet. Når kunden velger deg, betaler du en liten andel av jobben — ellers ingenting.",
  },
];

export function PartnerHowItWorks() {
  return (
    <section
      id="hvordan"
      className="px-6 py-20 sm:px-10 sm:py-28 lg:py-40"
    >
      <div className="mx-auto max-w-6xl">
        <h2 className="text-3xl font-semibold leading-[1.1] text-ink sm:text-[42px] lg:text-center">
          Slik fungerer det
        </h2>
        <ol className="mt-10 grid gap-4 sm:mt-14 md:grid-cols-3 md:gap-6">
          {steps.map((step) => (
            <li
              key={step.n}
              className="relative flex flex-col rounded-[14px] bg-surface-soft p-6 sm:p-7 lg:aspect-[4/5] lg:p-8"
            >
              <span className="lg:absolute lg:top-8 lg:left-8">
                <StepNumber n={step.n} />
              </span>
              <div className="mt-6 lg:mt-auto">
                <h3 className="text-2xl font-semibold tracking-tight text-ink lg:text-[28px] lg:leading-tight">
                  {step.title}
                </h3>
                <p className="mt-3 text-base text-ink-muted">{step.body}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
