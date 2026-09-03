import { CircleCheck, Filter, Wallet, Sparkles } from "lucide-react";

const props = [
  {
    icon: Filter,
    title: "Forhåndskvalifiserte leads",
    body: "Vi spør kunden om alt: adresse, type flytting, boligtype, dato og volum. Du får kun forespørsler som matcher området og kapasiteten din.",
  },
  {
    icon: Wallet,
    title: "Pay-per-job",
    body: "Ingen fastpris, ingen forpliktelser. Du betaler kun en liten andel per jobb du faktisk vinner. Ingen vinst, ingen kostnad.",
  },
  {
    icon: CircleCheck,
    title: "Du velger jobbene",
    body: "Se forespørselen, og takk ja eller nei. Ingen krav om å takke ja til alt — du styrer kapasiteten selv.",
  },
  {
    icon: Sparkles,
    title: "Bygg omdømme",
    body: "Hver jobb gir deg en mulighet til å samle anmeldelser. Gode tilbakemeldinger gjør at du blir foretrukket i fremtidige matchinger.",
  },
];

export function PartnerValueProps() {
  return (
    <section className="px-6 py-20 sm:px-10 sm:py-28 lg:py-32">
      <div className="mx-auto max-w-6xl">
        <h2 className="max-w-2xl text-3xl font-semibold leading-[1.1] text-ink sm:text-[42px]">
          Vi gjør det enkelt å vokse
        </h2>
        <div className="mt-10 grid gap-4 sm:mt-14 md:grid-cols-2 md:gap-6">
          {props.map((p) => (
            <article
              key={p.title}
              className="flex flex-col rounded-[14px] bg-surface-soft p-6 ring-1 ring-line sm:p-7 lg:p-8"
            >
              <span className="inline-flex h-11 w-11 items-center justify-center rounded-[14px] bg-accent-lime text-[#3D5507]">
                <p.icon className="h-5 w-5" strokeWidth={2} />
              </span>
              <h3 className="mt-5 text-2xl font-semibold text-ink">
                {p.title}
              </h3>
              <p className="mt-3 text-base leading-relaxed text-ink-muted">
                {p.body}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
