from django.contrib import admin
from .models import *
from django import forms
from .forms import *
from ckeditor.widgets import CKEditorWidget

# Register your models here.


class BudInline(admin.TabularInline):
    model = Bud
    extra = 1

class CarPostAdminForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorWidget())
    inlines = [BudInline]
    class Meta:
        model = Car
        fields = '__all__'

class CarPostAdmin(admin.ModelAdmin):
    form = CarPostAdminForm

admin.site.register(Car,CarPostAdmin)
admin.site.register(Bud)
admin.site.register(TestDrive)

    # list_display = ['name', 'business_name', 'slug', 'category', 'address', 'is_home_page',]
    # search_fields = ('name', 'business_name', 'slug', 'is_home_page', 'description')
    # list_filter = ('is_home_page',)
    # list_editable = ('is_home_page', 'business_name', 'slug', 'address', 'category',)
    # prepopulated_fields = {"slug": ("name","business_name",)}
