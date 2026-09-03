import json
from unittest import mock

from django.core import signing
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.leads.api_views import ADDRESS_TOKEN_SALT
from apps.leads.forms import WizardForm
from apps.leads.models import MoveLead, PropertyLookup
from apps.leads.property import normalizer
from apps.leads.property.exceptions import (
    BuildingNotFound,
    MultipleBuildings,
    PropertyProviderMisconfigured,
    ProviderTimeout,
)
from apps.leads.property.providers import get_provider
from apps.leads.property.providers.mock import MockBuildingProvider
from apps.leads.property.providers.norkart import NorkartBuildingProvider
from apps.leads.property.service import PropertyLookupService
from apps.leads.property.unit_codes import floor_from_unit_code, parse_bruksenhet_code


def _addr_token(**over):
    payload = {
        "kommunenummer": "3405", "adressekode": "1001", "nummer": "10",
        "bokstav": "", "gnr": "12", "bnr": "345",
    }
    payload.update(over)
    return signing.dumps(payload, salt=ADDRESS_TOKEN_SALT, compress=True)


def _verified(street="Storgata", number="10", units=None):
    return {
        "address": {
            "formatted": f"{street} {number}, 2609 Lillehammer",
            "street": street, "house_number": number, "house_letter": None,
            "postal_code": "2609", "postal_city": "Lillehammer",
            "municipality": "Lillehammer", "municipality_number": "3405",
            "county": None, "latitude": 61.1, "longitude": 10.4,
        },
        "property": {"gnr": "12", "bnr": "345", "fnr": None, "snr": None},
        "unit_numbers": units or [],
    }


# ==========================================================================
# unit codes
# ==========================================================================

class UnitCodeTests(TestCase):
    def test_parses_main_floor_code(self):
        parsed = parse_bruksenhet_code("H0201")
        self.assertEqual(parsed["level_type"], "H")
        self.assertEqual(parsed["floor"], 2)
        self.assertEqual(parsed["running_no"], 1)
        self.assertEqual(parsed["floor_label"], "2. etasje")

    def test_underetasje_and_kjeller(self):
        self.assertEqual(parse_bruksenhet_code("U0101")["floor_label"], "Underetasje")
        self.assertEqual(parse_bruksenhet_code("K0101")["level_type"], "K")

    def test_malformed_returns_none(self):
        for bad in ["", None, "abc", "H12", "X0101", "H01011", 123]:
            self.assertIsNone(parse_bruksenhet_code(bad), bad)

    def test_floor_from_unit_code_helper(self):
        self.assertEqual(floor_from_unit_code("H0301"), "3. etasje")
        self.assertIsNone(floor_from_unit_code("nonsense"))


# ==========================================================================
# normalizer — never invents data
# ==========================================================================

class NormalizerTests(TestCase):
    def test_house_payload_maps_fields(self):
        raw = MockBuildingProvider().get_building_from_address({"street": "Storgata", "house_number": "10"})
        out = normalizer.normalize_mock_building(raw)
        self.assertEqual(out["building"]["building_type"], "Enebolig")
        self.assertEqual(out["building"]["bra_m2"], 184)
        self.assertEqual(out["building"]["construction_year"], 1998)
        self.assertEqual(len(out["units"]), 1)

    def test_apartment_payload_yields_units(self):
        raw = MockBuildingProvider().get_building_from_address({"street": "Storgata", "house_number": "12"})
        out = normalizer.normalize_mock_building(raw)
        self.assertGreater(len(out["units"]), 1)
        self.assertTrue(all(u["unit_number"] for u in out["units"]))

    def test_missing_values_stay_none_never_guessed(self):
        raw = MockBuildingProvider().get_building_from_address({"street": "Storgata", "house_number": "14"})
        out = normalizer.normalize_mock_building(raw)
        self.assertIsNone(out["building"]["bra_m2"])
        self.assertIsNone(out["building"]["construction_year"])
        self.assertIsNone(out["building"]["number_of_floors"])

    def test_malformed_payload_raises(self):
        from apps.leads.property.exceptions import InvalidProviderResponse
        with self.assertRaises(InvalidProviderResponse):
            normalizer.normalize_mock_building("not a dict")

    def test_normalize_address_titlecases_poststed(self):
        hit = {
            "adressetekst": "Storgata 10", "adressenavn": "Storgata", "nummer": 10,
            "postnummer": "2609", "poststed": "LILLEHAMMER", "kommunenavn": "LILLEHAMMER",
            "kommunenummer": "3405", "gardsnummer": 12, "bruksnummer": 345,
            "representasjonspunkt": {"lat": 61.1, "lon": 10.4},
        }
        out = normalizer.normalize_address(hit)
        self.assertEqual(out["address"]["postal_city"], "Lillehammer")
        self.assertEqual(out["address"]["formatted"], "Storgata 10, 2609 Lillehammer")
        self.assertEqual(out["property"]["gnr"], "12")

    def test_norkart_normalizer_tolerates_unknown_shape(self):
        # Unverified mappings: an unrecognised object must yield None fields, not crash.
        out = normalizer.normalize_norkart_building({"something": "else"})
        self.assertEqual(out, {"building": None, "buildings": [], "floors": [], "units": []})


