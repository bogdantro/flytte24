from django.conf import settings


def map_config(request):
    """Exposes the CARTO basemap API key to every template so the map-bearing
    pages (customer wizard, staff + portal lead detail) can hand it to their
    Leaflet setup as window.KOBLY_CARTO_API_KEY. CARTO's raster tiles stopped
    working keyless — without this the map renders an "API KEY REQUIRED"
    watermark over grey tiles."""
    return {"CARTO_API_KEY": settings.CARTO_API_KEY}
