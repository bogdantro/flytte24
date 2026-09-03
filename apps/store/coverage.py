"""Structured service-area coverage for businesses.

`Bedrift_info.service_areas` (and `CoverageChangeRequest.service_areas`) is a
list of dicts, one per place a business serves:

    {"place": "Oslo", "pickup": true, "dropoff": true}

`pickup`  — the business takes jobs that *start* in this place.
`dropoff` — the business takes jobs that *end* in this place.

both true  = two-way (jobs to and from the place)
one true   = one-way (e.g. Oslo->Drammen but not Drammen->Oslo)

The onboarding UI is organised by REGION_GROUPS: picking a main city offers a
"select the whole region" shortcut (e.g. "Oslo/Viken" ticks every place under
it) plus a per-place list so a business can also say "Oslo, and also Drammen
and Asker, but not the rest of Viken".
"""

# Main cities — the flat `cities` list has always been these five
# (apps.core.forms.CITY_CHOICES). Each maps to a region group whose first
# entry is the city itself.
REGION_GROUPS = {
    "Oslo/Viken": [
        "Oslo", "Drammen", "Asker", "Bærum", "Lillestrøm", "Ski",
        "Jessheim", "Sandvika", "Moss", "Fredrikstad", "Sarpsborg", "Hønefoss",
    ],
    "Bergen/Vestland": [
        "Bergen", "Askøy", "Os", "Knarvik", "Voss", "Straume",
    ],
    "Stavanger/Rogaland": [
        "Stavanger", "Sandnes", "Haugesund", "Bryne", "Egersund",
    ],
    "Trondheim/Trøndelag": [
        "Trondheim", "Stjørdal", "Melhus", "Orkanger", "Malvik",
    ],
    "Tromsø/Troms": [
        "Tromsø", "Finnsnes", "Bardufoss",
    ],
}

# "Oslo" -> "Oslo/Viken"
MAIN_CITY_TO_REGION = {places[0]: region for region, places in REGION_GROUPS.items()}

# Every place that can appear in service_areas.
ALL_PLACES = [place for places in REGION_GROUPS.values() for place in places]
ALL_PLACES_SET = set(ALL_PLACES)


def region_of(place):
    """The region group a place belongs to, or None."""
    for region, places in REGION_GROUPS.items():
        if place in places:
            return region
    return None


def normalize_service_areas(raw):
    """Coerces arbitrary input (from a form POST or old data) into a clean,
    de-duplicated list of {place, pickup, dropoff} dicts, dropping unknown
    places and any entry that serves neither direction."""
    seen = {}
    for entry in raw or []:
        if not isinstance(entry, dict):
            continue
        place = str(entry.get("place", "")).strip()
        if place not in ALL_PLACES_SET:
            continue
        pickup = bool(entry.get("pickup", True))
        dropoff = bool(entry.get("dropoff", True))
        if not (pickup or dropoff):
            continue
        # Last one wins, but OR the directions if the same place repeats.
        prev = seen.get(place)
        if prev:
            pickup = pickup or prev["pickup"]
            dropoff = dropoff or prev["dropoff"]
        seen[place] = {"place": place, "pickup": pickup, "dropoff": dropoff}
    # Stable order: by region group, then by the group's own place order.
    order = {place: i for i, place in enumerate(ALL_PLACES)}
    return [seen[p] for p in sorted(seen, key=lambda p: order[p])]


def service_areas_to_cities(areas):
    """The flat, legacy `cities` string (main cities only) implied by a
    structured coverage list — so old matching / UI that still reads
    Bedrift_info.cities keeps working."""
    covered_regions = []
    for entry in areas or []:
        region = region_of(entry.get("place", ""))
        main_city = region and REGION_GROUPS[region][0]
        if main_city and main_city not in covered_regions:
            # Only claim the main city if it's actually in the list.
            if any(e.get("place") == main_city for e in areas):
                covered_regions.append(main_city)
    return ", ".join(covered_regions)


def cities_to_service_areas(cities_csv):
    """Best-effort upgrade of a legacy comma `cities` string into structured
    entries (two-way for each named main city) — used to seed the onboarding
    form for a business that only ever set the flat list."""
    out = []
    for raw in (cities_csv or "").split(","):
        place = raw.strip()
        if place in MAIN_CITY_TO_REGION:
            out.append({"place": place, "pickup": True, "dropoff": True})
    return out


def business_serves_move(areas, from_place, to_place):
    """True if a structured coverage list can take a job from `from_place`
    to `to_place` — needs pickup at the origin and dropoff at the
    destination. Place names are matched on a word boundary (so "Ski" does
    not match "Skien"). Falls back to True when the business has no
    structured areas at all (so unconfigured businesses behave as before)."""
    import re

    if not areas:
        return True
    from_text = (from_place or "").lower()
    to_text = (to_place or "").lower()

    def hit(place, text):
        return re.search(r"\b" + re.escape(place.lower()) + r"\b", text) is not None

    can_pick = any(e["pickup"] and hit(e["place"], from_text) for e in areas)
    can_drop = any(e["dropoff"] and hit(e["place"], to_text) for e in areas)
    return can_pick and can_drop
