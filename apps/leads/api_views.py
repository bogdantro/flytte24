# apps/leads/api_views.py
#
# The JSON endpoints behind the wizard's later steps. All deliberately thin:
# validation + rate limit + cache here, the real work in apps.leads.property /
# apps.leads.duplicates.
#
#   GET  /flytteforesporsel/api/adresse-sok/?q=   -> Kartverket autocomplete proxy
#   POST /flytteforesporsel/api/eiendom/          -> verify address + building lookup
#   POST /flytteforesporsel/api/duplikat-sjekk/   -> "sent one of these recently?" advisory

import hashlib
import json
import logging

from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .duplicates import find_recent_lead
from .models import PropertyLookup
from .property import kartverket
from .property.exceptions import (
    ERROR_CODES,
    InvalidAddress,
    MultipleBuildings,
    PropertyLookupError,
    RateLimited,
)
from .property.service import PropertyLookupService

logger = logging.getLogger(__name__)

ADDRESS_TOKEN_SALT = "leads.property.address"
ADDRESS_TOKEN_MAX_AGE = 60 * 60 * 24  # 24h — a wizard session won't outlast this

QUERY_MIN_LEN = 3
QUERY_MAX_LEN = 150

# Per-IP rate limits (cache-backed, same technique as the dashboard login
# lockout). Generous enough for real typing, tight enough to blunt scripted abuse.
SEARCH_RATE = (40, 10)   # 40 requests / 10 s
LOOKUP_RATE = (12, 10)   # 12 requests / 10 s
DUPLICATE_CHECK_RATE = (20, 10)  # 20 requests / 10 s

SEARCH_CACHE_SECONDS = 120


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "") or "unknown"


def _rate_limited(request, bucket, rate):
    limit, window = rate
    key = f"proprl:{bucket}:{_client_ip(request)}"
    # cache.add is atomic-ish: only sets if missing, so concurrent first hits
    # don't clobber each other's counter.
    cache.add(key, 0, window)
    try:
        current = cache.incr(key)
    except ValueError:
        # Key expired between add and incr — treat as first request in a new window.
        cache.add(key, 1, window)
        current = 1
    return current > limit


def _error(code, message, *, status=200, extra=None):
    body = {"success": False, "error": {"code": code, "message": message}}
    if extra:
        body.update(extra)
    return JsonResponse(body, status=status)


def _encode_address_id(hit):
    """Opaque signed token for one Geonorge hit — the only address identifier
    the frontend ever holds. Carries just enough to re-fetch the canonical
    record server-side."""
    payload = {
        "kommunenummer": str(hit.get("kommunenummer") or ""),
        "adressekode": str(hit.get("adressekode") or ""),
        "nummer": str(hit.get("nummer") or ""),
        "bokstav": hit.get("bokstav") or "",
        "gnr": str(hit.get("gardsnummer") or ""),
        "bnr": str(hit.get("bruksnummer") or ""),
    }
    return signing.dumps(payload, salt=ADDRESS_TOKEN_SALT, compress=True)


def _slim_hit(hit):
    poststed = (hit.get("poststed") or "").title()
    postnummer = hit.get("postnummer") or ""
    return {
        "id": _encode_address_id(hit),
        "label": hit.get("adressetekst") or "",
        "secondary_label": f"{postnummer} {poststed}".strip(),
        "street": hit.get("adressenavn") or "",
        "house_number": str(hit.get("nummer") or ""),
        "house_letter": hit.get("bokstav") or "",
        "postal_code": postnummer,
        "postal_city": poststed,
        "municipality": (hit.get("kommunenavn") or "").title(),
        "municipality_number": str(hit.get("kommunenummer") or ""),
        "latitude": (hit.get("representasjonspunkt") or {}).get("lat"),
        "longitude": (hit.get("representasjonspunkt") or {}).get("lon"),
    }


# --------------------------------------------------------------------------
# GET /flytteforesporsel/api/adresse-sok/?q=
# --------------------------------------------------------------------------

@require_GET
def address_search(request):
    query = (request.GET.get("q") or "").strip()

    if len(query) > QUERY_MAX_LEN:
        return JsonResponse({"results": []}, status=400)
    if len(query) < QUERY_MIN_LEN:
        return JsonResponse({"results": []})

    if _rate_limited(request, "search", SEARCH_RATE):
        return _error(ERROR_CODES.RATE_LIMITED, RateLimited.message, status=429)

    cache_key = "propsearch:" + hashlib.sha1(query.lower().encode("utf-8")).hexdigest()
    cached = cache.get(cache_key)
    if cached is not None:
        return JsonResponse({"results": cached})

    try:
        hits = kartverket.search_addresses(query)
    except PropertyLookupError as exc:
        # Geonorge slow / down / non-JSON — degrade to "no results", never 500.
        logger.warning("address_search: Geonorge failed (%s)", exc.detail or exc)
        return JsonResponse({"results": []})
    except Exception:  # pragma: no cover - defensive
        logger.exception("address_search: unexpected failure")
        return JsonResponse({"results": []})

    results = [_slim_hit(h) for h in hits if isinstance(h, dict)]
    cache.set(cache_key, results, SEARCH_CACHE_SECONDS)
    return JsonResponse({"results": results})


