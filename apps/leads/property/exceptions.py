# apps/leads/property/exceptions.py
#
# One exception per failure mode the property-lookup flow can hit. Every one
# carries a stable `code` (surfaced to the frontend as error.code — see the
# design doc's "internal codes" list) and a Norwegian `message` safe to show a
# visitor. Views translate an exception into a JSON error body; they never leak
# the underlying technical detail (that goes to the log only).


class ERROR_CODES:
    """String constants for every error.code the API can return. Grouped here
    so the frontend contract and the exceptions below can't drift apart."""

    INVALID_ADDRESS = "INVALID_ADDRESS"
    ADDRESS_NOT_FOUND = "ADDRESS_NOT_FOUND"
    BUILDING_NOT_FOUND = "BUILDING_NOT_FOUND"
    MULTIPLE_BUILDINGS = "MULTIPLE_BUILDINGS"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    RATE_LIMITED = "RATE_LIMITED"
    INVALID_PROVIDER_RESPONSE = "INVALID_PROVIDER_RESPONSE"
    SERVER_ERROR = "SERVER_ERROR"


class PropertyLookupError(Exception):
    """Base for every expected property-lookup failure. `code` is one of
    ERROR_CODES; `message` is visitor-safe Norwegian."""

    code = ERROR_CODES.SERVER_ERROR
    message = "Noe gikk galt. Prøv igjen om litt."
    # HTTP status the API view should respond with. Semantic failures default
    # to 200 (success:false) so the frontend's fallback flow isn't treated as
    # a transport error; only genuinely bad requests / rate limits / bugs
    # override this.
    http_status = 200

    def __init__(self, message=None, *, detail=None):
        # `detail` is technical context for the server log only — never sent to
        # the client.
        self.detail = detail
        if message is not None:
            self.message = message
        super().__init__(self.message)


class InvalidAddress(PropertyLookupError):
    code = ERROR_CODES.INVALID_ADDRESS
    message = "Adressen er ikke gyldig. Søk på nytt og velg en adresse fra listen."
    http_status = 400


class AddressNotFound(PropertyLookupError):
    code = ERROR_CODES.ADDRESS_NOT_FOUND
    message = "Vi fant ikke adressen. Kontroller gatenavn og husnummer og prøv igjen."


class BuildingNotFound(PropertyLookupError):
    code = ERROR_CODES.BUILDING_NOT_FOUND
    message = (
        "Adressen ble funnet, men vi kunne ikke hente fullstendig informasjon "
        "om boligen."
    )


class MultipleBuildings(PropertyLookupError):
    """Raised only when several buildings are on the property and the provider
    gives us nothing to disambiguate them. The view still returns 200 with the
    `buildings` list so the frontend can offer a picker."""

    code = ERROR_CODES.MULTIPLE_BUILDINGS
    message = "Vi fant flere bygg på eiendommen. Velg riktig bygg."

    def __init__(self, message=None, *, buildings=None, detail=None):
        self.buildings = buildings or []
        super().__init__(message, detail=detail)


class ProviderUnavailable(PropertyLookupError):
    code = ERROR_CODES.PROVIDER_UNAVAILABLE
    message = "Tjenesten for boliginformasjon er utilgjengelig akkurat nå. Prøv igjen senere."


class ProviderTimeout(PropertyLookupError):
    code = ERROR_CODES.PROVIDER_TIMEOUT
    message = "Det tok for lang tid å hente boliginformasjon. Prøv igjen."


class RateLimited(PropertyLookupError):
    code = ERROR_CODES.RATE_LIMITED
    message = "For mange forespørsler. Vent litt og prøv igjen."
    http_status = 429


class InvalidProviderResponse(PropertyLookupError):
    code = ERROR_CODES.INVALID_PROVIDER_RESPONSE
    message = "Vi fikk et uventet svar fra registeret. Prøv igjen senere."


class PropertyProviderMisconfigured(PropertyLookupError):
    """The deployment selected a provider it can't actually use (e.g. norkart
    without credentials). Distinct from ProviderUnavailable: this is our
    configuration bug, not the provider being down. Never silently falls back
    to mock."""

    code = ERROR_CODES.SERVER_ERROR
    message = "Boliginformasjon er ikke konfigurert. Kontakt oss om problemet vedvarer."
    http_status = 500
