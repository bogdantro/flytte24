from django.urls import path

from . import api_views, views

app_name = "leads"

urlpatterns = [
    path("", views.wizard, name="wizard"),
    path("takk/", views.wizard_thank_you, name="wizard_thank_you"),
    path("start-fra-postnummer/<str:postal_code>/", views.start_from_postal_code, name="start_from_postal_code"),

    # Step 2 "Din nåværende bolig" — address verification + building lookup.
    path("api/adresse-sok/", api_views.address_search, name="api_address_search"),
    path("api/eiendom/", api_views.property_lookup, name="api_property_lookup"),
    # Step 6 — advisory repeat-submission check.
    path("api/duplikat-sjekk/", api_views.duplicate_check, name="api_duplicate_check"),
]