# --------------------------------------------------------------------------
# POST /flytteforesporsel/api/eiendom/
# --------------------------------------------------------------------------

@require_POST
def property_lookup(request):
    # CSRF is enforced by the middleware (this view is not exempt) — the wizard
    # page always carries the token.
    if _rate_limited(request, "lookup", LOOKUP_RATE):
        return _error(ERROR_CODES.RATE_LIMITED, RateLimited.message, status=429)

    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return _error(ERROR_CODES.INVALID_ADDRESS, InvalidAddress.message, status=400)

    address_id = body.get("address_id")
    if not isinstance(address_id, str) or not address_id:
        return _error(ERROR_CODES.INVALID_ADDRESS, InvalidAddress.message, status=400)

    building_id = body.get("building_id")
    building_id = str(building_id)[:64] if building_id not in (None, "") else None

    try:
        components = signing.loads(
            address_id, salt=ADDRESS_TOKEN_SALT, max_age=ADDRESS_TOKEN_MAX_AGE
        )
    except signing.BadSignature:
        return _error(ERROR_CODES.INVALID_ADDRESS, InvalidAddress.message, status=400)

    # Never run fixture data in production.
    if (getattr(settings, "PROPERTY_PROVIDER", "mock") == "mock") and not settings.DEBUG:
        logger.error("property_lookup: PROPERTY_PROVIDER=mock with DEBUG=False — refusing")
        return _error(ERROR_CODES.SERVER_ERROR, "Boliginformasjon er ikke konfigurert.", status=500)

    try:
        verified = kartverket.verify_address(components)
    except PropertyLookupError as exc:
        return _log_and_error(exc, context="verify")
    except Exception:  # pragma: no cover - defensive
        logger.exception("property_lookup: unexpected verify failure")
        return _error(ERROR_CODES.SERVER_ERROR, PropertyLookupError.message, status=500)

    provider_name = getattr(settings, "PROPERTY_PROVIDER", "mock")
    cache_key = _building_cache_key(verified, building_id)
    normalized = cache.get(cache_key) if cache_key else None

    if normalized is None:
        try:
            normalized = PropertyLookupService().lookup(verified, building_id=building_id)
        except MultipleBuildings as exc:
            # Not an error to the user — a selection step. 200, buildings list.
            return _error(
                exc.code, exc.message,
                extra={"address": verified["address"], "buildings": exc.buildings},
            )
        except PropertyLookupError as exc:
            return _log_and_error(exc, context="lookup", address=verified["address"])
        except Exception:  # pragma: no cover - defensive
            logger.exception("property_lookup: unexpected lookup failure")
            return _error(ERROR_CODES.SERVER_ERROR, PropertyLookupError.message, status=500)
        if cache_key and provider_name != "mock":
            cache.set(cache_key, normalized, getattr(settings, "PROPERTY_LOOKUP_CACHE_SECONDS", 21600))

    lookup_row = PropertyLookup.objects.create(
        provider=provider_name,
        verified_address=verified,
        normalized=normalized,
    )

    return JsonResponse({
        "success": True,
        "token": lookup_row.token,
        "address": normalized["address"],
        "property": normalized["property"],
        "building": normalized["building"],
        "buildings": normalized["buildings"],
        "floors": normalized["floors"],
        "units": normalized["units"],
        "source_note": (
            "Eiendomsinformasjon hentet fra offentlige registre. "
            "Opplysningene kan avvike fra dagens faktiske forhold."
        ),
    })


def _building_cache_key(verified, building_id=None):
    addr = verified.get("address") or {}
    prop = verified.get("property") or {}
    kommune = addr.get("municipality_number")
    gnr = prop.get("gnr")
    bnr = prop.get("bnr")
    if kommune and gnr and bnr:
        suffix = ""
        if building_id:
            suffix = "-b" + hashlib.sha1(str(building_id).encode("utf-8")).hexdigest()[:12]
        return f"propbuilding:{kommune}-{gnr}-{bnr}{suffix}"
    return None


def _log_and_error(exc, *, context, address=None):
    logger.warning(
        "property_lookup: %s failed code=%s detail=%s",
        context, exc.code, getattr(exc, "detail", None),
    )
    extra = {"address": address} if address else None
    return _error(exc.code, exc.message, status=exc.http_status, extra=extra)


# --------------------------------------------------------------------------
# POST /flytteforesporsel/api/duplikat-sjekk/
# --------------------------------------------------------------------------

@require_POST
def duplicate_check(request):
    """Live "have you sent one of these recently?" check for the wizard's
    contact step. Advisory only — apps.leads.views.wizard re-checks on submit
    and is the real gate. Returns just enough for the warning copy, nothing the
    caller didn't already type."""
    if _rate_limited(request, "dupcheck", DUPLICATE_CHECK_RATE):
        return JsonResponse({"duplicate": False}, status=429)

    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"duplicate": False}, status=400)

    telefon = str(body.get("telefon") or "")[:50]
    epost = str(body.get("epost") or "")[:254]

    recent = find_recent_lead(telefon, epost)
    if recent is None:
        return JsonResponse({"duplicate": False})

    return JsonResponse({
        "duplicate": True,
        "reference": recent.reference,
        "since": timezone.localtime(recent.created_at).strftime("%d.%m.%Y"),
    })
