export type ArticleBlock =
  | { type: "h2"; text: string }
  | { type: "p"; text: string }
  | { type: "list"; items: string[] }
  | { type: "image"; src: string; alt: string; caption?: string }
  | { type: "cta" };

export type Article = {
  slug: string;
  title: string;
  ingress: string;
  headerImage: string;
  date: string; // ISO
  readMinutes: number;
  blocks: ArticleBlock[];
};

export const ARTICLES: Article[] = [
  {
    slug: "hva-er-viktig-a-tenke-pa-nar-du-skal-flytte",
    title: "Hva er viktig å tenke på når du skal flytte?",
    ingress:
      "En flytting blir sjelden stressende fordi den er vanskelig. Den blir stressende fordi mye skjer samtidig. Her er det som faktisk er viktig å få på plass, i riktig rekkefølge.",
    headerImage:
      "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?q=80&w=2400&auto=format&fit=crop",
    date: "2026-08-04",
    readMinutes: 6,
    blocks: [
      {
        type: "p",
        text: "De fleste undervurderer ikke selve flyttedagen, men ukene før. Nøkkelen til en rolig flytting er å ta beslutningene tidlig, slik at de siste dagene bare handler om gjennomføring. Denne guiden går gjennom det viktigste, fra seks uker før til dagen du leverer nøklene.",
      },
      { type: "h2", text: "Seks uker før: ta de store valgene" },
      {
        type: "p",
        text: "Det første du bør avklare er om du skal flytte selv eller bruke flyttebyrå. Regnestykket er ofte jevnere enn folk tror: leiebil, drivstoff, bæring, forsikring og en helg eller to av din egen tid mot en fast pris fra et byrå som gjør alt på én dag. Bor du i leilighet uten heis, eller har du tunge møbler, taler det meste for byrå.",
      },
      {
        type: "p",
        text: "Innhent tilbud fra flere byråer samtidig, og be om fastpris fremfor timepris når det er mulig. Da vet du hva flyttingen koster før den starter, og du slipper overraskelser hvis dagen tar lengre tid enn planlagt.",
      },
      { type: "cta" },
      { type: "h2", text: "Fire uker før: rydd før du pakker" },
      {
        type: "p",
        text: "Alt du ikke tar med deg, slipper du å pakke, bære og betale for. Gå gjennom rom for rom og sorter i tre bunker: behold, gi bort eller selg, og kast. Møbler og klær i god stand kan leveres til gjenbruksstasjoner eller selges på Finn. Spesialavfall som maling og elektronikk må til miljøstasjonen.",
      },
      {
        type: "p",
        text: "Meld adresseendring til Posten og Folkeregisteret. Det tar noen minutter på nett, og gjelder fra datoen du velger. Husk også å flytte eller si opp strømavtale, internett og innboforsikring. Innboforsikringen bør gjelde begge boliger i overgangsperioden.",
      },
      {
        type: "image",
        src: "/images/boxes-and-plants.jpg",
        alt: "Flytteesker og planter stablet i en stue",
        caption: "Merk eskene med rom og innhold, ikke bare «diverse».",
      },
      { type: "h2", text: "To uker før: pakk systematisk" },
      {
        type: "list",
        items: [
          "Pakk ett rom om gangen, og merk hver eske med rom og kort innhold.",
          "Tunge ting i små esker, lette ting i store. Ryggen din takker deg.",
          "Pakk en «første natt»-bag med sengetøy, lader, toalettsaker og kaffe.",
          "Ta bilder av elektronikk-kabling før du kobler fra.",
          "La klær henge i garderobeesker i stedet for å brette alt.",
        ],
      },
      {
        type: "p",
        text: "Bruker du flyttebyrå, avklar hva de pakker og hva du pakker selv. Mange byråer tilbyr full pakking, og det er ofte rimeligere enn folk tror. Uansett bør verdisaker, dokumenter og medisiner fraktes av deg personlig.",
      },
      { type: "h2", text: "Flyttedagen: logistikk og nøkler" },
      {
        type: "p",
        text: "Sørg for parkering nær inngangen i begge ender, og reserver heisen hvis du bor i blokk. Gå en siste runde i den gamle boligen når alt er ute: sjekk skap, loft, bod og kjeller. Les av strømmåleren og ta bilde av den, både der du flytter fra og dit du flytter.",
      },
      {
        type: "p",
        text: "Og til slutt: senk skuldrene. Med beslutningene tatt på forhånd er flyttedagen bare gjennomføring. Det meste som kan gå galt, er allerede håndtert i planen din.",
      },
    ],
  },
  {
    slug: "hva-koster-det-a-bruke-flyttebyra-i-2026",
    title: "Hva koster det å bruke flyttebyrå i 2026?",
    ingress:
      "Prisen på flyttebyrå varierer mer enn de fleste tjenester du kjøper. Her er hva flyttinger faktisk koster i 2026, hva som driver prisen, og hvordan du unngår å betale for mye.",
    headerImage:
      "https://images.unsplash.com/photo-1554224155-6726b3ff858f?q=80&w=2400&auto=format&fit=crop",
    date: "2026-07-21",
    readMinutes: 5,
    blocks: [
      {
        type: "p",
        text: "Spør du tre byråer om pris på samme flytting, kan du få svar som spriker med flere tusen kroner. Det betyr ikke at noen prøver å lure deg. Det betyr at pris avhenger av ting du kan påvirke: tidspunkt, tilgjengelighet og hvor mye du gjør selv.",
      },
      { type: "h2", text: "Typiske priser i 2026" },
      {
        type: "list",
        items: [
          "Liten leilighet (1–2 rom, samme by): 4 000–8 000 kr",
          "Vanlig leilighet (3 rom, samme by): 8 000–15 000 kr",
          "Rekkehus eller enebolig (samme by): 15 000–30 000 kr",
          "Flytting mellom byer, for eksempel Oslo–Bergen: 15 000–40 000 kr",
          "Full pakking i tillegg: vanligvis 3 000–8 000 kr ekstra",
        ],
      },
      {
        type: "p",
        text: "Prisene er veiledende og forutsetter seriøse, forsikrede byråer. Timepris ligger typisk på 900–1 400 kr for to mann og bil. Ved timepris bør du alltid be om et estimat på totaltid, og gjerne et pristak.",
      },
      { type: "h2", text: "Dette driver prisen opp eller ned" },
      {
        type: "p",
        text: "Volum er den største faktoren: antall kubikkmeter avgjør hvor stor bil og hvor mange folk som trengs. Deretter kommer tilgjengelighet. Trapp uten heis, lang bæreavstand fra dør til bil og trange oppganger gir flere arbeidstimer. En flytting fra fjerde etasje uten heis kan koste 20–30 prosent mer enn samme volum med heis.",
      },
      {
        type: "p",
        text: "Tidspunktet betyr også mye. Månedsskifter, helger og sommermånedene er høysesong. Kan du flytte en tirsdag midt i måneden, er det ofte flere tusen kroner å spare.",
      },
      { type: "cta" },
      { type: "h2", text: "Slik unngår du å betale for mye" },
      {
        type: "list",
        items: [
          "Innhent alltid flere tilbud på samme grunnlag, med likt volum og like betingelser.",
          "Be om fastpris når flyttingen er oversiktlig.",
          "Sjekk at byrået er registrert i Brønnøysund og har ansvarsforsikring.",
          "Rydd og kvitt deg med ting før befaring, så prises et mindre volum.",
          "Vær fleksibel på dato hvis du kan.",
        ],
      },
      {
        type: "p",
        text: "Vær skeptisk til tilbud som er langt under alle andre. Useriøse aktører sparer inn differansen på manglende forsikring, svart arbeid eller tillegg som dukker opp på fakturaen. Et ryddig tilbud skal spesifisere hva som inngår: bil, antall folk, bæring, montering og forsikring.",
      },
      { type: "h2", text: "Husk fradraget i skattemeldingen? Nei." },
      {
        type: "p",
        text: "Et vanlig spørsmål: flytteutgifter er som hovedregel ikke fradragsberettiget for privatpersoner, med mindre flyttingen skjer på grunn av jobb og arbeidsgiver ikke dekker den. Sjekk skatteetaten.no for detaljene som gjelder din situasjon.",
      },
      {
        type: "p",
        text: "Kort oppsummert: prisen på flyttebyrå er ikke hugget i stein. Med flere tilbud, riktig tidspunkt og et ryddig volum får du samme jobb gjort til en lavere pris.",
      },
    ],
  },
  {
    slug: "flyttevask-dette-ma-vaere-gjort-for-du-leverer-noklene",
    title: "Flyttevask: dette må være gjort før du leverer nøklene",
    ingress:
      "Flyttevasken er det siste du gjør i boligen, og det hyppigste konflikttemaet mellom utleier og leietaker. Her er sjekklisten som sørger for at du får godkjent vasken på første forsøk.",
    headerImage:
      "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?q=80&w=2400&auto=format&fit=crop",
    date: "2026-06-30",
    readMinutes: 7,
    blocks: [
      {
        type: "p",
        text: "En flyttevask er noe annet enn en vanlig helgevask. Kravet er at boligen skal være like ren som da du overtok den, og det inkluderer alt du vanligvis hopper over: inni ovnen, bak hvitevarene, oppå skapene og i ventilene. Setter du av tid til det, eller kjøper tjenesten, slipper du trekk i depositum og diskusjoner på overtakelsen.",
      },
      { type: "h2", text: "Kjøkkenet: der de fleste feiler" },
      {
        type: "list",
        items: [
          "Stekeovn: vask innvendig, inkludert rister og stekebrett. Bruk ovnsrens og la den virke.",
          "Kjøleskap og fryser: tøm, avrim og vask innvendig. La dørene stå på gløtt.",
          "Ventilator: vask filter og avfetting av selve viften.",
          "Skap og skuffer: tørk innvendig og utvendig, også oppå skapene.",
          "Bak og under hvitevarer: trekk frem komfyr og kjøleskap og vask gulvet bak.",
        ],
      },
      {
        type: "p",
        text: "Ovnen og ventilatorfilteret er de to punktene som oftest fører til at flyttevask underkjennes. Sett av god tid til begge, eller sjekk at de står eksplisitt i tilbudet hvis du kjøper vasken.",
      },
      { type: "h2", text: "Bad: kalk og sluk" },
      {
        type: "list",
        items: [
          "Rens sluk i dusj og på gulv, og fjern hår og såperester.",
          "Fjern kalk på fliser, dusjvegger og armaturer med kalkfjerner.",
          "Vask toalettet grundig, også bak og rundt festene.",
          "Tørk av rør, lister og ventiler.",
        ],
      },
      {
        type: "image",
        src: "/images/moving-couple.jpg",
        alt: "To personer i gang med flytting og rengjøring",
        caption:
          "Flyttevasken går raskere når boligen allerede er tom for esker.",
      },
      { type: "h2", text: "Resten av boligen" },
      {
        type: "list",
        items: [
          "Vinduer: vask innvendig og utvendig der det er tilgjengelig, inkludert karmer og mellom glassene der det går.",
          "Lister, dørkarmer og stikkontakter: tørk av alt.",
          "Ventiler: støvsug og tørk av friskluftsventiler.",
          "Gulv: støvsug og vask, inkludert under radiatorer og i kroker.",
          "Bod, loft og garasje: tøm helt og kost gulvet.",
        ],
      },
      { type: "h2", text: "Gjøre det selv eller kjøpe flyttevask?" },
      {
        type: "p",
        text: "En profesjonell flyttevask av en vanlig leilighet koster typisk 2 500–5 500 kr i 2026, avhengig av størrelse og stand. Da følger det normalt med garanti: blir vasken underkjent på overtakelsen, kommer firmaet tilbake og utbedrer kostnadsfritt. For mange er det verdt prisen alene, siden du slipper å stå i diskusjonen selv.",
      },
      {
        type: "p",
        text: "Velger du å vaske selv, regn med en hel dag for en leilighet og gjerne en helg for et hus. Vask ovenfra og ned i hvert rom, og ta gulvet til slutt. Dokumenter resultatet med bilder når du er ferdig, datostemplet i mobilen, i tilfelle det blir uenighet i etterkant.",
      },
      { type: "cta" },
      { type: "h2", text: "Sjekklisten før nøkkeloverlevering" },
      {
        type: "list",
        items: [
          "Alle rom tomme, også bod og loft.",
          "Ovn, kjøleskap og ventilator godkjent-rene.",
          "Sluk renset og kalk fjernet på badet.",
          "Vinduer, lister og ventiler tørket av.",
          "Strøm lest av og bilder tatt.",
          "Alle nøkler samlet, også til postkasse og bod.",
        ],
      },
      {
        type: "p",
        text: "Med denne listen i hånden er flyttevasken en jobb med en tydelig slutt, ikke et åpent prosjekt. Og leverer du nøklene til en ren bolig, er sjansen stor for at både depositum og forholdet til utleier forblir intakt.",
      },
    ],
  },
];

export function getArticle(slug: string): Article | undefined {
  return ARTICLES.find((a) => a.slug === slug);
}
