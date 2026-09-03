export type District = {
  /** Slug uten norske tegn: grunerlokka, sondre-nordstrand, st-hanshaugen, ostensjo. */
  slug: string;
  name: string;
  /** Kort setning under H1 i heroen. */
  lead: string;
  /** Ett kort avsnitt: hva slags område dette er, og at vi stiller opp uansett. */
  body: string;
  metaDescription: string;
};

export const DISTRICTS: District[] = [
  {
    slug: "alna",
    name: "Alna",
    lead: "Groruddalens sørside, med romslige borettslag og kort vei til E6.",
    body: "Alna strekker seg fra Teisen i vest til Furuset i øst, med blokker og rekkehus fra sekstitallet og syttitallet, brede oppganger og god plass rundt byggene. Enten du flytter fra en leilighet på Lindeberg eller et rekkehus på Haugerud, har vi byråer som kjenner området og er klare til å ta jobben.",
    metaDescription:
      "Skal du flytte til eller fra Alna? Få 3 uforpliktende tilbud fra kvalitetssjekkede flyttebyråer som jobber på Furuset, Lindeberg og Haugerud.",
  },
  {
    slug: "bjerke",
    name: "Bjerke",
    lead: "Nye leilighetskvartaler på Løren, etterkrigsborettslag på Veitvet.",
    body: "Bjerke er bydelen med størst spenn i boligmasse, fra de moderne byggene på Løren og Økern til borettslagene på Veitvet, Linderud og Årvoll. Byråene våre jobber i hele bydelen, uansett om lasset skal ut gjennom en ny heis eller ned en gammel trapp.",
    metaDescription:
      "Flyttebyrå i Bjerke: få 3 gratis tilbud fra byråer som jobber på Løren, Økern, Veitvet og Årvoll. Uforpliktende og ferdig på to minutter.",
  },
  {
    slug: "frogner",
    name: "Frogner",
    lead: "Store leiligheter i bygårder fra århundreskiftet.",
    body: "Frogner har byens mest påkostede boligmasse fra 1890- til 1910-tallet, fra Majorstuen og Uranienborg til villaene på Bygdøy. Vi har byråer som er vant til høye tak, smale trapperom og innbo som må håndteres varsomt.",
    metaDescription:
      "Flyttebyrå på Frogner: få 3 tilbud gratis fra byråer med erfaring fra bygårder på Majorstuen, Uranienborg og Bygdøy.",
  },
  {
    slug: "gamle-oslo",
    name: "Gamle Oslo",
    lead: "Trehusidyll på Kampen og Vålerenga, glassfasader i Bjørvika.",
    body: "Gamle Oslo spenner fra de små trehusene på Kampen og Vålerenga til de nye kvartalene i Bjørvika og på Ensjø, med Grønland og Tøyen imellom. Uansett hvilken del av bydelen du bor i, finner vi byråer som er klare til å hjelpe deg.",
    metaDescription:
      "Flyttebyrå i Gamle Oslo: 3 gratis tilbud fra byråer som jobber på Kampen, Tøyen, Grønland og i Bjørvika.",
  },
  {
    slug: "grorud",
    name: "Grorud",
    lead: "Blokker og rekkehus fra syttitallet, og bilfrie Romsås på toppen.",
    body: "Grorud består i hovedsak av borettslag på Ammerud, Rødtvet og Kalbakken, pluss Romsås som ble bygget bilfritt med parkering i eget P-hus. Byråene våre kjenner både heisene og gangveiene her, og stiller opp uansett hvor i bydelen du bor.",
    metaDescription:
      "Flyttebyrå i Grorud: få 3 tilbud gratis fra byråer som jobber på Ammerud, Rødtvet, Kalbakken og Romsås.",
  },
  {
    slug: "grunerlokka",
    name: "Grünerløkka",
    lead: "Fire etasjer, ingen heis og en gate der det aldri er ledig parkering.",
    body: "Grünerløkka er Oslos tettest bebygde bydel, med bygårder i fire og fem etasjer rundt Birkelunden, Sofienberg og Thorvald Meyers gate. Vi har byråer som er vant til trapper uten heis og gater der parkeringen må planlegges, og som stiller opp uansett hvilken etasje du bor i.",
    metaDescription:
      "Flyttebyrå på Grünerløkka: 3 gratis tilbud fra byråer som er vant til bygårder uten heis rundt Birkelunden og Sofienberg.",
  },
  {
    slug: "nordre-aker",
    name: "Nordre Aker",
    lead: "Hagebyer, studentboliger og Nydalens leilighetsbygg.",
    body: "Nordre Aker går fra rekkehusene i Ullevål hageby og Tåsen, via studentbyene på Sogn og Kringsjå, til de store leilighetsprosjektene i Nydalen og på Storo. Byråene våre tar oppdrag i hele bydelen, enten det er en hybel eller et helt hus som skal flyttes.",
    metaDescription:
      "Flyttebyrå i Nordre Aker: få 3 tilbud gratis fra byråer som jobber i Ullevål hageby, på Tåsen, Kringsjå og i Nydalen.",
  },
  {
    slug: "nordstrand",
    name: "Nordstrand",
    lead: "Utsikt over fjorden, og bakker mellom bilen og inngangsdøra.",
    body: "Nordstrand er villaer og tomannsboliger i skrånende terreng fra Ekeberg og Bekkelaget i nord til Ljan i sør, med blokkene på Lambertseter innimellom. Vi har byråer som er vant til bratte innkjørsler og trapper gjennom hagen, og som tar jobben uansett årstid.",
    metaDescription:
      "Flyttebyrå på Nordstrand: 3 gratis tilbud fra byråer som jobber på Ljan, Bekkelaget, Ekeberg og Lambertseter.",
  },
  {
    slug: "sagene",
    name: "Sagene",
    lead: "Arbeiderbyens bygårder langs Akerselva.",
    body: "Sagene ble bygget for folkene ved fabrikkene langs Akerselva, og bygårdene fra 1890- til 1930-tallet står fortsatt tett i Torshov, Bjølsen og Iladalen. Byråene våre kjenner oppgangene her godt, og hjelper deg enten det er en toroms eller en hel etasje som skal ut.",
    metaDescription:
      "Flyttebyrå på Sagene: få 3 tilbud gratis fra byråer som jobber på Torshov, Bjølsen og Iladalen.",
  },
  {
    slug: "st-hanshaugen",
    name: "St. Hanshaugen",
    lead: "Sentrumsnært, tett trafikkert og fullt av små leiligheter.",
    body: "St. Hanshaugen ligger som en ring rundt parken med samme navn, fra Bislett og Fagerborg til Ila og Adamstuen, med bygårder fra rundt år 1900. Vi har byråer som kan bydelen, og som vet hvordan de får en flyttebil trygt på plass i travle gater.",
    metaDescription:
      "Flyttebyrå på St. Hanshaugen: 3 gratis tilbud fra byråer som jobber på Bislett, Fagerborg, Ila og Adamstuen.",
  },
  {
    slug: "stovner",
    name: "Stovner",
    lead: "Groruddalens nordligste bydel, med god plass rundt blokkene.",
    body: "Stovner ligger øverst i Groruddalen, med Vestli, Haugenstua, Rommen og Fossum, romslige uteområder og parkering nær inngangen. Byråene våre kjører hit fast, så du får like gode tilbud her som ellers i byen.",
    metaDescription:
      "Flyttebyrå på Stovner: få 3 tilbud gratis fra byråer som jobber på Vestli, Haugenstua, Rommen og Fossum.",
  },
  {
    slug: "sondre-nordstrand",
    name: "Søndre Nordstrand",
    lead: "Rekkehus, terrassehus og mye grønt mellom husene.",
    body: "Søndre Nordstrand er Oslos sørligste bydel, med Holmlia, Mortensrud, Bjørndal og Prinsdal, bygget ut på sytti- og åttitallet med rekkehus og lave blokker. Vi har byråer som kjenner veien inn til riktig side av bygget, og som stiller opp uansett hvor stort lasset er.",
    metaDescription:
      "Flyttebyrå i Søndre Nordstrand: 3 gratis tilbud fra byråer som jobber på Holmlia, Mortensrud, Bjørndal og Prinsdal.",
  },
  {
    slug: "ullern",
    name: "Ullern",
    lead: "Villaveier på åsen, nybygg og kontorer på Skøyen.",
    body: "Ullern deler seg naturlig i to: villaene fra mellomkrigstiden på Ullernåsen, Montebello og Bestum, og de moderne byggene nede på Skøyen. Byråene våre tar både privatflytting og kontorflytting her, så du får hjelp uansett hva som skal flyttes.",
    metaDescription:
      "Flyttebyrå i Ullern: få 3 tilbud gratis fra byråer som jobber på Skøyen, Montebello, Bestum og Ullernåsen.",
  },
  {
    slug: "vestre-aker",
    name: "Vestre Aker",
    lead: "Store eneboliger, lange oppkjørsler og bakker som merkes om vinteren.",
    body: "Vestre Aker strekker seg oppover mot marka, fra Vinderen og Slemdal til Holmenkollen, Røa og Voksen, med store eneboliger med hage, garasje og kjeller. Vi har byråer som er vant til volumet her, og som kommer trygt frem også når oppkjørselen er glatt.",
    metaDescription:
      "Flyttebyrå i Vestre Aker: 3 gratis tilbud fra byråer som jobber på Vinderen, Slemdal, Holmenkollen og Røa.",
  },
  {
    slug: "ostensjo",
    name: "Østensjø",
    lead: "Femti- og sekstitallets Oslo rundt Østensjøvannet.",
    body: "Østensjø ble bygget for barnefamilier, og rekkehusene og lavblokkene på Bøler, Oppsal og Manglerud står fortsatt slik de ble tegnet, med bod og parkering nær inngangen. Byråene våre kjenner bydelen godt, og hjelper deg uansett hvor mye som skal være med.",
    metaDescription:
      "Flyttebyrå i Østensjø: få 3 tilbud gratis fra byråer som jobber på Bøler, Oppsal og Manglerud.",
  },
];

export function getDistrict(slug: string): District | undefined {
  return DISTRICTS.find((d) => d.slug === slug);
}
