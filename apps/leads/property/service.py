# apps/leads/property/service.py
#
# PropertyLookupService — the seam the wizard view calls. Takes a verified
# Kartverket address, asks the configured building provider about it, and
# returns ONE normalized structure. The view stays thin and never imports a
# provider or the normalizer directly.

import logging

from .exceptions import BuildingNotFound, MultipleBuildings
from .normalizer import assemble_normalized
from .providers import get_provider, normalizer_for
from .unit_codes import floor_from_unit_code

logger = logging.getLogger(__name__)


class PropertyLookupService:
    def __init__(self, provider=None):
        self.provider = provider or get_provider()

    def lookup(self, verified_address, *, building_id=None):
        """`verified_address` is kartverket.verify_address()'s output
        ({"address", "property", "unit_numbers"}).

        `building_id` — when several buildings are on the property and none is
        tied to the address, the frontend picks one and re-calls with its id.

        Returns the normalized dict:
            {address, property, building, buildings, floors, units}

        Raises a PropertyLookupError subclass on failure (BuildingNotFound,
        MultipleBuildings, ProviderUnavailable, ...). Never fabricates.
        """
        raw = self.provider.get_building_from_address(_provider_address_view(verified_address))
        normalize_building = normalizer_for(self.provider.name)
        building_norm = normalize_building(raw)

        normalized = assemble_normalized(verified_address, building_norm)
        normalized = _merge_kartverket_units(normalized, verified_address.get("unit_numbers") or [])

        has_building = normalized.get("building") is not None
        has_buildings = bool(normalized.get("buildings"))
        has_units = bool(normalized.get("units"))

        if not has_building and not has_buildings and not has_units:
            raise BuildingNotFound(detail="provider returned no building for the address")

        if not has_building and has_buildings:
            chosen = None
            if building_id:
                chosen = next(
                    (b for b in normalized["buildings"] if str(b.get("id")) == str(building_id)),
                    None,
                )
            if chosen is None:
                # Several buildings, none resolvable — hand the frontend a picker
                # (id/label/type only; it re-calls with the chosen id).
                raise MultipleBuildings(buildings=[
                    {"id": b.get("id"), "label": b.get("label"), "type": b.get("type")}
                    for b in normalized["buildings"]
                ])
            normalized["building"] = chosen.get("building")
            normalized["floors"] = chosen.get("floors") or []
            normalized["units"] = chosen.get("units") or []

        # The full per-building payloads were only needed for the picker step —
        # don't persist / return them once a single building is resolved.
        normalized["buildings"] = [
            {"id": b.get("id"), "label": b.get("label"), "type": b.get("type")}
            for b in normalized.get("buildings") or []
        ]
        return normalized


def _provider_address_view(verified_address):
    """A flat dict a provider can read without knowing our nesting — street,
    house number, kommunenummer, gnr/bnr, coordinates."""
    address = verified_address.get("address") or {}
    prop = verified_address.get("property") or {}
    return {
        "street": address.get("street"),
        "house_number": address.get("house_number"),
        "house_letter": address.get("house_letter"),
        "postal_code": address.get("postal_code"),
        "municipality_number": address.get("municipality_number"),
        "latitude": address.get("latitude"),
        "longitude": address.get("longitude"),
        "property": {"gnr": prop.get("gnr"), "bnr": prop.get("bnr")},
    }


def _merge_kartverket_units(normalized, kartverket_unit_numbers):
    """Kartverket lists the bruksenhetsnummer at an address even when the
    building provider gives thin unit data. If the provider returned no units
    but Kartverket names several, surface them (floor derived only from the
    documented unit-code parser, area left null — never guessed)."""
    if normalized.get("units"):
        return normalized
    real_codes = [c for c in kartverket_unit_numbers if c and c.upper() != "H0101"]
    if len(real_codes) <= 1:
        return normalized
    normalized["units"] = [
        {
            "unit_id": code,
            "unit_number": code,
            "floor": floor_from_unit_code(code),
            "bra_m2": None,
            "type": None,
        }
        for code in sorted(real_codes)
    ]
    return normalized
