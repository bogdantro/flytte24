const services = [
  {
    title: "Flyttehjelp",
    body: "Pakking, bæring og transport, trygt fra dør til dør. Vi finner byråer som tar hele jobben. Du velger hvor mye hjelp du trenger.",
  },
  {
    title: "Flyttevask",
    body: "Godkjente vaskebyråer med garanti. Perfekt før innflytting eller når leiekontrakten krever en grundig sluttvask.",
  },
  {
    title: "Lagring",
    body: "Trygg kortsiktig eller langsiktig oppbevaring i ditt nærområde, med forsikring og fleksibel tilgang.",
  },
  {
    title: "Utlandsflytting",
    body: "Spesialiserte byråer som håndterer toll, containere og papirarbeid. Både flytting ut av Norge og hjem igjen.",
  },
  {
    title: "Kontorflytting",
    body: "Erfarne partnere som flytter kontor, lager og næringslokaler utenom arbeidstid. IT, møbler og arkiv håndtert profesjonelt.",
  },
  {
    title: "Dødsbo",
    body: "Tømming og ryddighet med respekt. Byråer med erfaring fra bobehandling av innbo.",
  },
];

export function Services() {
  return (
    <section className="px-6 py-20 sm:px-10 sm:py-28 lg:py-40">
      <div className="mx-auto max-w-6xl">
        <div className="flex flex-col items-center text-center">
          <h2 className="text-3xl font-semibold text-ink sm:text-[42px] sm:leading-[1.1]">
            Alt du trenger på ett sted
          </h2>
          <span
            aria-hidden
            className="mt-3 inline-block h-1 w-16 rounded-full bg-accent-amber"
          />
        </div>
        <div className="mt-12 grid gap-4 sm:gap-6 md:grid-cols-3">
          {services.map((s) => (
            <article
              key={s.title}
              className="rounded-[14px] bg-surface-soft p-6 ring-1 ring-line transition-colors hover:bg-surface-soft/70 sm:p-7 lg:p-8"
            >
              <h3 className="text-2xl font-semibold text-ink">
                {s.title}
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-ink-muted sm:text-base">
                {s.body}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
