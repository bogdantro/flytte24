# apps/leads/property/providers/base.py

from abc import ABC, abstractmethod


class BuildingDataProvider(ABC):
    """A source of building information for a verified address.

    The rest of the app never touches a concrete provider — it goes through
    PropertyLookupService, which holds whichever provider get_provider()
    returned. Swapping Norkart for Ambita / Matrikkelen later means adding one
    file here and one branch in providers/__init__.py; nothing else changes.
    """

    #: short stable id, also used to pick the matching normalizer function
    name = "base"

    @abstractmethod
    def get_building_from_address(self, address):
        """Return the provider's RAW payload (a dict) for the given verified
        address dict (the output of kartverket.verify_address).

        Must raise a apps.leads.property.exceptions.PropertyLookupError subclass
        on any failure — never a bare requests/other exception, and never
        return a partial/fabricated result.
        """
        raise NotImplementedError
