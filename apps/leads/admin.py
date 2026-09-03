from django.contrib import admin

from .models import LeadImage, MoveLead, PropertyLookup


class LeadImageInline(admin.TabularInline):
    model = LeadImage
    extra = 0


@admin.register(MoveLead)
class MoveLeadAdmin(admin.ModelAdmin):
    list_display = ("reference", "navn", "status", "is_duplicate", "flytte_type", "boligtype", "fra", "til", "created_at")
    list_filter = ("status", "is_duplicate", "flytte_type", "boligtype", "fleksibel", "bolig_datakilde")
    search_fields = (
        "reference", "navn", "epost", "telefon", "telefon_normalisert",
        "epost_normalisert", "fra", "til", "bolig_adresse",
    )
    inlines = [LeadImageInline]
    readonly_fields = ("property_lookup", "duplicate_of", "telefon_normalisert", "epost_normalisert")


@admin.register(PropertyLookup)
class PropertyLookupAdmin(admin.ModelAdmin):
    list_display = ("token", "provider", "data_source", "selected_unit_number", "created_at")
    list_filter = ("provider", "data_source")
    search_fields = ("token",)
    readonly_fields = ("token", "provider", "verified_address", "normalized", "created_at")
