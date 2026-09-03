# apps/leads/property/normalizer.py
#
# The ONE place external responses become our internal shape. Nothing else in
# the codebase should know a provider's field names.
#
# Two inputs get normalized here:
#   * a Kartverket / Geonorge address hit           -> normalize_address()
#   * a building-data provider's raw payload         -> normalize_<provider>_building()
#
# assemble_normalized() stitches an address-normalization and a
# building-normalization into the final structure the API returns.
#
# HARD RULE: never invent, estimate, or derive a value. If the source doesn't
# carry it, the normalized field is None. No computing BRA, byggeår, floor
# counts or unit areas from anything.

import logging

from .exceptions import InvalidProviderResponse
from .unit_codes import floor_from_unit_code

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Empty templates — the canonical shape, single source of truth for keys.
# --------------------------------------------------------------------------

def _empty_address():
    return {
        "formatted": None,
        "street": None,
        "house_number": None,
        "house_letter": None,
        "postal_code": None,
        "postal_city": None,
        "municipality": None,
        "municipality_number": None,
        "county": None,
        "latitude": None,
        "longitude": None,
    }


def _empty_property():
    return {"gnr": None, "bnr": None, "fnr": None, "snr": None}


def _empty_building():
    return {
        "building_number": None,
        "building_type": None,
        "building_status": None,
        "construction_year": None,
        "bra_m2": None,
        "gross_area_m2": None,
        "number_of_floors": None,
        "has_elevator": None,
        "residential_unit_count": None,
    }


# --------------------------------------------------------------------------
# Address (Geonorge)
# --------------------------------------------------------------------------

def normalize_address(hit):
    """Normalize one Geonorge `adresser/v1/sok` result object.

    Returns {"address": {...}, "property": {...}}. Missing pieces stay None —
    Geonorge is reliable for the address block but `festenummer` / section
    numbers are often absent, and that's fine.
    """
    if not isinstance(hit, dict):
        raise InvalidProviderResponse(detail="Geonorge hit was not an object")

    point = hit.get("representasjonspunkt") or {}
    poststed = hit.get("poststed")
    postnummer = hit.get("postnummer")
    street = hit.get("adressenavn")
    house_number = hit.get("nummer")
    house_letter = hit.get("bokstav") or None
    adressetekst = hit.get("adressetekst") or _join_address_text(street, house_number, house_letter)

    address = _empty_address()
    address.update(
        formatted=_formatted(adressetekst, postnummer, poststed),
        street=street or None,
        house_number=_str_or_none(house_number),
        house_letter=house_letter,
        postal_code=_str_or_none(postnummer),
        postal_city=_titlecase(poststed),
        municipality=_titlecase(hit.get("kommunenavn")),
        municipality_number=_str_or_none(hit.get("kommunenummer")),
        county=None,  # not in the basic Geonorge address response — stays null
        latitude=_float_or_none(point.get("lat")),
        longitude=_float_or_none(point.get("lon")),
    )

    prop = _empty_property()
    prop.update(
        gnr=_str_or_none(hit.get("gardsnummer")),
        bnr=_str_or_none(hit.get("bruksnummer")),
        fnr=_str_or_none(hit.get("festenummer")) if hit.get("festenummer") else None,
        snr=_str_or_none(hit.get("undernummer")) if hit.get("undernummer") else None,
    )
    return {"address": address, "property": prop}


def _join_address_text(street, number, letter):
    if not street:
        return None
    tail = f" {number}" if number not in (None, "") else ""
    tail += letter or ""
    return f"{street}{tail}"


def _formatted(adressetekst, postnummer, poststed):
    if not adressetekst:
        return None
    if postnummer and poststed:
        return f"{adressetekst}, {postnummer} {_titlecase(poststed)}"
    return adressetekst


# --------------------------------------------------------------------------
# Building — mock provider payload
# --------------------------------------------------------------------------
#
# The mock payload deliberately mirrors Matrikkelen "bygning" concepts (see
# providers/mock.py) so this function does real mapping work, and so the shape
# is a sensible target for whatever the Norkart mapping eventually produces.

