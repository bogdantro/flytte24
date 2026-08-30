"""
The Oslo district ("bydel") landing pages — spec §8/§13.2. Oslo is the only
city with sub-pages; every CTA on a district page funnels into the same
Oslo-centered wizard map (/flytteforesporsel/?by=oslo), since the wizard has
no per-district map center (spec §8's own note).

Each entry carries a `lead` (one-line hero subhead, mirrors CityHero's body
line) and a `body` (a unique descriptive paragraph, distinct per district,
so these pages don't read as thin/duplicate content for SEO — spec §8) and
a `meta_description` for the page's own <meta name="description">.
"""

OSLO_DISTRICTS = {
    "alna": {
        "name": "Alna",
        "lead": "Flyttebyråer med god kjennskap til Furuset, Haugerud, Lindeberg og Ellingsrud.",
        "body": (
            "Alna strekker seg fra Furuset i nord til Ellingsrud og Lindeberg lenger sør, med et "
            "variert boligmiljø av blokkbebyggelse og rekkehus. Flyttebyråene vi jobber med i "
            "området kjenner adkomsten til de store borettslagene godt, og har erfaring med alt "
            "fra små hybler til flytting av hele familieboliger."
        ),
        "meta_description": "Flyttebyrå i Alna — få 3 tilbud gratis fra kvalitetssjekkede byråer som kjenner Furuset, Haugerud, Lindeberg og Ellingsrud.",
    },
    "bjerke": {
        "name": "Bjerke",
        "lead": "Erfarne byråer som dekker Linderud, Økern og Vollebekk.",
        "body": (
            "Bjerke ligger sentralt mellom store innfartsårer, med Linderud, Økern og det stadig "
            "voksende Vollebekk som de mest folkerike delene. Mange av byråene i vårt nettverk "
            "flytter jevnlig inn og ut av nyere leilighetsbygg her, og vet hva som skal til for en "
            "smidig flytting i områder med travle bomringveier."
        ),
        "meta_description": "Flyttebyrå i Bjerke — få 3 tilbud gratis fra kvalitetssjekkede byråer som kjenner Linderud, Økern og Vollebekk.",
    },
    "frogner": {
        "name": "Frogner",
        "lead": "Byråer som er vant til smale gater, sameier og eldre bygårder på Frogner.",
        "body": (
            "Frogner er en av Oslos tettest bebygde bydeler, med mye eldre bygårder, smale gater og "
            "begrenset parkering rundt Skillebekk, Solli og Frognerparken. Byråene som jobber her "
            "har erfaring med bæring i trapp uten heis, og vet hvordan man løser flyttebil-parkering "
            "midt i sentrum uten stress."
        ),
        "meta_description": "Flyttebyrå i Frogner — få 3 tilbud gratis fra kvalitetssjekkede byråer som kjenner Skillebekk, Solli og Frognerparken.",
    },
    "gamle-oslo": {
        "name": "Gamle Oslo",
        "lead": "Godt kjent i Grønland, Tøyen, Kampen og Vålerenga.",
        "body": (
            "Gamle Oslo er en av byens mest mangfoldige bydeler, fra de tette kvartalene på Grønland "
            "og Tøyen til trehusbebyggelsen på Kampen og Vålerenga. Flyttebyråene vi samarbeider med "
            "kjenner både de trange bakgatene og de nyere høyblokkene ved Ensjø, og planlegger "
            "flyttingen deretter."
        ),
        "meta_description": "Flyttebyrå i Gamle Oslo — få 3 tilbud gratis fra kvalitetssjekkede byråer som kjenner Grønland, Tøyen, Kampen og Vålerenga.",
    },
    "grorud": {
        "name": "Grorud",
        "lead": "Byråer som kjenner Ammerud, Rødtvet og Kalbakken godt.",
        "body": (
            "Grorud har mye av sin bebyggelse i borettslag rundt Ammerud, Rødtvet og Kalbakken, ofte "
            "med korte avstander fra parkeringsplass til inngangsdør. Det gjør flyttingen effektiv "
            "når byrået kjenner lokale kjøremønstre og heisstørrelser fra tidligere oppdrag i "
            "området."
        ),
        "meta_description": "Flyttebyrå i Grorud — få 3 tilbud gratis fra kvalitetssjekkede byråer som kjenner Ammerud, Rødtvet og Kalbakken.",
    },
    "grunerlokka": {
        "name": "Grünerløkka",
        "lead": "Spesialister på trange bygårder og sykkelgater på Løkka.",
        "body": (
            "Grünerløkka er tett befolket med gamle bygårder rundt Sofienberg, Rodeløkka og "
            "Birkelunden, mange uten heis og med begrenset kjøretilgang på sykkelprioriterte gater. "
            "Byråene i vårt nettverk er vant til å bære opp smale trapper og til å koordinere "
            "lossetid rundt gatetravle tidspunkt på Løkka."
        ),
        "meta_description": "Flyttebyrå i Grünerløkka — få 3 tilbud gratis fra kvalitetssjekkede byråer som kjenner Sofienberg, Rodeløkka og Birkelunden.",
    },
    "nordre-aker": {
        "name": "Nordre Aker",
        "lead": "Dekker Kjelsås, Grefsen, Nydalen og Tåsen.",
        "body": (
            "Nordre Aker spenner fra eneboligstrøkene på Grefsen og Tåsen til de nyere "
            "leilighetsbyggene i Nydalen og Kjelsås. Byråene her er like komfortable med "
            "flyttelass fra en enebolig med hage som med en leilighet i et moderne næringsbygg "
            "gjort om til bolig."
        ),
        "meta_description": "Flyttebyrå i Nordre Aker — få 3 tilbud gratis fra kvalitetssjekkede byråer som kjenner Kjelsås, Grefsen, Nydalen og Tåsen.",
    },
    "nordstrand": {
        "name": "Nordstrand",
        "lead": "Trygge byråer for Ljan, Bekkelaget og Hellerud.",
        "body": (
            "Nordstrand er preget av rolige villaveier og god nærhet til fjorden, fra Ljan og "
            "Bekkelaget i sør til Hellerud lenger nord. Mange av flyttingene her involverer større "
            "eneboliger, og byråene vi jobber med har utstyr og bemanning til å håndtere store "
            "flyttelass på bratte, svingete villaveier."
        ),
        "meta_description": "Flyttebyrå i Nordstrand — få 3 tilbud gratis fra kvalitetssjekkede byråer som kjenner Ljan, Bekkelaget og Hellerud.",
    },
    "sagene": {
        "name": "Sagene",
        "lead": "Byråer som kjenner Torshov, Bjølsen og Iladalen.",
        "body": (
            "Sagene er en kompakt bydel med mye murgårdbebyggelse rundt Torshov, Bjølsen og "
            "Iladalen, gjerne med smale oppganger og trange fortau. Flyttebyråene som dekker "
            "området er vant til å planlegge lossing rundt beboerparkering og korte "
            "stopp-forbudssoner."
        ),
        "meta_description": "Flyttebyrå i Sagene — få 3 tilbud gratis fra kvalitetssjekkede byråer som kjenner Torshov, Bjølsen og Iladalen.",
    },
    "st-hanshaugen": {
        "name": "St. Hanshaugen",
        "lead": "Kjenner Bislett, Ullevål Hageby og Adamstuen.",
        "body": (
            "St. Hanshaugen strekker seg fra det tett bebygde Bislett til de rolige "
            "villastrøkene i Ullevål Hageby og Adamstuen. Byråene vi samarbeider med her har "
            "erfaring fra begge ytterpunkter — trange bygårder like gjerne som eneboliger med "
            "egen hage."
        ),
        "meta_description": "Flyttebyrå i St. Hanshaugen — få 3 tilbud gratis fra kvalitetssjekkede byråer som kjenner Bislett, Ullevål Hageby og Adamstuen.",
    },
    "stovner": {
        "name": "Stovner",
        "lead": "Byråer som er trygge på Vestli, Rommen og Fossum.",
        "body": (
            "Stovner ligger lengst nordøst i Oslo, med Vestli, Rommen og Fossum som kjente "
            "boligområder tett på T-banen. Flyttebyråene i nettverket vårt kjenner "
            "adkomstveiene godt og planlegger effektive ruter mellom blokkbebyggelsen og "
            "flyttebilen."
        ),
        "meta_description": "Flyttebyrå i Stovner — få 3 tilbud gratis fra kvalitetssjekkede byråer som kjenner Vestli, Rommen og Fossum.",
    },
    "sondre-nordstrand": {
        "name": "Søndre Nordstrand",
        "lead": "Dekker Holmlia, Mortensrud og Bjørndal.",
        "body": (
            "Søndre Nordstrand er Oslos grønneste bydel, med Holmlia, Mortensrud og Bjørndal "
            "omgitt av mye friareal og lengre avstander mellom byggene. Byråene her er vant til "
            "flyttebiler som må kjøre litt lenger inn i boligfeltene, og til flytting både til og "
            "fra rekkehus og blokk."
        ),
        "meta_description": "Flyttebyrå i Søndre Nordstrand — få 3 tilbud gratis fra kvalitetssjekkede byråer som kjenner Holmlia, Mortensrud og Bjørndal.",
    },
    "ullern": {
        "name": "Ullern",
        "lead": "Byråer som kjenner Lysaker, Montebello og Hoff.",
        "body": (
            "Ullern ligger fint til langs fjorden mot Lysaker, med Montebello og Hoff som "
            "sentrale boligstrøk mellom eneboliger og nyere leilighetskompleks. Flyttebyråene vi "
            "jobber med her har god erfaring med både villaflytting og innflytting i moderne "
            "sameier med underjordisk garasje."
        ),
        "meta_description": "Flyttebyrå i Ullern — få 3 tilbud gratis fra kvalitetssjekkede byråer som kjenner Lysaker, Montebello og Hoff.",
    },
    "vestre-aker": {
        "name": "Vestre Aker",
        "lead": "Trygge byråer for Holmenkollen, Ris, Vinderen og Røa.",
        "body": (
            "Vestre Aker er kjent for store eneboliger og villaer i Holmenkollen, Ris, Vinderen "
            "og Røa, ofte med bratte innkjørsler og krevende adkomst. Byråene i nettverket vårt "
            "har erfaring med store, verdifulle flyttelass og vet hvordan man sikrer møbler og "
            "gjenstander godt på vei ned de svingete veiene."
        ),
        "meta_description": "Flyttebyrå i Vestre Aker — få 3 tilbud gratis fra kvalitetssjekkede byråer som kjenner Holmenkollen, Ris, Vinderen og Røa.",
    },
    "ostensjo": {
        "name": "Østensjø",
        "lead": "Byråer som kjenner Bøler, Skullerud, Manglerud og Oppsal.",
        "body": (
            "Østensjø er en av Oslos mest folkerike bydeler, med Bøler, Skullerud, Manglerud og "
            "Oppsal som store boligområder rundt Østensjøvannet. Flyttebyråene vi samarbeider med "
            "her flytter jevnlig både blokkleiligheter og rekkehus, og kjenner de beste rutene "
            "forbi områdets travleste kryss."
        ),
        "meta_description": "Flyttebyrå i Østensjø — få 3 tilbud gratis fra kvalitetssjekkede byråer som kjenner Bøler, Skullerud, Manglerud og Oppsal.",
    },
}