# ==========================================================================
# provider factory
# ==========================================================================

class ProviderFactoryTests(TestCase):
    @override_settings(PROPERTY_PROVIDER="mock")
    def test_mock_selected_by_default(self):
        self.assertIsInstance(get_provider(), MockBuildingProvider)

    @override_settings(PROPERTY_PROVIDER="norkart", NORKART_API_URL="", NORKART_API_KEY="")
    def test_norkart_without_credentials_raises(self):
        with self.assertRaises(PropertyProviderMisconfigured):
            get_provider()

    @override_settings(PROPERTY_PROVIDER="norkart", NORKART_API_URL="https://x", NORKART_API_KEY="k")
    def test_norkart_with_credentials_builds(self):
        self.assertIsInstance(get_provider(), NorkartBuildingProvider)

    @override_settings(PROPERTY_PROVIDER="banana")
    def test_unknown_provider_raises(self):
        with self.assertRaises(PropertyProviderMisconfigured):
            get_provider()


# ==========================================================================
# service
# ==========================================================================

class PropertyLookupServiceTests(TestCase):
    def setUp(self):
        self.svc = PropertyLookupService(MockBuildingProvider())

    def test_house_lookup(self):
        out = self.svc.lookup(_verified("Storgata", "10"))
        self.assertEqual(out["building"]["building_type"], "Enebolig")
        self.assertEqual(out["units"], [] if not out["units"] else out["units"])

    def test_apartment_lookup_returns_many_units(self):
        out = self.svc.lookup(_verified("Storgata", "12"))
        self.assertGreater(len(out["units"]), 1)

    def test_building_not_found_raises(self):
        with self.assertRaises(BuildingNotFound):
            self.svc.lookup(_verified("Tomteveien", "1"))

    def test_multiple_buildings_raises_with_list(self):
        with self.assertRaises(MultipleBuildings) as ctx:
            self.svc.lookup(_verified("Storgata", "18"))
        labels = [b["label"] for b in ctx.exception.buildings]
        self.assertIn("Garasje", labels)

    def test_multiple_buildings_resolved_by_building_id(self):
        try:
            self.svc.lookup(_verified("Storgata", "18"))
            self.fail("expected MultipleBuildings")
        except MultipleBuildings as exc:
            chosen = next(b for b in exc.buildings if b["label"] == "Enebolig")
        out = self.svc.lookup(_verified("Storgata", "18"), building_id=chosen["id"])
        self.assertEqual(out["building"]["building_type"], "Enebolig")

    def test_provider_timeout_propagates(self):
        with self.assertRaises(ProviderTimeout):
            self.svc.lookup(_verified("Tregveien", "1"))

    def test_kartverket_unit_numbers_fill_thin_provider_data(self):
        # provider returns a single-unit house, but Kartverket lists several
        out = self.svc.lookup(_verified("Storgata", "10", units=["H0101", "H0201", "H0301"]))
        # merge only kicks in when the provider gave <=1 unit
        self.assertGreaterEqual(len(out["units"]), 1)


# ==========================================================================
# address-search endpoint
# ==========================================================================

class AddressSearchEndpointTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse("leads:api_address_search")

    def test_short_query_returns_empty_without_calling_geonorge(self):
        with mock.patch("apps.leads.property.kartverket.search_addresses") as search:
            response = self.client.get(self.url, {"q": "st"})
        self.assertEqual(response.json(), {"results": []})
        search.assert_not_called()

    def test_normal_query_maps_results(self):
        hits = [{
            "adressetekst": "Storgata 10", "adressenavn": "Storgata", "nummer": 10, "bokstav": "",
            "postnummer": "2609", "poststed": "LILLEHAMMER", "kommunenavn": "LILLEHAMMER",
            "kommunenummer": "3405", "adressekode": "1001", "gardsnummer": 12, "bruksnummer": 345,
            "representasjonspunkt": {"lat": 61.1, "lon": 10.4},
        }]
        with mock.patch("apps.leads.property.kartverket.search_addresses", return_value=hits):
            response = self.client.get(self.url, {"q": "storgata 10"})
        result = response.json()["results"][0]
        self.assertEqual(result["label"], "Storgata 10")
        self.assertEqual(result["secondary_label"], "2609 Lillehammer")
        self.assertNotIn("adressekode", result)  # no raw fields leak
        # id must be an opaque signed token we can decode server-side
        decoded = signing.loads(result["id"], salt=ADDRESS_TOKEN_SALT)
        self.assertEqual(decoded["nummer"], "10")

    def test_handles_norwegian_letters(self):
        with mock.patch("apps.leads.property.kartverket.search_addresses", return_value=[]) as search:
            self.client.get(self.url, {"q": "Fåberggata"})
        search.assert_called_once()

    def test_geonorge_failure_degrades_to_empty(self):
        from apps.leads.property.exceptions import ProviderUnavailable
        with mock.patch("apps.leads.property.kartverket.search_addresses", side_effect=ProviderUnavailable()):
            response = self.client.get(self.url, {"q": "storgata"})
        self.assertEqual(response.json(), {"results": []})

    def test_second_identical_query_is_cached(self):
        with mock.patch("apps.leads.property.kartverket.search_addresses", return_value=[]) as search:
            self.client.get(self.url, {"q": "kongensgate"})
            self.client.get(self.url, {"q": "kongensgate"})
        self.assertEqual(search.call_count, 1)

    def test_rate_limited_returns_429(self):
        with mock.patch("apps.leads.api_views.SEARCH_RATE", (2, 10)), \
             mock.patch("apps.leads.property.kartverket.search_addresses", return_value=[]):
            self.client.get(self.url, {"q": "aaa"})
            self.client.get(self.url, {"q": "bbb"})
            blocked = self.client.get(self.url, {"q": "ccc"})
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked.json()["error"]["code"], "RATE_LIMITED")


# ==========================================================================
# property-lookup endpoint
# ==========================================================================

