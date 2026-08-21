from django.contrib import admin

from .models import LeadImage, MoveLead


class LeadImageInline(admin.TabularInline):
    model = LeadImage
    extra = 0


@admin.register(MoveLead)
class MoveLeadAdmin(admin.ModelAdmin):
    list_display = ("reference", "navn", "flytte_type", "boligtype", "fra", "til", "created_at")
    list_filter = ("flytte_type", "boligtype", "fleksibel")
    search_fields = ("reference", "navn", "epost", "telefon", "fra", "til")
    inlines = [LeadImageInline]
