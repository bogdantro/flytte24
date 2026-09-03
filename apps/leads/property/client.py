# apps/leads/property/client.py
#
# One small HTTP client shared by every outbound call this feature makes
# (Kartverket today, Norkart once wired). It exists so timeout handling, JSON
# parsing, and HTTP-status -> exception mapping are written once, not copied
# into each provider.
#
# Design rules (feature brief "HTTP CLIENT"):
#   * reasonable timeouts, always set
#   * every failure mode handled: connect/read timeout, malformed JSON,
#     400/401/403/404/429, 5xx, connection refused
#   * an external failure NEVER propagates as a raw requests exception — it is
#     always translated into a PropertyLookupError subclass
#   * technical detail goes to `detail=` (logged server-side), never to the
#     visitor-facing message

import logging

import requests

from .exceptions import (
    InvalidProviderResponse,
    ProviderTimeout,
    ProviderUnavailable,
    RateLimited,
)

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 8


class HttpClient:
    """Thin requests.Session wrapper. One instance per provider is fine; it is
    not thread-affine beyond what requests.Session already guarantees."""

    def __init__(self, *, timeout=DEFAULT_TIMEOUT_SECONDS, session=None, log_label="http"):
        self.timeout = timeout
        self.log_label = log_label
        self._session = session or requests.Session()

    def get_json(self, url, *, params=None, headers=None):
        return self._request_json("GET", url, params=params, headers=headers)

    def post_json(self, url, *, json=None, params=None, headers=None):
        return self._request_json("POST", url, json=json, params=params, headers=headers)

    def _request_json(self, method, url, *, params=None, json=None, headers=None):
        try:
            response = self._session.request(
                method, url, params=params, json=json, headers=headers, timeout=self.timeout
            )
        except requests.Timeout as exc:
            logger.warning("%s timeout: %s %s", self.log_label, method, url)
            raise ProviderTimeout(detail=f"{method} {url}: {exc}") from exc
        except requests.RequestException as exc:
            # DNS failure, connection refused, TLS error, too many redirects…
            logger.warning("%s connection error: %s %s (%s)", self.log_label, method, url, exc)
            raise ProviderUnavailable(detail=f"{method} {url}: {exc}") from exc

        self._raise_for_status(response, method, url)

        try:
            return response.json()
        except ValueError as exc:
            logger.warning(
                "%s returned non-JSON body: %s %s (status %s)",
                self.log_label, method, url, response.status_code,
            )
            raise InvalidProviderResponse(detail=f"{method} {url}: non-JSON body") from exc

    def _raise_for_status(self, response, method, url):
        status = response.status_code
        if status < 400:
            return
        # Never log the response body wholesale — it can contain request echoes.
        detail = f"{method} {url}: HTTP {status}"
        if status == 429:
            logger.warning("%s rate limited: %s", self.log_label, detail)
            raise RateLimited(detail=detail)
        if status in (401, 403):
            # Our credentials / permissions problem — surfaced to the visitor as
            # a generic "unavailable", logged distinctly so ops can tell.
            logger.error("%s auth failure: %s", self.log_label, detail)
            raise ProviderUnavailable(detail=detail)
        if status == 404:
            logger.info("%s not found: %s", self.log_label, detail)
            raise ProviderUnavailable(detail=detail)
        if status == 400:
            logger.warning("%s bad request: %s", self.log_label, detail)
            raise InvalidProviderResponse(detail=detail)
        # 5xx and anything else in the 4xx range
        logger.error("%s upstream error: %s", self.log_label, detail)
        raise ProviderUnavailable(detail=detail)
