from django.contrib import admin
from .models import Bedrift_info, PublicBusinessInformation, BusinessImage, Review

class BusinessImageInline(admin.TabularInline):
    model = BusinessImage
    extra = 1

class PublicBusinessInformationInline(admin.StackedInline):
    model = PublicBusinessInformation
    can_delete = False
    show_change_link = True
    extra = 0
    inlines = [BusinessImageInline]

class ReviewInline(admin.TabularInline):
    model = Review
    extra = 1
    readonly_fields = ("created_at",)

@admin.register(Bedrift_info)
class BedriftInfoAdmin(admin.ModelAdmin):
    list_display = ("company_name", "email", "city", "active", "created_at")
    search_fields = ("company_name", "email", "city")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
    inlines = [PublicBusinessInformationInline, ReviewInline]
