# apps/leads/property/kartverket.py
#
# Stage 1 — address lookup against Kartverket's Geonorge address API
# (https://ws.geonorge.no/adresser/v1/, free, keyless).
#
#   search_addresses(query)      -> raw hits for the autocomplete endpoint
#   verify_address(components)    -> the single canonical address for a set of
#                                    matrikkel/address components (from the
#                                    signed address token) — this is what makes
#                                    the lookup trustworthy: the frontend's
#                                    address object is never believed, we
#                                    re-fetch the authoritative record here.

import logging

from .client import HttpClient
from .exceptions import AddressNotFound
from .normalizer import normalize_address

logger = logging.getLogger(__name__)

BASE_URL = "https://ws.geonorge.no/adresser/v1"
SEARCH_RESULT_LIMIT = 8

_http = HttpClient(log_label="geonorge")


def search_addresses(query, *, limit=SEARCH_RESULT_LIMIT):
    """Free-text address search. Returns the raw `adresser` list from Geonorge
    (possibly empty). Never raises for "no results" — only the HttpClient's
    transport errors propagate, and the caller (address-search view) catches
    those and returns an empty result set."""
    payload = _http.get_json(
        f"{BASE_URL}/sok",
        params={
            "sok": query,
            "fuzzy": "true",
            "treffPerSide": limit,
            "side": 0,
            "asciiKompatibel": "true",
        },
    )
    hits = payload.get("adresser") if isinstance(payload, dict) else None
    return hits or []


def verify_address(components):
    """Re-fetch the one authoritative address for a set of components decoded
    from the signed address token:
        {kommunenummer, adressekode, nummer, bokstav, gnr, bnr}

    Returns the normalized address structure:
        {"address": {...}, "property": {...}, "unit_numbers": [...]}

    Raises AddressNotFound if Geonorge returns nothing matching.
    """
    kommunenummer = str(components.get("kommunenummer") or "").strip()
    adressekode = str(components.get("adressekode") or "").strip()
    nummer = str(components.get("nummer") or "").strip()
    bokstav = (components.get("bokstav") or "").strip()

    if not (kommunenummer and adressekode and nummer):
        raise AddressNotFound(detail=f"incomplete address components: {components!r}")

    params = {
        "kommunenummer": kommunenummer,
        "adressekode": adressekode,
        "nummer": nummer,
        "treffPerSide": 20,
        "side": 0,
        "asciiKompatibel": "true",
    }
    if bokstav:
        params["bokstav"] = bokstav

    payload = _http.get_json(f"{BASE_URL}/sok", params=params)
    hits = (payload.get("adresser") if isinstance(payload, dict) else None) or []

    match = _pick_exact(hits, adressekode, nummer, bokstav)
    if match is None:
        raise AddressNotFound(
            detail=f"no Geonorge match for {kommunenummer}/{adressekode}/{nummer}{bokstav}"
        )

    normalized = normalize_address(match)
    normalized["unit_numbers"] = [
        str(u).strip() for u in (match.get("bruksenhetsnummer") or []) if str(u).strip()
    ]
    return normalized


def _pick_exact(hits, adressekode, nummer, bokstav):
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        if (
            str(hit.get("adressekode") or "").strip() == adressekode
            and str(hit.get("nummer") or "").strip() == nummer
            and (hit.get("bokstav") or "").strip() == bokstav
        ):
            return hit
    # Fall back to the first hit only if there is exactly one — otherwise we
    # can't be sure which address the token meant.
    if len(hits) == 1 and isinstance(hits[0], dict):
        return hits[0]
    return None