def normalize_mock_building(raw):
    if not isinstance(raw, dict):
        raise InvalidProviderResponse(detail="mock payload was not an object")

    bygninger = raw.get("bygninger")
    if not isinstance(bygninger, list) or not bygninger:
        # A well-formed payload that simply has no buildings on the property.
        return {"building": None, "buildings": [], "floors": [], "units": []}

    normalized_buildings = [_normalize_one_mock_building(b) for b in bygninger]

    if len(normalized_buildings) == 1:
        only = normalized_buildings[0]
        return {
            "building": only["building"],
            "buildings": [],
            "floors": only["floors"],
            "units": only["units"],
        }

    # More than one building on the property. Prefer the one flagged primary by
    # the payload; if none is flagged, hand the frontend a picker list.
    primary = next((b for b in normalized_buildings if b["is_primary"]), None)
    if primary is not None:
        return {
            "building": primary["building"],
            "buildings": [_building_summary(b) for b in normalized_buildings],
            "floors": primary["floors"],
            "units": primary["units"],
        }
    return {
        "building": None,
        "buildings": [_building_summary(b) for b in normalized_buildings],
        "floors": [],
        "units": [],
    }


def _normalize_one_mock_building(b):
    if not isinstance(b, dict):
        raise InvalidProviderResponse(detail="mock building entry was not an object")

    building = _empty_building()
    building.update(
        building_number=_str_or_none(b.get("bygningsnummer")),
        building_type=_nested_beskrivelse(b.get("bygningstype")),
        building_status=_nested_beskrivelse(b.get("bygningsstatus")),
        construction_year=_int_or_none(b.get("byggeaar")),
        bra_m2=_int_or_none(b.get("bruksareal")),
        gross_area_m2=_int_or_none(b.get("bruttoareal")),
        number_of_floors=_int_or_none(b.get("antallEtasjer")),
        has_elevator=_bool_or_none(b.get("harHeis")),
        residential_unit_count=_int_or_none(b.get("antallBoenheter")),
    )

    floors = []
    for f in b.get("etasjer") or []:
        if not isinstance(f, dict):
            continue
        floors.append({
            "floor": _str_or_none(f.get("etasjenummer")),
            "bra_m2": _int_or_none(f.get("bruksareal")),
        })

    units = []
    for u in b.get("bruksenheter") or []:
        if not isinstance(u, dict):
            continue
        unit_number = _str_or_none(u.get("bruksenhetsnummer"))
        explicit_floor = _str_or_none(u.get("etasje"))
        units.append({
            "unit_id": _str_or_none(u.get("id")) or unit_number,
            "unit_number": unit_number,
            # Prefer the provider's own floor; only fall back to the unit code.
            "floor": explicit_floor or floor_from_unit_code(unit_number),
            "bra_m2": _int_or_none(u.get("bruksareal")),
            "type": _str_or_none(u.get("bruksenhetstype")),
        })

    mx = b.get("matrikkelenhet") or {}
    return {
        "building": building,
        "floors": floors,
        "units": units,
        "is_primary": bool(b.get("primaerBygning")),
        "_label": _nested_beskrivelse(b.get("bygningstype")) or "Bygg",
        "_id": _str_or_none(b.get("bygningsnummer")) or _str_or_none(b.get("id")),
        "_matrikkel": {
            "gnr": _str_or_none(mx.get("gardsnummer")),
            "bnr": _str_or_none(mx.get("bruksnummer")),
        },
    }


def _building_summary(nb):
    """Full per-building normalization, kept in the `buildings` list so a
    frontend building-picker choice can be resolved by
    PropertyLookupService without another provider call."""
    return {
        "id": nb["_id"],
        "label": nb["_label"],
        "type": nb["building"]["building_type"],
        "building": nb["building"],
        "floors": nb["floors"],
        "units": nb["units"],
    }


# --------------------------------------------------------------------------
# Building — Norkart payload  (MAPPINGS UNVERIFIED)
# --------------------------------------------------------------------------

