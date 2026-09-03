# apps/leads/property/providers/mock.py
#
# Development / test provider. Returns fixed payloads shaped like Matrikkelen
# "bygning" data so normalize_mock_building() does real mapping work.
#
# NEVER used in production: providers/__init__.py logs a warning every time
# this is selected, and the API view refuses mock data when settings.DEBUG is
# False (see api_views.py).
#
# Fixtures are matched on (street lower-cased, house number). Unknown addresses
# fall back to a plain detached house so a demo always shows something.

import logging

from ..exceptions import BuildingNotFound, ProviderTimeout, ProviderUnavailable

logger = logging.getLogger(__name__)


def _house_payload():
    return {
        "bygninger": [{
            "bygningsnummer": "300123456",
            "bygningstype": {"kode": "111", "beskrivelse": "Enebolig"},
            "bygningsstatus": {"kode": "TB", "beskrivelse": "Tatt i bruk"},
            "byggeaar": 1998,
            "bruksareal": 184,
            "bruttoareal": 205,
            "antallEtasjer": 2,
            "harHeis": False,
            "antallBoenheter": 1,
            "primaerBygning": True,
            "etasjer": [
                {"etasjenummer": "01", "bruksareal": 96},
                {"etasjenummer": "02", "bruksareal": 88},
            ],
            "bruksenheter": [
                {"id": "u-1", "bruksenhetsnummer": "H0101", "etasje": "1", "bruksareal": 184, "bruksenhetstype": "Bolig"},
            ],
            "matrikkelenhet": {"gardsnummer": 12, "bruksnummer": 345, "festenummer": 0, "seksjonsnummer": 0},
        }],
    }


def _apartment_payload():
    units = []
    for floor in range(1, 4):
        for door in range(1, 3):
            code = f"H0{floor}0{door}"
            units.append({
                "id": f"u-{code}",
                "bruksenhetsnummer": code,
                "etasje": str(floor),
                "bruksareal": 62 + door * 6 + floor * 2,
                "bruksenhetstype": "Bolig",
            })
    return {
        "bygninger": [{
            "bygningsnummer": "300222333",
            "bygningstype": {"kode": "142", "beskrivelse": "Store boligbygg"},
            "bygningsstatus": {"kode": "TB", "beskrivelse": "Tatt i bruk"},
            "byggeaar": 2012,
            "bruksareal": 2400,
            "bruttoareal": 2680,
            "antallEtasjer": 3,
            "harHeis": True,
            "antallBoenheter": len(units),
            "primaerBygning": True,
            "etasjer": [
                {"etasjenummer": "01", "bruksareal": 800},
                {"etasjenummer": "02", "bruksareal": 800},
                {"etasjenummer": "03", "bruksareal": 800},
            ],
            "bruksenheter": units,
            "matrikkelenhet": {"gardsnummer": 12, "bruksnummer": 88, "festenummer": 0, "seksjonsnummer": 0},
        }],
    }


def _missing_data_payload():
    """The building is on the register but almost nothing is filled in — the
    normalizer must surface None, and the UI must show "Ikke tilgjengelig",
    never a guessed value."""
    return {
        "bygninger": [{
            "bygningsnummer": "300999888",
            "bygningstype": {"beskrivelse": "Bolig"},
            "bygningsstatus": None,
            "byggeaar": None,
            "bruksareal": None,
            "bruttoareal": None,
            "antallEtasjer": None,
            "harHeis": None,
            "antallBoenheter": 1,
            "primaerBygning": True,
            "etasjer": [],
            "bruksenheter": [
                {"id": "u-x", "bruksenhetsnummer": "H0101", "etasje": None, "bruksareal": None, "bruksenhetstype": "Bolig"},
            ],
            "matrikkelenhet": {"gardsnummer": 12, "bruksnummer": 500},
        }],
    }


def _multiple_buildings_payload():
    return {
        "bygninger": [
            {
                "bygningsnummer": "300777001",
                "bygningstype": {"beskrivelse": "Enebolig"},
                "bygningsstatus": {"beskrivelse": "Tatt i bruk"},
                "byggeaar": 1975, "bruksareal": 142, "antallEtasjer": 2,
                "harHeis": False, "antallBoenheter": 1,
                "bruksenheter": [
                    {"id": "u-h", "bruksenhetsnummer": "H0101", "etasje": "1", "bruksareal": 142, "bruksenhetstype": "Bolig"},
                ],
                "matrikkelenhet": {"gardsnummer": 12, "bruksnummer": 12},
            },
            {
                "bygningsnummer": "300777002",
                "bygningstype": {"beskrivelse": "Garasje"},
                "bygningsstatus": {"beskrivelse": "Tatt i bruk"},
                "byggeaar": 1998, "bruksareal": 36, "antallEtasjer": 1,
                "harHeis": False, "antallBoenheter": 0,
                "bruksenheter": [],
                "matrikkelenhet": {"gardsnummer": 12, "bruksnummer": 12},
            },
        ],
    }


class MockBuildingProvider:
    name = "mock"

    _FIXTURES = {
        ("storgata", "10"): _house_payload,
        ("storgata", "12"): _apartment_payload,
        ("storgata", "14"): _missing_data_payload,
        ("storgata", "18"): _multiple_buildings_payload,
        # Manual-testing triggers for the non-happy paths:
        ("feilveien", "1"): "unavailable",
        ("tregveien", "1"): "timeout",
        ("tomteveien", "1"): "not_found",
    }

    def get_building_from_address(self, address):
        street = (address.get("street") or "").strip().lower()
        number = str(address.get("house_number") or "").strip()
        key = (street, number)

        fixture = self._FIXTURES.get(key)
        if fixture == "unavailable":
            raise ProviderUnavailable(detail="mock: forced unavailable")
        if fixture == "timeout":
            raise ProviderTimeout(detail="mock: forced timeout")
        if fixture == "not_found":
            raise BuildingNotFound(detail="mock: forced building-not-found")

        if callable(fixture):
            return fixture()

        # Unknown address -> a plain house so the flow always demonstrates.
        logger.info("MockBuildingProvider: no fixture for %r, returning default house", key)
        return _house_payload()
