from django.urls import path

from . import views

app_name = "leads"

urlpatterns = [
    path("", views.wizard, name="wizard"),
    path("takk/", views.wizard_thank_you, name="wizard_thank_you"),
    path("start-fra-postnummer/<str:postal_code>/", views.start_from_postal_code, name="start_from_postal_code"),
]
