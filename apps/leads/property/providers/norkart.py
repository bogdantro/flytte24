# apps/leads/property/providers/norkart.py
#
# Norkart Bygningsdata / Bygning API provider.
#
# ============================ NOT YET FUNCTIONAL ============================
# Norkart access requires credentials and private API documentation that are
# not in this repository. This file implements the *shape* — configuration,
# credential handling, the request site, and error handling — with the actual
# endpoint path, authentication scheme, request parameters, and response
# mapping all marked TODO(norkart).
#
# To finish it you need, from Norkart:
#   * the base URL of the Bygning API           -> settings.NORKART_API_URL
#   * the API key / client id                   -> settings.NORKART_API_KEY
#   * the API secret, if their auth uses one    -> settings.NORKART_API_SECRET
#   * the auth mechanism (header? OAuth token exchange? query param?)
#   * a sample "buildings for an address / matrikkelenhet" response
#
# Then: fill in `_auth_headers`, `_build_request`, and
# normalizer.normalize_norkart_building. Do NOT invent any of these.
#
# providers/__init__.py will not construct this provider unless URL + KEY are
# set, and api_views.py refuses to serve if DEBUG is False and the provider is
# still "mock" — so there is no path where a half-configured Norkart silently
# returns nothing in production.
# ==========================================================================

import logging

from django.conf import settings

from ..client import HttpClient
from ..exceptions import BuildingNotFound, ProviderUnavailable

logger = logging.getLogger("apps.leads.property.norkart")


class NorkartBuildingProvider:
    name = "norkart"

    def __init__(self, *, http_client=None):
        self.api_url = (settings.NORKART_API_URL or "").rstrip("/")
        self.api_key = settings.NORKART_API_KEY
        self.api_secret = settings.NORKART_API_SECRET
        self.http = http_client or HttpClient(
            timeout=getattr(settings, "NORKART_API_TIMEOUT", 8),
            log_label="norkart",
        )

    # -- auth ---------------------------------------------------------------

    def _auth_headers(self):
        """TODO(norkart): replace with the real scheme from Norkart's docs.

        Common possibilities (pick per documentation, don't guess in prod):
          * {"X-WAAPI-TOKEN": self.api_key}
          * {"Authorization": f"Bearer {self._oauth_token()}"}
          * {"apikey": self.api_key}
        """
        return {
            # placeholder — DO NOT rely on this header name
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

    # -- request ----------------------------------------------------------

    def _build_request(self, address):
        """TODO(norkart): real endpoint path + query params.

        We hold a fully verified address (kommunenummer, gnr, bnr, adressekode,
        house number/letter, lat/lon). Norkart most likely wants the
        matrikkelenhet (kommune-gnr-bnr) or a point; confirm which.
        """
        kommune = address.get("municipality_number")
        gnr = (address.get("property") or {}).get("gnr")
        bnr = (address.get("property") or {}).get("bnr")
        url = f"{self.api_url}/TODO/bygninger"  # TODO(norkart): real path
        params = {
            # TODO(norkart): confirm parameter names
            "kommunenummer": kommune,
            "gardsnummer": gnr,
            "bruksnummer": bnr,
        }
        return url, params

    # -- public -----------------------------------------------------------

    def get_building_from_address(self, address):
        if not self.api_url or not self.api_key:
            # Should be caught earlier by get_provider(); belt and braces.
            raise ProviderUnavailable(detail="norkart: URL or key missing")

        url, params = self._build_request(address)
        payload = self.http.get_json(url, params=params, headers=self._auth_headers())

        # TODO(norkart): confirm how "address exists but no building on file"
        # comes back (empty list? 404? a flag?) and raise BuildingNotFound for it.
        if isinstance(payload, dict) and payload.get("bygninger") == []:
            raise BuildingNotFound(detail="norkart: empty bygninger list")

        return payload