def normalize_norkart_building(raw):
    """Map a Norkart Bygning API response to our normalized building structure.

    !!! The field paths below are NOT verified against Norkart documentation. !!!
    Norkart access requires credentials and private API docs we do not have in
    this repository. Every mapping is a placeholder: confirm the real response
    field names, then replace each `_dig(...)` path. Do not ship
    PROPERTY_PROVIDER=norkart until this is done (providers/__init__.py refuses
    to build the provider without credentials, and this function will simply
    return mostly-None until the paths are correct).

    The function is intentionally defensive — an unrecognised shape yields a
    normalized structure full of None rather than an exception, EXCEPT when the
    top-level payload isn't even a JSON object.
    """
    if not isinstance(raw, dict):
        raise InvalidProviderResponse(detail="Norkart payload was not an object")

    # TODO(norkart): confirm the list key holding buildings for the property.
    raw_buildings = _dig(raw, "bygninger") or _dig(raw, "buildings") or []
    if not isinstance(raw_buildings, list) or not raw_buildings:
        return {"building": None, "buildings": [], "floors": [], "units": []}

    # TODO(norkart): confirm how Norkart marks the building tied to the address,
    # and whether multiple buildings even come back on one call.
    first = raw_buildings[0] if isinstance(raw_buildings[0], dict) else {}

    building = _empty_building()
    building.update(
        building_number=_str_or_none(_dig(first, "bygningsnummer")),          # TODO(norkart)
        building_type=_str_or_none(_dig(first, "bygningstype", "beskrivelse")),  # TODO(norkart)
        building_status=_str_or_none(_dig(first, "bygningsstatus", "beskrivelse")),  # TODO(norkart)
        construction_year=_int_or_none(_dig(first, "byggeaar")),              # TODO(norkart)
        bra_m2=_int_or_none(_dig(first, "bruksareal")),                       # TODO(norkart)
        gross_area_m2=_int_or_none(_dig(first, "bruttoareal")),               # TODO(norkart)
        number_of_floors=_int_or_none(_dig(first, "antallEtasjer")),          # TODO(norkart)
        has_elevator=_bool_or_none(_dig(first, "harHeis")),                   # TODO(norkart)
        residential_unit_count=_int_or_none(_dig(first, "antallBoenheter")),  # TODO(norkart)
    )

    floors = []  # TODO(norkart): map per-floor area rows if the API returns them.

    units = []
    for u in _dig(first, "bruksenheter") or []:  # TODO(norkart): confirm key
        if not isinstance(u, dict):
            continue
        unit_number = _str_or_none(_dig(u, "bruksenhetsnummer"))  # TODO(norkart)
        explicit_floor = _str_or_none(_dig(u, "etasje"))          # TODO(norkart)
        units.append({
            "unit_id": _str_or_none(_dig(u, "id")) or unit_number,
            "unit_number": unit_number,
            "floor": explicit_floor or floor_from_unit_code(unit_number),
            "bra_m2": _int_or_none(_dig(u, "bruksareal")),        # TODO(norkart)
            "type": _str_or_none(_dig(u, "bruksenhetstype")),     # TODO(norkart)
        })

    return {"building": building, "buildings": [], "floors": floors, "units": units}


# --------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------

def assemble_normalized(address_norm, building_norm):
    """Combine an address normalization (from normalize_address) and a building
    normalization (from a normalize_*_building) into the final structure."""
    prop = dict(address_norm.get("property") or _empty_property())
    # Let the building payload fill in matrikkel numbers the address lacked.
    building_block = building_norm.get("building") or {}
    for src_building in _iter_building_matrikkel(building_norm):
        for key in ("gnr", "bnr"):
            if not prop.get(key) and src_building.get(key):
                prop[key] = src_building[key]

    return {
        "address": dict(address_norm.get("address") or _empty_address()),
        "property": prop,
        "building": building_block or None,
        "buildings": building_norm.get("buildings") or [],
        "floors": building_norm.get("floors") or [],
        "units": building_norm.get("units") or [],
    }


def _iter_building_matrikkel(building_norm):
    for b in building_norm.get("buildings") or []:
        if isinstance(b, dict) and "_matrikkel" in b:
            yield b["_matrikkel"]


# --------------------------------------------------------------------------
# Coercion helpers — every one returns None rather than guessing.
# --------------------------------------------------------------------------

def _dig(obj, *path):
    cur = obj
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _nested_beskrivelse(obj):
    if isinstance(obj, dict):
        return _str_or_none(obj.get("beskrivelse")) or _str_or_none(obj.get("kode"))
    return _str_or_none(obj)


def _str_or_none(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _int_or_none(value):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float_or_none(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bool_or_none(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in ("true", "ja", "yes", "1"):
        return True
    if text in ("false", "nei", "no", "0"):
        return False
    return None


def _titlecase(value):
    text = _str_or_none(value)
    if not text:
        return None
    # Poststed / kommunenavn come back UPPERCASED from Geonorge.
    return text.title() if text.isupper() else text
