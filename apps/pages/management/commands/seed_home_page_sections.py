from django.core.management.base import BaseCommand

from apps.pages.models import Page, PageSection


class Command(BaseCommand):
    help = "Seeds the home page's Page/PageSection rows from its current hardcoded copy (apps/core/templates/core/home.html). Idempotent — safe to re-run."

    def handle(self, *args, **options):
        page, created = Page.objects.get_or_create(
            template_key="home",
            defaults={
                "title": "Forside",
                "slug": "forside",
                "path": "/",
                "status": "published",
            },
        )

        sections = [
            dict(
                order=1,
                section_type="hero",
                heading="Vi finner det beste flyttebyrået for deg",
                subheading="Kobly kobler deg med kvalitetssjekkede byråer i ditt område",
                button_label="Få 3 tilbud gratis",
                button_href="/flytteforesporsel/",
                extra_json={
                    "eyebrow": "Norges smarteste tilbudstjeneste",
                    "card_title": "La firmaene konkurrere om deg",
                    "card_body": "Vi kobler deg med 3 håndplukkede, kvalitetssjekkede byråer i ditt område.",
                },
            ),
            dict(
                order=2,
                section_type="stats",
                extra_json={
                    "items": [
                        {"value": "100%", "label": "Gratis og uforpliktende"},
                        {"value": "1 min", "label": "Å fylle ut skjema"},
                        {"value": "5 000+", "label": "Fornøyde kunder"},
                        {"value": "4.8/5", "label": "Gjennomsnittlig vurdering"},
                    ]
                },
            ),
            dict(
                order=3,
                section_type="how_it_works",
                heading="Slik fungerer det",
                button_label="Få 3 tilbud gratis",
                button_href="/flytteforesporsel/",
                extra_json={
                    "steps": [
                        {"title": "Fyll ut skjema", "body": "Svar på noen enkle spørsmål. Tar under to minutter."},
                        {"title": "Vi kobler deg med de beste", "body": "Tre kvalitetssjekkede byråer kobles med din flytting."},
                        {"title": "Velg tilbud", "body": "Sammenlign, velg ditt byrå, og avtal resten direkte med dem."},
                    ]
                },
            ),
            dict(
                order=4,
                section_type="testimonials",
                heading="Hva sier kundene våre?",
                extra_json={
                    "items": [
                        {
                            "quote": "Kobly fant meg tre seriøse byråer i løpet av få timer. Sparte meg for både tid og masse penger.",
                            "name": "Kristoffer Skogen",
                            "meta": "Privatkunde, Bergen",
                        },
                        {
                            "quote": "Vi fikk skreddersydde tilbud uten å måtte ringe ti forskjellige byråer selv. Anbefales på det varmeste.",
                            "name": "Sunniva Thune",
                            "meta": "Næringsflytting, Oslo",
                        },
                        {
                            "quote": "Trygg og enkel prosess fra start til slutt. Byråene som tok kontakt var profesjonelle og hyggelige.",
                            "name": "Eivind Johansen",
                            "meta": "Privatkunde, Trondheim",
                        },
                    ]
                },
            ),
            dict(
                order=5,
                section_type="trust",
                heading="Norges smarteste tilbudstjeneste",
                body_text="Kobly flytter ikke selv — vi samler byråene som gjør det best, og kobler deg med tre som passer akkurat din flytting.",
                button_label="Få 3 tilbud gratis",
                button_href="/flytteforesporsel/",
                extra_json={"secondary_label": "Møt byråene", "secondary_href": "/byraer/"},
            ),
            dict(
                order=6,
                section_type="services",
                heading="Alt du trenger på ett sted",
                extra_json={
                    "items": [
                        {"title": "Flyttehjelp", "body": "Pakking, bæring og transport, trygt fra dør til dør. Vi finner byråer som tar hele jobben. Du velger hvor mye hjelp du trenger."},
                        {"title": "Flyttevask", "body": "Godkjente vaskebyråer med garanti. Perfekt før innflytting eller når leiekontrakten krever en grundig sluttvask."},
                        {"title": "Lagring", "body": "Trygg kortsiktig eller langsiktig oppbevaring i ditt nærområde, med forsikring og fleksibel tilgang."},
                        {"title": "Utlandsflytting", "body": "Spesialiserte byråer som håndterer toll, containere og papirarbeid. Både flytting ut av Norge og hjem igjen."},
                        {"title": "Kontorflytting", "body": "Erfarne partnere som flytter kontor, lager og næringslokaler utenom arbeidstid. IT, møbler og arkiv håndtert profesjonelt."},
                        {"title": "Dødsbo", "body": "Tømming og ryddighet med respekt. Byråer med erfaring fra bobehandling av innbo."},
                    ]
                },
            ),
            dict(
                order=7,
                section_type="cities",
                heading="Flytter du i en av disse byene?",
                body_text="Vi har kvalitetssjekkede byråer som tar oppdrag i hele landet. Velg byen din for å komme raskere i gang.",
                extra_json={
                    "items": [
                        {"name": "Oslo", "href": "/oslo/"},
                        {"name": "Bergen", "href": "/bergen/"},
                        {"name": "Trondheim", "href": "/trondheim/"},
                        {"name": "Stavanger", "href": "/stavanger/"},
                        {"name": "Tromsø", "href": "/tromso/"},
                    ]
                },
            ),
            dict(
                order=8,
                section_type="faq",
                heading="Ofte stilte spørsmål",
                extra_json={
                    "items": [
                        {"question": "Hva koster det å bruke Kobly?", "answer": "Det er helt gratis og uforpliktende å få tilbud gjennom Kobly. Du betaler kun for selve flyttejobben — direkte til byrået du velger."},
                        {"question": "Hvor mange byråer kontaktes?", "answer": "Vi kobler deg med tre håndplukkede, kvalitetssjekkede byråer i ditt område. Slik kan du sammenligne pris og tjenester før du bestemmer deg."},
                        {"question": "Hvor lang tid tar det før jeg får tilbud?", "answer": "De fleste mottar tilbud på e-post innen 24 timer etter at forespørselen er sendt inn."},
                        {"question": "Hvordan velger Kobly hvilke byråer som passer for meg?", "answer": "Vi matcher basert på adresse, type flytting (privat, bedrift, internasjonal), boligtype og ønsket dato. Bare byråer med dokumentert erfaring og gode kundeanmeldelser blir koblet på."},
                        {"question": "Er jeg forpliktet til å velge ett av byråene?", "answer": "Nei. Du velger selv om du vil bruke et av byråene som tar kontakt, eller takke nei. Det er helt uforpliktende."},
                    ]
                },
            ),
        ]

        for data in sections:
            section_type = data.pop("section_type")
            PageSection.objects.update_or_create(
                page=page, section_type=section_type, defaults=data
            )

        verb = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{verb} '{page.title}' with {len(sections)} sections."))
