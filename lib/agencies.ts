export type Review = {
  name: string;
  date: string; // ISO
  stars: number;
  service: string;
  comment: string;
};

export type Agency = {
  slug: string;
  name: string;
  logo: string;
  /** Sant navn på logofilen krever egen behandling for relok. (mørk logo på lys flate). */
  logoBlendMultiply?: boolean;
  tagline: string;
  /** Kort beskrivelse på oversiktskortet. */
  short: string;
  /** «Om oss», skrevet i byråets egen stemme. */
  about: string[];
  rating: number;
  reviewCount: number;
  jobsCompleted: number;
  responseTime: string;
  memberSince: number;
  services: string[];
  areas: string[];
  /** Kontaktperson brukes i bekreftelses-e-posten til kunden. */
  contact: { name: string; role: string; phone: string };
  reviews: Review[];
};

export const AGENCIES: Agency[] = [
  {
    slug: "loft",
    name: "LØFT",
    logo: "/images/loeftlogo.svg",
    tagline: "Flytting med hodet, ikke bare ryggen",
    short:
      "Oslo-basert byrå med spesialkompetanse på trange bygårder og verdifullt innbo.",
    about: [
      "Vi startet LØFT i 2019 fordi vi var lei av flyttebyråer som behandlet folks eiendeler som stein. Alle hos oss har fagbrev eller har gått i lære hos noen som har det, og vi bruker like mye tid på å planlegge en flytting som på å gjennomføre den.",
      "Spesialiteten vår er gamle bygårder i indre Oslo. Trange trapper, dører som ikke er standard og heiser som enten ikke finnes eller ikke virker. Vi kommer alltid på befaring før tilbudet, så prisen du får er den du betaler.",
      "Vi tar imot et begrenset antall jobber i uka. Det gjør at vi kan si nei til å stresse, og ja til å gjøre jobben ordentlig.",
    ],
    rating: 4.9,
    reviewCount: 87,
    jobsCompleted: 312,
    responseTime: "Svarer vanligvis innen 2 timer",
    memberSince: 2023,
    services: [
      "Flyttehjelp",
      "Pakking",
      "Flyttevask",
      "Piano og flygel",
      "Kunst og antikviteter",
      "Montering",
    ],
    areas: [
      "Grünerløkka",
      "Gamle Oslo",
      "St. Hanshaugen",
      "Sagene",
      "Frogner",
      "Nordre Aker",
    ],
    contact: { name: "Marius Halvorsen", role: "Prosjektleder", phone: "922 14 087" },
    reviews: [
      {
        name: "Ingrid S.",
        date: "2026-07-18",
        stars: 5,
        service: "Flyttehjelp og pakking",
        comment:
          "Vi bor i fjerde etasje uten heis på Grünerløkka og gruet oss skikkelig. Guttene fra LØFT tok med seg sekkevogner og stropper vi ikke visste fantes, og hele leiligheten var nede på tre timer. Ingenting fikk en ripe.",
      },
      {
        name: "Fredrik B.",
        date: "2026-06-02",
        stars: 5,
        service: "Pianotransport",
        comment:
          "Hadde et gammelt Steinway-piano etter min far som måtte fra Frogner til Nordstrand. De sendte fire mann og et spesialstativ, og var tydelige på hva de kunne og ikke kunne garantere. Profesjonelt hele veien.",
      },
      {
        name: "Anniken H.",
        date: "2026-05-21",
        stars: 4,
        service: "Flyttehjelp",
        comment:
          "Veldig fornøyd med selve flyttingen. Trekker en stjerne fordi de kom 45 minutter senere enn avtalt, men de ga beskjed underveis og tok igjen tiden.",
      },
      {
        name: "Tobias M.",
        date: "2026-04-11",
        stars: 5,
        service: "Flyttehjelp og flyttevask",
        comment:
          "Bestilte flyttevask i tillegg, og den ble godkjent på overtakelsen uten kommentarer. Utleier spurte til og med hvem vi hadde brukt.",
      },
    ],
  },
  {
    slug: "relok",
    name: "relok.",
    logo: "/images/reloklogo.png",
    logoBlendMultiply: true,
    tagline: "Hele Østlandet, hele veien",
    short:
      "Stort apparat med egen lagerpark. Tar både privatflyttinger og hele kontorbygg.",
    about: [
      "relok. har kjørt flyttebiler siden 2011, og i dag har vi 24 ansatte og elleve biler. Størrelsen gjør at vi nesten alltid kan tilby datoen du ønsker, også i månedsskiftene når resten av bransjen er utsolgt.",
      "Vi har eget lager på Alnabru med døgnbemannet adgangskontroll. Det er nyttig når overtakelse og innflytting ikke skjer samme dag, noe som er oftere enn folk tror.",
      "Halvparten av omsetningen vår kommer fra bedriftsflytting. Det har lært oss å planlegge presist: når et kontor skal være oppe igjen mandag morgen, finnes det ingen fleksibilitet. Den planleggingen tar vi med oss inn i privatjobbene også.",
    ],
    rating: 4.7,
    reviewCount: 214,
    jobsCompleted: 1840,
    responseTime: "Svarer vanligvis innen 1 time",
    memberSince: 2022,
    services: [
      "Flyttehjelp",
      "Kontorflytting",
      "Lagring",
      "Pakking",
      "Flyttevask",
      "Avfallshåndtering",
    ],
    areas: [
      "Hele Oslo",
      "Bærum",
      "Asker",
      "Lillestrøm",
      "Drammen",
      "Follo",
    ],
    contact: { name: "Sara Nyland", role: "Kundeansvarlig", phone: "477 03 512" },
    reviews: [
      {
        name: "Petter L.",
        date: "2026-08-01",
        stars: 5,
        service: "Kontorflytting",
        comment:
          "Flyttet 40 arbeidsplasser fra Skøyen til Nydalen over en helg. Alt sto klart mandag morgen, inkludert skjermer og dokkingstasjoner. Imponerende logistikk.",
      },
      {
        name: "Camilla R.",
        date: "2026-06-27",
        stars: 5,
        service: "Flyttehjelp og lagring",
        comment:
          "Vi måtte ut av gammel bolig tre uker før vi fikk nøklene til den nye. relok. mellomlagret alt på Alnabru og kjørte det ut igjen på dagen vi hadde avtalt. Løste et problem jeg trodde skulle bli dyrt og vanskelig.",
      },
      {
        name: "Håkon E.",
        date: "2026-05-09",
        stars: 4,
        service: "Flyttehjelp",
        comment:
          "Effektive og hyggelige. Kunne ønsket meg litt tydeligere informasjon om hva som var inkludert i prisen på forhånd, men da jeg spurte fikk jeg raskt svar.",
      },
      {
        name: "Nina D.",
        date: "2026-03-30",
        stars: 5,
        service: "Flyttehjelp Oslo til Drammen",
        comment:
          "Lang flytting med mye tungt. To mann jobbet jevnt og trutt i sju timer uten å klage én gang. Fastprisen holdt selv om det tok lengre tid enn estimert.",
      },
    ],
  },
  {
    slug: "flyttefoten",
    name: "Flyttefoten",
    logo: "/images/flyttefotenlogo.png",
    tagline: "Familiedrevet siden 2014",
    short:
      "Lite byrå med faste folk. Kjent for å ta godt vare på studenter og førstegangsflyttere.",
    about: [
      "Flyttefoten er et familieforetak. Pappa startet med én varebil i 2014, i dag er vi seks stykker og tre biler, og de fleste av oss er i slekt eller har vokst opp i samme gate.",
      "Vi er små, og det er et bevisst valg. Du snakker med den samme personen fra første telefon til siste eske er båret inn, og det er stor sjanse for at du møter noen av oss igjen neste gang du flytter.",
      "Vi har en myk plass i hjertet for folk som flytter for første gang. Studenter, nyutdannede, folk som flytter fra barndomshjemmet. Vi tar oss tid til å forklare hva som lønner seg, også når svaret er at du klarer deg fint uten oss.",
    ],
    rating: 4.8,
    reviewCount: 63,
    jobsCompleted: 428,
    responseTime: "Svarer vanligvis samme dag",
    memberSince: 2024,
    services: [
      "Flyttehjelp",
      "Studentflytting",
      "Pakking",
      "Flyttevask",
      "Bortkjøring",
    ],
    areas: [
      "Gamle Oslo",
      "Grünerløkka",
      "Sagene",
      "Bjerke",
      "Østensjø",
      "Nordstrand",
    ],
    contact: { name: "Jonas Ødegård", role: "Daglig leder", phone: "986 42 210" },
    reviews: [
      {
        name: "Sofie T.",
        date: "2026-07-30",
        stars: 5,
        service: "Studentflytting",
        comment:
          "Flyttet fra hybel på Bjerke til kollektiv på Løkka. De ga meg et tilbud som var billigere enn jeg hadde budsjettert, og sa rett ut at jeg ikke trengte pakketjenesten deres. Sjeldent å oppleve.",
      },
      {
        name: "Emil K.",
        date: "2026-06-14",
        stars: 5,
        service: "Flyttehjelp",
        comment:
          "Jonas kom selv på befaring og husket navnet mitt da de dukket opp tre uker senere. Små ting, men det gjør at man føler seg trygg.",
      },
      {
        name: "Maria V.",
        date: "2026-04-25",
        stars: 4,
        service: "Flyttehjelp og bortkjøring",
        comment:
          "Tok med seg gammel sofa og et skap til gjenbruksstasjonen samtidig. Praktisk. Litt trangt om plassen i bilen, så vi måtte ta to turer, men de tok ikke ekstra betalt for det.",
      },
      {
        name: "Lars-Petter N.",
        date: "2026-02-08",
        stars: 5,
        service: "Flyttehjelp",
        comment:
          "Flyttet mamma til leilighet med livsløpsstandard på Nordstrand. De var tålmodige med henne, bar inn alt på riktig plass og satte sammen senga uten at vi spurte.",
      },
    ],
  },
  {
    slug: "flytteby",
    name: "Flytteby",
    logo: "/images/flytteblogo.png",
    tagline: "Nøkkelferdig flytting fra dør til dør",
    short:
      "Full pakke: pakking, flytting, vask og montering. For deg som vil slippe å tenke.",
    about: [
      "Flytteby ble startet av to tidligere hotelldirektører som mente flyttebransjen kunne lære noe av servicebransjen. Derfor er vi bygget rundt én idé: du skal kunne dra på jobb om morgenen og komme hjem til en ferdig innflyttet bolig.",
      "Vi pakker, kjører, bærer inn, monterer møbler, henger opp bilder og tar med oss emballasjen ut igjen. Flyttevasken av den gamle boligen skjer parallelt, av vårt eget vaskelag, ikke en underleverandør.",
      "Det koster mer enn å bære selv. Til gjengjeld er det ingenting du må huske, og vi har aldri hatt en kunde som måtte ta fri fra jobb på flyttedagen.",
    ],
    rating: 4.6,
    reviewCount: 129,
    jobsCompleted: 764,
    responseTime: "Svarer vanligvis innen 3 timer",
    memberSince: 2021,
    services: [
      "Nøkkelferdig flytting",
      "Pakking og utpakking",
      "Flyttevask",
      "Montering",
      "Lagring",
      "Kontorflytting",
    ],
    areas: [
      "Frogner",
      "Ullern",
      "Vestre Aker",
      "Nordre Aker",
      "Nordstrand",
      "Bærum",
    ],
    contact: { name: "Elise Aarø", role: "Flyttekoordinator", phone: "934 77 601" },
    reviews: [
      {
        name: "Kristin A.",
        date: "2026-07-05",
        stars: 5,
        service: "Nøkkelferdig flytting",
        comment:
          "Dro på jobb fra en full leilighet på Majorstuen og kom hjem til et ferdig innredet hus på Vinderen. Bøkene sto til og med i riktig rekkefølge i hylla. Verdt hver krone.",
      },
      {
        name: "Ole Martin S.",
        date: "2026-06-19",
        stars: 4,
        service: "Flytting og montering",
        comment:
          "Veldig god service og ryddig gjennomføring. Prisen er i øvre sjikt, og det bør man vite på forhånd. Men de leverte nøyaktig det de lovet.",
      },
      {
        name: "Beate W.",
        date: "2026-05-02",
        stars: 5,
        service: "Flytting, vask og lagring",
        comment:
          "Vi hadde en kaotisk periode med salg og kjøp som ikke gikk opp. Elise holdt oversikten for oss og flyttet datoene to ganger uten å blunke.",
      },
      {
        name: "Andreas G.",
        date: "2026-03-14",
        stars: 4,
        service: "Nøkkelferdig flytting",
        comment:
          "Alt gikk bra, men vi måtte etterspørre utpakkingen av kjøkkenet som lå inne i avtalen. De kom tilbake dagen etter og fullførte uten diskusjon.",
      },
    ],
  },
];

export function getAgency(slug: string): Agency | undefined {
  return AGENCIES.find((a) => a.slug === slug);
}

/** Formaterer rating på norsk: 4.9 → «4,9». */
export function formatRating(rating: number): string {
  return rating.toFixed(1).replace(".", ",");
}
