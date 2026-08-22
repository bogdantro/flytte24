from django.core.management.base import BaseCommand

from apps.core.models import Agency, Article


class Command(BaseCommand):
    help = "Seeds the Agency and Article rows behind /byraer/ and /blogg/. Idempotent — safe to re-run (update_or_create keyed on slug)."

    def handle(self, *args, **options):
        agencies = [
            {
                "slug": "loft", "name": "LØFT", "logo": "images/home/loeftlogo.svg", "logo_blend_multiply": False,
                "tagline": "Flytting med hodet, ikke bare ryggen",
                "short": "Oslo-basert byrå med spesialkompetanse på trange bygårder og verdifullt innbo.",
                "about": [
                    "Vi startet LØFT i 2019 fordi vi var lei av flyttebyråer som behandlet folks eiendeler som stein. Alle hos oss har fagbrev eller har gått i lære hos noen som har det, og vi bruker like mye tid på å planlegge en flytting som på å gjennomføre den.",
                    "Spesialiteten vår er gamle bygårder i indre Oslo. Trange trapper, dører som ikke er standard og heiser som enten ikke finnes eller ikke virker. Vi kommer alltid på befaring før tilbudet, så prisen du får er den du betaler.",
                    "Vi tar imot et begrenset antall jobber i uka. Det gjør at vi kan si nei til å stresse, og ja til å gjøre jobben ordentlig.",
                ],
                "rating": "4.9", "review_count": 87, "jobs_completed": 312, "response_time": "Svarer vanligvis innen 2 timer", "member_since": 2023,
                "services": ["Flyttehjelp", "Pakking", "Flyttevask", "Piano og flygel", "Kunst og antikviteter", "Montering"],
                "areas": ["Grünerløkka", "Gamle Oslo", "St. Hanshaugen", "Sagene", "Frogner", "Nordre Aker"],
                "contact_name": "Marius Halvorsen", "contact_role": "Prosjektleder", "contact_phone": "922 14 087",
                "reviews": [
                    {"name": "Ingrid S.", "date": "2026-07-18", "stars": 5, "service": "Flyttehjelp og pakking", "comment": "Vi bor i fjerde etasje uten heis på Grünerløkka og gruet oss skikkelig. Guttene fra LØFT tok med seg sekkevogner og stropper vi ikke visste fantes, og hele leiligheten var nede på tre timer. Ingenting fikk en ripe."},
                    {"name": "Fredrik B.", "date": "2026-06-02", "stars": 5, "service": "Pianotransport", "comment": "Hadde et gammelt Steinway-piano etter min far som måtte fra Frogner til Nordstrand. De sendte fire mann og et spesialstativ, og var tydelige på hva de kunne og ikke kunne garantere. Profesjonelt hele veien."},
                    {"name": "Anniken H.", "date": "2026-05-21", "stars": 4, "service": "Flyttehjelp", "comment": "Veldig fornøyd med selve flyttingen. Trekker en stjerne fordi de kom 45 minutter senere enn avtalt, men de ga beskjed underveis og tok igjen tiden."},
                    {"name": "Tobias M.", "date": "2026-04-11", "stars": 5, "service": "Flyttehjelp og flyttevask", "comment": "Bestilte flyttevask i tillegg, og den ble godkjent på overtakelsen uten kommentarer. Utleier spurte til og med hvem vi hadde brukt."},
                ],
            },
            {
                "slug": "relok", "name": "relok.", "logo": "images/home/reloklogo.png", "logo_blend_multiply": True,
                "tagline": "Hele Østlandet, hele veien",
                "short": "Stort apparat med egen lagerpark. Tar både privatflyttinger og hele kontorbygg.",
                "about": [
                    "relok. har kjørt flyttebiler siden 2011, og i dag har vi 24 ansatte og elleve biler. Størrelsen gjør at vi nesten alltid kan tilby datoen du ønsker, også i månedsskiftene når resten av bransjen er utsolgt.",
                    "Vi har eget lager på Alnabru med døgnbemannet adgangskontroll. Det er nyttig når overtakelse og innflytting ikke skjer samme dag, noe som er oftere enn folk tror.",
                    "Halvparten av omsetningen vår kommer fra bedriftsflytting. Det har lært oss å planlegge presist: når et kontor skal være oppe igjen mandag morgen, finnes det ingen fleksibilitet. Den planleggingen tar vi med oss inn i privatjobbene også.",
                ],
                "rating": "4.7", "review_count": 214, "jobs_completed": 1840, "response_time": "Svarer vanligvis innen 1 time", "member_since": 2022,
                "services": ["Flyttehjelp", "Kontorflytting", "Lagring", "Pakking", "Flyttevask", "Avfallshåndtering"],
                "areas": ["Hele Oslo", "Bærum", "Asker", "Lillestrøm", "Drammen", "Follo"],
                "contact_name": "Sara Nyland", "contact_role": "Kundeansvarlig", "contact_phone": "477 03 512",
                "reviews": [
                    {"name": "Petter L.", "date": "2026-08-01", "stars": 5, "service": "Kontorflytting", "comment": "Flyttet 40 arbeidsplasser fra Skøyen til Nydalen over en helg. Alt sto klart mandag morgen, inkludert skjermer og dokkingstasjoner. Imponerende logistikk."},
                    {"name": "Camilla R.", "date": "2026-06-27", "stars": 5, "service": "Flyttehjelp og lagring", "comment": "Vi måtte ut av gammel bolig tre uker før vi fikk nøklene til den nye. relok. mellomlagret alt på Alnabru og kjørte det ut igjen på dagen vi hadde avtalt. Løste et problem jeg trodde skulle bli dyrt og vanskelig."},
                    {"name": "Håkon E.", "date": "2026-05-09", "stars": 4, "service": "Flyttehjelp", "comment": "Effektive og hyggelige. Kunne ønsket meg litt tydeligere informasjon om hva som var inkludert i prisen på forhånd, men da jeg spurte fikk jeg raskt svar."},
                    {"name": "Nina D.", "date": "2026-03-30", "stars": 5, "service": "Flyttehjelp Oslo til Drammen", "comment": "Lang flytting med mye tungt. To mann jobbet jevnt og trutt i sju timer uten å klage én gang. Fastprisen holdt selv om det tok lengre tid enn estimert."},
                ],
            },
            {
                "slug": "flyttefoten", "name": "Flyttefoten", "logo": "images/home/flyttefotenlogo.png", "logo_blend_multiply": False,
                "tagline": "Familiedrevet siden 2014",
                "short": "Lite byrå med faste folk. Kjent for å ta godt vare på studenter og førstegangsflyttere.",
                "about": [
                    "Flyttefoten er et familieforetak. Pappa startet med én varebil i 2014, i dag er vi seks stykker og tre biler, og de fleste av oss er i slekt eller har vokst opp i samme gate.",
                    "Vi er små, og det er et bevisst valg. Du snakker med den samme personen fra første telefon til siste eske er båret inn, og det er stor sjanse for at du møter noen av oss igjen neste gang du flytter.",
                    "Vi har en myk plass i hjertet for folk som flytter for første gang. Studenter, nyutdannede, folk som flytter fra barndomshjemmet. Vi tar oss tid til å forklare hva som lønner seg, også når svaret er at du klarer deg fint uten oss.",
                ],
                "rating": "4.8", "review_count": 63, "jobs_completed": 428, "response_time": "Svarer vanligvis samme dag", "member_since": 2024,
                "services": ["Flyttehjelp", "Studentflytting", "Pakking", "Flyttevask", "Bortkjøring"],
                "areas": ["Gamle Oslo", "Grünerløkka", "Sagene", "Bjerke", "Østensjø", "Nordstrand"],
                "contact_name": "Jonas Ødegård", "contact_role": "Daglig leder", "contact_phone": "986 42 210",
                "reviews": [
                    {"name": "Sofie T.", "date": "2026-07-30", "stars": 5, "service": "Studentflytting", "comment": "Flyttet fra hybel på Bjerke til kollektiv på Løkka. De ga meg et tilbud som var billigere enn jeg hadde budsjettert, og sa rett ut at jeg ikke trengte pakketjenesten deres. Sjeldent å oppleve."},
                    {"name": "Emil K.", "date": "2026-06-14", "stars": 5, "service": "Flyttehjelp", "comment": "Jonas kom selv på befaring og husket navnet mitt da de dukket opp tre uker senere. Små ting, men det gjør at man føler seg trygg."},
                    {"name": "Maria V.", "date": "2026-04-25", "stars": 4, "service": "Flyttehjelp og bortkjøring", "comment": "Tok med seg gammel sofa og et skap til gjenbruksstasjonen samtidig. Praktisk. Litt trangt om plassen i bilen, så vi måtte ta to turer, men de tok ikke ekstra betalt for det."},
                    {"name": "Lars-Petter N.", "date": "2026-02-08", "stars": 5, "service": "Flyttehjelp", "comment": "Flyttet mamma til leilighet med livsløpsstandard på Nordstrand. De var tålmodige med henne, bar inn alt på riktig plass og satte sammen senga uten at vi spurte."},
                ],
            },
            {
                "slug": "flytteby", "name": "Flytteby", "logo": "images/home/flytteblogo.png", "logo_blend_multiply": False,
                "tagline": "Nøkkelferdig flytting fra dør til dør",
                "short": "Full pakke: pakking, flytting, vask og montering. For deg som vil slippe å tenke.",
                "about": [
                    "Flytteby ble startet av to tidligere hotelldirektører som mente flyttebransjen kunne lære noe av servicebransjen. Derfor er vi bygget rundt én idé: du skal kunne dra på jobb om morgenen og komme hjem til en ferdig innflyttet bolig.",
                    "Vi pakker, kjører, bærer inn, monterer møbler, henger opp bilder og tar med oss emballasjen ut igjen. Flyttevasken av den gamle boligen skjer parallelt, av vårt eget vaskelag, ikke en underleverandør.",
                    "Det koster mer enn å bære selv. Til gjengjeld er det ingenting du må huske, og vi har aldri hatt en kunde som måtte ta fri fra jobb på flyttedagen.",
                ],
                "rating": "4.6", "review_count": 129, "jobs_completed": 764, "response_time": "Svarer vanligvis innen 3 timer", "member_since": 2021,
                "services": ["Nøkkelferdig flytting", "Pakking og utpakking", "Flyttevask", "Montering", "Lagring", "Kontorflytting"],
                "areas": ["Frogner", "Ullern", "Vestre Aker", "Nordre Aker", "Nordstrand", "Bærum"],
                "contact_name": "Elise Aarø", "contact_role": "Flyttekoordinator", "contact_phone": "934 77 601",
                "reviews": [
                    {"name": "Kristin A.", "date": "2026-07-05", "stars": 5, "service": "Nøkkelferdig flytting", "comment": "Dro på jobb fra en full leilighet på Majorstuen og kom hjem til et ferdig innredet hus på Vinderen. Bøkene sto til og med i riktig rekkefølge i hylla. Verdt hver krone."},
                    {"name": "Ole Martin S.", "date": "2026-06-19", "stars": 4, "service": "Flytting og montering", "comment": "Veldig god service og ryddig gjennomføring. Prisen er i øvre sjikt, og det bør man vite på forhånd. Men de leverte nøyaktig det de lovet."},
                    {"name": "Beate W.", "date": "2026-05-02", "stars": 5, "service": "Flytting, vask og lagring", "comment": "Vi hadde en kaotisk periode med salg og kjøp som ikke gikk opp. Elise holdt oversikten for oss og flyttet datoene to ganger uten å blunke."},
                    {"name": "Andreas G.", "date": "2026-03-14", "stars": 4, "service": "Nøkkelferdig flytting", "comment": "Alt gikk bra, men vi måtte etterspørre utpakkingen av kjøkkenet som lå inne i avtalen. De kom tilbake dagen etter og fullførte uten diskusjon."},
                ],
            },
        ]

        articles = [
            {
                "slug": "hva-er-viktig-a-tenke-pa-nar-du-skal-flytte",
                "title": "Hva er viktig å tenke på når du skal flytte?",
                "ingress": "En flytting blir sjelden stressende fordi den er vanskelig. Den blir stressende fordi mye skjer samtidig. Her er det som faktisk er viktig å få på plass, i riktig rekkefølge.",
                "header_image": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?q=80&w=2400&auto=format&fit=crop",
                "date": "2026-08-04",
                "read_minutes": 6,
                "blocks": [
                    {"type": "p", "text": "De fleste undervurderer ikke selve flyttedagen, men ukene før. Nøkkelen til en rolig flytting er å ta beslutningene tidlig, slik at de siste dagene bare handler om gjennomføring. Denne guiden går gjennom det viktigste, fra seks uker før til dagen du leverer nøklene."},
                    {"type": "h2", "text": "Seks uker før: ta de store valgene"},
                    {"type": "p", "text": "Det første du bør avklare er om du skal flytte selv eller bruke flyttebyrå. Regnestykket er ofte jevnere enn folk tror: leiebil, drivstoff, bæring, forsikring og en helg eller to av din egen tid mot en fast pris fra et byrå som gjør alt på én dag. Bor du i leilighet uten heis, eller har du tunge møbler, taler det meste for byrå."},
                    {"type": "p", "text": "Innhent tilbud fra flere byråer samtidig, og be om fastpris fremfor timepris når det er mulig. Da vet du hva flyttingen koster før den starter, og du slipper overraskelser hvis dagen tar lengre tid enn planlagt."},
                    {"type": "cta"},
                    {"type": "h2", "text": "Fire uker før: rydd før du pakker"},
                    {"type": "p", "text": "Alt du ikke tar med deg, slipper du å pakke, bære og betale for. Gå gjennom rom for rom og sorter i tre bunker: behold, gi bort eller selg, og kast. Møbler og klær i god stand kan leveres til gjenbruksstasjoner eller selges på Finn. Spesialavfall som maling og elektronikk må til miljøstasjonen."},
                    {"type": "p", "text": "Meld adresseendring til Posten og Folkeregisteret. Det tar noen minutter på nett, og gjelder fra datoen du velger. Husk også å flytte eller si opp strømavtale, internett og innboforsikring. Innboforsikringen bør gjelde begge boliger i overgangsperioden."},
                    {"type": "image", "src": "/images/boxes-and-plants.jpg", "alt": "Flytteesker og planter stablet i en stue", "caption": "Merk eskene med rom og innhold, ikke bare «diverse»."},
                    {"type": "h2", "text": "To uker før: pakk systematisk"},
                    {"type": "list", "items": [
                        "Pakk ett rom om gangen, og merk hver eske med rom og kort innhold.",
                        "Tunge ting i små esker, lette ting i store. Ryggen din takker deg.",
                        "Pakk en «første natt»-bag med sengetøy, lader, toalettsaker og kaffe.",
                        "Ta bilder av elektronikk-kabling før du kobler fra.",
                        "La klær henge i garderobeesker i stedet for å brette alt.",
                    ]},
                    {"type": "p", "text": "Bruker du flyttebyrå, avklar hva de pakker og hva du pakker selv. Mange byråer tilbyr full pakking, og det er ofte rimeligere enn folk tror. Uansett bør verdisaker, dokumenter og medisiner fraktes av deg personlig."},
                    {"type": "h2", "text": "Flyttedagen: logistikk og nøkler"},
                    {"type": "p", "text": "Sørg for parkering nær inngangen i begge ender, og reserver heisen hvis du bor i blokk. Gå en siste runde i den gamle boligen når alt er ute: sjekk skap, loft, bod og kjeller. Les av strømmåleren og ta bilde av den, både der du flytter fra og dit du flytter."},
                    {"type": "p", "text": "Og til slutt: senk skuldrene. Med beslutningene tatt på forhånd er flyttedagen bare gjennomføring. Det meste som kan gå galt, er allerede håndtert i planen din."},
                ],
            },
            {
                "slug": "hva-koster-det-a-bruke-flyttebyra-i-2026",
                "title": "Hva koster det å bruke flyttebyrå i 2026?",
                "ingress": "Prisen på flyttebyrå varierer mer enn de fleste tjenester du kjøper. Her er hva flyttinger faktisk koster i 2026, hva som driver prisen, og hvordan du unngår å betale for mye.",
                "header_image": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?q=80&w=2400&auto=format&fit=crop",
                "date": "2026-07-21",
                "read_minutes": 5,
                "blocks": [
                    {"type": "p", "text": "Spør du tre byråer om pris på samme flytting, kan du få svar som spriker med flere tusen kroner. Det betyr ikke at noen prøver å lure deg. Det betyr at pris avhenger av ting du kan påvirke: tidspunkt, tilgjengelighet og hvor mye du gjør selv."},
                    {"type": "h2", "text": "Typiske priser i 2026"},
                    {"type": "list", "items": [
                        "Liten leilighet (1–2 rom, samme by): 4 000–8 000 kr",
                        "Vanlig leilighet (3 rom, samme by): 8 000–15 000 kr",
                        "Rekkehus eller enebolig (samme by): 15 000–30 000 kr",
                        "Flytting mellom byer, for eksempel Oslo–Bergen: 15 000–40 000 kr",
                        "Full pakking i tillegg: vanligvis 3 000–8 000 kr ekstra",
                    ]},
                    {"type": "p", "text": "Prisene er veiledende og forutsetter seriøse, forsikrede byråer. Timepris ligger typisk på 900–1 400 kr for to mann og bil. Ved timepris bør du alltid be om et estimat på totaltid, og gjerne et pristak."},
                    {"type": "h2", "text": "Dette driver prisen opp eller ned"},
                    {"type": "p", "text": "Volum er den største faktoren: antall kubikkmeter avgjør hvor stor bil og hvor mange folk som trengs. Deretter kommer tilgjengelighet. Trapp uten heis, lang bæreavstand fra dør til bil og trange oppganger gir flere arbeidstimer. En flytting fra fjerde etasje uten heis kan koste 20–30 prosent mer enn samme volum med heis."},
                    {"type": "p", "text": "Tidspunktet betyr også mye. Månedsskifter, helger og sommermånedene er høysesong. Kan du flytte en tirsdag midt i måneden, er det ofte flere tusen kroner å spare."},
                    {"type": "cta"},
                    {"type": "h2", "text": "Slik unngår du å betale for mye"},
                    {"type": "list", "items": [
                        "Innhent alltid flere tilbud på samme grunnlag, med likt volum og like betingelser.",
                        "Be om fastpris når flyttingen er oversiktlig.",
                        "Sjekk at byrået er registrert i Brønnøysund og har ansvarsforsikring.",
                        "Rydd og kvitt deg med ting før befaring, så prises et mindre volum.",
                        "Vær fleksibel på dato hvis du kan.",
                    ]},
                    {"type": "p", "text": "Vær skeptisk til tilbud som er langt under alle andre. Useriøse aktører sparer inn differansen på manglende forsikring, svart arbeid eller tillegg som dukker opp på fakturaen. Et ryddig tilbud skal spesifisere hva som inngår: bil, antall folk, bæring, montering og forsikring."},
                    {"type": "h2", "text": "Husk fradraget i skattemeldingen? Nei."},
                    {"type": "p", "text": "Et vanlig spørsmål: flytteutgifter er som hovedregel ikke fradragsberettiget for privatpersoner, med mindre flyttingen skjer på grunn av jobb og arbeidsgiver ikke dekker den. Sjekk skatteetaten.no for detaljene som gjelder din situasjon."},
                    {"type": "p", "text": "Kort oppsummert: prisen på flyttebyrå er ikke hugget i stein. Med flere tilbud, riktig tidspunkt og et ryddig volum får du samme jobb gjort til en lavere pris."},
                ],
            },
            {
                "slug": "flyttevask-dette-ma-vaere-gjort-for-du-leverer-noklene",
                "title": "Flyttevask: dette må være gjort før du leverer nøklene",
                "ingress": "Flyttevasken er det siste du gjør i boligen, og det hyppigste konflikttemaet mellom utleier og leietaker. Her er sjekklisten som sørger for at du får godkjent vasken på første forsøk.",
                "header_image": "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?q=80&w=2400&auto=format&fit=crop",
                "date": "2026-06-30",
                "read_minutes": 7,
                "blocks": [
                    {"type": "p", "text": "En flyttevask er noe annet enn en vanlig helgevask. Kravet er at boligen skal være like ren som da du overtok den, og det inkluderer alt du vanligvis hopper over: inni ovnen, bak hvitevarene, oppå skapene og i ventilene. Setter du av tid til det, eller kjøper tjenesten, slipper du trekk i depositum og diskusjoner på overtakelsen."},
                    {"type": "h2", "text": "Kjøkkenet: der de fleste feiler"},
                    {"type": "list", "items": [
                        "Stekeovn: vask innvendig, inkludert rister og stekebrett. Bruk ovnsrens og la den virke.",
                        "Kjøleskap og fryser: tøm, avrim og vask innvendig. La dørene stå på gløtt.",
                        "Ventilator: vask filter og avfetting av selve viften.",
                        "Skap og skuffer: tørk innvendig og utvendig, også oppå skapene.",
                        "Bak og under hvitevarer: trekk frem komfyr og kjøleskap og vask gulvet bak.",
                    ]},
                    {"type": "p", "text": "Ovnen og ventilatorfilteret er de to punktene som oftest fører til at flyttevask underkjennes. Sett av god tid til begge, eller sjekk at de står eksplisitt i tilbudet hvis du kjøper vasken."},
                    {"type": "h2", "text": "Bad: kalk og sluk"},
                    {"type": "list", "items": [
                        "Rens sluk i dusj og på gulv, og fjern hår og såperester.",
                        "Fjern kalk på fliser, dusjvegger og armaturer med kalkfjerner.",
                        "Vask toalettet grundig, også bak og rundt festene.",
                        "Tørk av rør, lister og ventiler.",
                    ]},
                    {"type": "image", "src": "/images/moving-couple.jpg", "alt": "To personer i gang med flytting og rengjøring", "caption": "Flyttevasken går raskere når boligen allerede er tom for esker."},
                    {"type": "h2", "text": "Resten av boligen"},
                    {"type": "list", "items": [
                        "Vinduer: vask innvendig og utvendig der det er tilgjengelig, inkludert karmer og mellom glassene der det går.",
                        "Lister, dørkarmer og stikkontakter: tørk av alt.",
                        "Ventiler: støvsug og tørk av friskluftsventiler.",
                        "Gulv: støvsug og vask, inkludert under radiatorer og i kroker.",
                        "Bod, loft og garasje: tøm helt og kost gulvet.",
                    ]},
                    {"type": "h2", "text": "Gjøre det selv eller kjøpe flyttevask?"},
                    {"type": "p", "text": "En profesjonell flyttevask av en vanlig leilighet koster typisk 2 500–5 500 kr i 2026, avhengig av størrelse og stand. Da følger det normalt med garanti: blir vasken underkjent på overtakelsen, kommer firmaet tilbake og utbedrer kostnadsfritt. For mange er det verdt prisen alene, siden du slipper å stå i diskusjonen selv."},
                    {"type": "p", "text": "Velger du å vaske selv, regn med en hel dag for en leilighet og gjerne en helg for et hus. Vask ovenfra og ned i hvert rom, og ta gulvet til slutt. Dokumenter resultatet med bilder når du er ferdig, datostemplet i mobilen, i tilfelle det blir uenighet i etterkant."},
                    {"type": "cta"},
                    {"type": "h2", "text": "Sjekklisten før nøkkeloverlevering"},
                    {"type": "list", "items": [
                        "Alle rom tomme, også bod og loft.",
                        "Ovn, kjøleskap og ventilator godkjent-rene.",
                        "Sluk renset og kalk fjernet på badet.",
                        "Vinduer, lister og ventiler tørket av.",
                        "Strøm lest av og bilder tatt.",
                        "Alle nøkler samlet, også til postkasse og bod.",
                    ]},
                    {"type": "p", "text": "Med denne listen i hånden er flyttevasken en jobb med en tydelig slutt, ikke et åpent prosjekt. Og leverer du nøklene til en ren bolig, er sjansen stor for at både depositum og forholdet til utleier forblir intakt."},
                ],
            },
        ]

        for data in agencies:
            slug = data.pop("slug")
            Agency.objects.update_or_create(slug=slug, defaults=data)

        for data in articles:
            slug = data.pop("slug")
            Article.objects.update_or_create(slug=slug, defaults=data)

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(agencies)} agencies and {len(articles)} articles."))