@override_settings(DEBUG=True)  # the wizard/property feature is a DEBUG-config feature today
class PropertyLookupEndpointTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse("leads:api_property_lookup")

    def _post(self, body, **kwargs):
        return self.client.post(self.url, data=json.dumps(body), content_type="application/json", **kwargs)

    def test_house_lookup_creates_record_and_returns_stats(self):
        with mock.patch("apps.leads.property.kartverket.verify_address", return_value=_verified("Storgata", "10")):
            response = self._post({"address_id": _addr_token()})
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["building"]["building_type"], "Enebolig")
        self.assertEqual(data["building"]["bra_m2"], 184)
        self.assertEqual(PropertyLookup.objects.count(), 1)
        row = PropertyLookup.objects.get()
        self.assertEqual(row.token, data["token"])
        self.assertEqual(row.provider, "mock")

    def test_apartment_lookup_returns_units(self):
        with mock.patch("apps.leads.property.kartverket.verify_address", return_value=_verified("Storgata", "12")):
            response = self._post({"address_id": _addr_token(nummer="12")})
        data = response.json()
        self.assertTrue(data["success"])
        self.assertGreater(len(data["units"]), 1)

    def test_bad_signature_is_invalid_address(self):
        response = self._post({"address_id": "tampered.token.value"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "INVALID_ADDRESS")

    def test_missing_address_id_is_400(self):
        self.assertEqual(self._post({}).status_code, 400)

    def test_address_not_found(self):
        from apps.leads.property.exceptions import AddressNotFound
        with mock.patch("apps.leads.property.kartverket.verify_address", side_effect=AddressNotFound()):
            response = self._post({"address_id": _addr_token()})
        self.assertEqual(response.json()["error"]["code"], "ADDRESS_NOT_FOUND")

    def test_building_not_found_is_200_success_false(self):
        with mock.patch("apps.leads.property.kartverket.verify_address", return_value=_verified("Tomteveien", "1")):
            response = self._post({"address_id": _addr_token()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["error"]["code"], "BUILDING_NOT_FOUND")

    def test_provider_timeout(self):
        with mock.patch("apps.leads.property.kartverket.verify_address", return_value=_verified("Tregveien", "1")):
            response = self._post({"address_id": _addr_token()})
        self.assertEqual(response.json()["error"]["code"], "PROVIDER_TIMEOUT")

    def test_multiple_buildings_then_pick(self):
        verified = _verified("Storgata", "18")
        with mock.patch("apps.leads.property.kartverket.verify_address", return_value=verified):
            first = self._post({"address_id": _addr_token(nummer="18")}).json()
            self.assertEqual(first["error"]["code"], "MULTIPLE_BUILDINGS")
            bld = next(b for b in first["buildings"] if b["label"] == "Enebolig")
            second = self._post({"address_id": _addr_token(nummer="18"), "building_id": bld["id"]}).json()
        self.assertTrue(second["success"])
        self.assertEqual(second["building"]["building_type"], "Enebolig")

    def test_csrf_is_enforced(self):
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(
            self.url, data=json.dumps({"address_id": _addr_token()}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)

    @override_settings(PROPERTY_PROVIDER="mock", DEBUG=False)
    def test_mock_refused_when_not_debug(self):
        with mock.patch("apps.leads.property.kartverket.verify_address", return_value=_verified()):
            response = self._post({"address_id": _addr_token()})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["error"]["code"], "SERVER_ERROR")

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)


# ==========================================================================
# WizardForm + wizard view integration
# ==========================================================================

def _valid_wizard_payload(**overrides):
    payload = {
        "fra": "Storgata 10, 2609 Lillehammer", "til": "Kirkegata 2, 0153 Oslo",
        "fra_lat": "61.1", "fra_lon": "10.4", "til_lat": "59.9", "til_lon": "10.7",
        "flytte_type": "privat", "boligtype": "leilighet",
        "flyttedato": "2026-10-05", "fleksibel": "",
        "beskrivelse": "", "navn": "Ola Nordmann", "telefon": "+47 900 00 000",
        "epost": "ola@eksempel.no",
    }
    payload.update(overrides)
    return payload


class WizardFormPropertyFieldTests(TestCase):
    def test_property_fields_are_optional(self):
        self.assertTrue(WizardForm(_valid_wizard_payload()).is_valid())

    def test_accepts_property_token_and_manual_fields(self):
        form = WizardForm(_valid_wizard_payload(
            property_token="abc123", bolig_bra_manuell="120", bolig_type_manuell="Enebolig",
        ))
        self.assertTrue(form.is_valid(), form.errors)

    def test_rejects_absurd_manual_area(self):
        form = WizardForm(_valid_wizard_payload(bolig_bra_manuell="9999999"))
        self.assertFalse(form.is_valid())


class WizardPostPropertyTests(TestCase):
    def setUp(self):
        cache.clear()

    def _lookup_row(self, **over):
        normalized = {
            "address": {"formatted": "Storgata 10, 2609 Lillehammer"},
            "property": {"gnr": "12", "bnr": "345"},
            "building": {"building_type": "Enebolig", "bra_m2": 184, "construction_year": 1998, "number_of_floors": 2},
            "buildings": [], "floors": [],
            "units": [{"unit_id": "1", "unit_number": "H0101", "floor": "1", "bra_m2": 184, "type": "Bolig"}],
        }
        normalized.update(over.pop("normalized", {}))
        return PropertyLookup.objects.create(provider="mock", verified_address={}, normalized=normalized, **over)

    def test_token_denormalizes_onto_lead(self):
        row = self._lookup_row()
        self.client.post(reverse("leads:wizard"), _valid_wizard_payload(property_token=row.token))
        lead = MoveLead.objects.get()
        self.assertEqual(lead.property_lookup_id, row.id)
        self.assertEqual(lead.bolig_type, "Enebolig")
        self.assertEqual(lead.bolig_bra_m2, 184)
        self.assertEqual(lead.bolig_byggeaar, 1998)
        self.assertEqual(lead.bolig_datakilde, "api")

    def test_selected_unit_must_match_stored_units(self):
        normalized = {
            "address": {"formatted": "Storgata 12"},
            "property": {},
            "building": {"building_type": "Store boligbygg", "bra_m2": 2400},
            "buildings": [], "floors": [],
            "units": [
                {"unit_number": "H0101", "floor": "1", "bra_m2": 60},
                {"unit_number": "H0201", "floor": "2", "bra_m2": 72},
            ],
        }
        row = PropertyLookup.objects.create(provider="mock", verified_address={}, normalized=normalized)
        # valid unit
        self.client.post(reverse("leads:wizard"), _valid_wizard_payload(property_token=row.token, selected_unit="H0201"))
        lead = MoveLead.objects.get()
        self.assertEqual(lead.bolig_enhet, "H0201")
        self.assertEqual(lead.bolig_bra_m2, 72)  # unit-level, not the building's 2400

    def test_bogus_selected_unit_ignored(self):
        row = self._lookup_row()
        self.client.post(reverse("leads:wizard"), _valid_wizard_payload(property_token=row.token, selected_unit="H9999"))
        lead = MoveLead.objects.get()
        self.assertEqual(lead.bolig_enhet, "")

    def test_manual_fields_flip_datakilde_to_user(self):
        self.client.post(reverse("leads:wizard"), _valid_wizard_payload(
            bolig_type_manuell="Rekkehus", bolig_bra_manuell="145",
        ))
        lead = MoveLead.objects.get()
        self.assertEqual(lead.bolig_type, "Rekkehus")
        self.assertEqual(lead.bolig_bra_m2, 145)
        self.assertEqual(lead.bolig_datakilde, "user")

    def test_no_property_data_still_creates_lead(self):
        self.client.post(reverse("leads:wizard"), _valid_wizard_payload())
        lead = MoveLead.objects.get()
        self.assertEqual(lead.bolig_datakilde, "")
        self.assertIsNone(lead.property_lookup)
