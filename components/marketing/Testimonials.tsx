import Image from "next/image";

type Sitat = {
  quote: string;
  name: string;
  role: string;
  src: string;
};

const sitater: Sitat[] = [
  {
    quote:
      "Kobly fant meg tre seriøse byråer i løpet av få timer. Sparte meg for både tid og masse penger.",
    name: "Kristoffer Skogen",
    role: "Privatkunde, Bergen",
    src: "/images/ciocan-ciprian-_Z2eTqGL7dg-unsplash.jpg",
  },
  {
    quote:
      "Vi fikk skreddersydde tilbud uten å måtte ringe ti forskjellige byråer selv. Anbefales på det varmeste.",
    name: "Sunniva Thune",
    role: "Næringsflytting, Oslo",
    src: "/images/sinitta-leunen-Y6fw-exCnsg-unsplash.jpg",
  },
  {
    quote:
      "Trygg og enkel prosess fra start til slutt. Byråene som tok kontakt var profesjonelle og hyggelige.",
    name: "Eivind Johansen",
    role: "Privatkunde, Trondheim",
    src: "/images/veronika-trushkevich-krFfLPfSj4k-unsplash.jpg",
  },
];

export function Testimonials() {
  return (
    <section className="px-6 py-20 sm:px-10 sm:py-28 lg:py-40">
      <div className="mx-auto max-w-6xl">
        <h2 className="mx-auto max-w-2xl text-center text-3xl font-semibold leading-[1.1] text-ink sm:text-[42px]">
          Hva sier kundene våre?
        </h2>
        <div className="mt-12 grid gap-8 sm:mt-14 md:grid-cols-3 md:gap-6 lg:gap-10">
          {sitater.map((s) => (
            <article key={s.name} className="flex flex-col">
              <div className="relative aspect-[4/5] overflow-hidden rounded-[14px] bg-line">
                <Image
                  src={s.src}
                  alt=""
                  fill
                  sizes="(min-width: 768px) 33vw, 90vw"
                  className="object-cover"
                />
              </div>
              <p className="mt-6 text-xl leading-[1.3] text-ink sm:text-[22px]">
                “{s.quote}”
              </p>
              <p className="mt-4 text-sm text-ink-muted">
                {s.name}
                <span className="text-ink/40"> · {s.role}</span>
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
