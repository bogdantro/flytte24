# apps/leads/property/providers/__init__.py
#
# get_provider() — the one place that decides which BuildingDataProvider the
# app runs with, from settings.PROPERTY_PROVIDER.

import logging

from django.conf import settings

from ..exceptions import PropertyProviderMisconfigured
from .base import BuildingDataProvider
from .mock import MockBuildingProvider
from .norkart import NorkartBuildingProvider

logger = logging.getLogger(__name__)

__all__ = ["BuildingDataProvider", "get_provider", "MockBuildingProvider", "NorkartBuildingProvider"]


def get_provider():
    """Instantiate the configured provider.

    * "mock"    -> MockBuildingProvider (logs a warning every call — this
                   settings file has no production branch, so mock must be loud).
    * "norkart" -> NorkartBuildingProvider, but only if URL + key are present;
                   otherwise PropertyProviderMisconfigured (never a silent
                   fallback to mock).
    * anything else -> PropertyProviderMisconfigured.
    """
    choice = (getattr(settings, "PROPERTY_PROVIDER", "mock") or "mock").strip().lower()

    if choice == "mock":
        logger.warning(
            "PROPERTY_PROVIDER=mock — serving fixture building data. Set "
            "PROPERTY_PROVIDER=norkart with credentials for real data."
        )
        return MockBuildingProvider()

    if choice == "norkart":
        if not settings.NORKART_API_URL or not settings.NORKART_API_KEY:
            raise PropertyProviderMisconfigured(
                detail="PROPERTY_PROVIDER=norkart but NORKART_API_URL / NORKART_API_KEY is empty"
            )
        return NorkartBuildingProvider()

    raise PropertyProviderMisconfigured(detail=f"Unknown PROPERTY_PROVIDER={choice!r}")


def normalizer_for(provider_name):
    """The normalize_*_building function matching a provider name."""
    from .. import normalizer

    return {
        "mock": normalizer.normalize_mock_building,
        "norkart": normalizer.normalize_norkart_building,
    }.get(provider_name, normalizer.normalize_norkart_building)
