from django.contrib import admin
from .models import Flytteforesporsel

@admin.register(Flytteforesporsel)
class FlytteforesporselAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "move_type", "from_city", "to_city", "email", "created_at")
    list_filter = ("move_type", "from_city", "to_city")
    search_fields = ("first_name", "last_name", "email", "phone", "from_city", "to_city")
