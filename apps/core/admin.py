from django.contrib import admin
from django.utils.html import format_html
from .models import Flytteforesporsel
from apps.store.models import JobDistribution, Bedrift_info


# --- INLINE: JobDistribution ---
class JobDistributionInline(admin.TabularInline):
    model = JobDistribution
    extra = 0
    autocomplete_fields = ["business_1", "business_2", "business_3"]
    fields = ("business_1", "business_2", "business_3", "viewed", "created_at")
    readonly_fields = ("created_at",)
    ordering = ["-created_at"]

    def get_queryset(self, request):
        # Optimize queries to load related businesses efficiently
        return (
            super()
            .get_queryset(request)
            .select_related("business_1", "business_2", "business_3")
        )


# --- ADMIN: Flytteforesporsel ---
@admin.register(Flytteforesporsel)
class FlytteforesporselAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "move_type",
        "from_city",
        "to_city",
        "created_at",
        "assigned_businesses",
    )
    list_filter = ("move_type", "created_at", "from_city", "to_city")
    search_fields = (
        "first_name",
        "last_name",
        "email",
        "phone",
        "from_city",
        "to_city",
    )
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)
    inlines = [JobDistributionInline]
    list_select_related = True
    ordering = ("-created_at",)

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = "Name"

    def assigned_businesses(self, obj):
        # Combine all businesses from all related JobDistributions
        businesses = []
        for dist in obj.distributions.all():
            businesses.extend(dist.businesses())
        names = ", ".join(b.company_name for b in businesses if b)
        return names or "-"
    assigned_businesses.short_description = "Assigned Businesses"
