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

    list_display = ['id', 'name', 'car_brand', 'car_model', 'price']
    search_fields = ('id', 'name', 'car_brand', 'car_model', 'km')


    fieldsets = (
      ('Hoved informasjon', {
          'fields': ('user', 'name', 'slug', 'price','fritak_for_reg_pris','reg_pris','expiry_date','description')
      }),
      ('Kvalitet', {
          'fields': (
              'chasis',
              'reg_nr',
              'year',
              'car_brand',
              'car_model',
              'km',
              'first_registered',
              'amount_of_owners',
              'last_EU_accepted',
              'next_EU_test_deadline',
              'garanti_type',
          )
      }),
      ('Bilder', {
          'fields': (
              'image1',
              'image2',
              'image3',
              'image4',
              'image5',
              'image6',
              'image7',
              'image8',
              'image9',
              'image10',
              'image11',
              'image12',
              'image13',
              'image14',
              'image15',
              'image16',
              'image17',
              'image18',
              'image19',
              'image20',
              'image21',
              'image22',
              'image23',
              'image24',
              'image25',
              'image26',
              'image27',
              'image28',
              'image29',
              'image30',
          )
      }),
      ('Kontakt informasjon', {
          'fields': (
              'adress',
              'post_nr',
              'country',
              'mobile_nr',
              'owner_mobile_nr',
              'email',
              'contact_person',
          )
      }),
      ('Garanti', {
          'fields': (
              'garanti_mnd',
              'garanti_km',
              'fulgt_bilens_vedlikeholdsprogram',
              'bytterett',
          )
      }),
      ('Sikkerhet', {
          'fields': (
              'ABS_bremser',
              'airbag_foran',
              'alarm',
              'gjenfinningssystem',
              'isofix',
              'sentrallås',
              'sideairbager',
              'startsperre',
          )
      }),
      ('Media', {
          'fields': (
              'AUX_inngang',
              'bluetooth',
              'CD_spiller',
              'handsfree_opplegg',
              'head_up_display',
              'kassetspiller',
              'multifunksjonsratt',
              'navigasjonssystem',
              'original_telefon',
              'radio_DAB',
              'radio_FM',
              'TV_skjerm_i_baksetet',
          )
      }),
      ('Motor', {
          'fields': (
              'antiskrens',
              'antispin',
              'diesel_partikkelfilter',
              'diffsperre',
              'kjørecomputer',
              'servostyring',
          )
      }),
      ('Interior', {
          'fields': (
              'elvinduer',
              'mørke_ruter_bak',
              'seter_i_delskinn',
              'seter_i_helskinn',
              'soltak_eller_glasstak',
              'sportsseter',
          )
      }),
      ('Komfort', {
          'fields': (
              'air_Condition',
              'bagasjeromstrekk',
              'cruisekontroll',
              'cruisekontroll_Adaptiv',
              'elektrisk_sete_med_memory',
              'elektrisk_sete_uten_memory',
              'klimaanlegg',
              'kupevarmer',
              'luftfjæring',
              'midtarmlene',
              'motorvarmer',
              'nivåregulering',
              'nøkkelløs_start',
              'oppvarmende_seter',
          )
      }),
      ('Eksteriør', {
          'fields': (
              'elektriske_speil',
              'helårsdekk',
              'hengerfeste_eller_svingbart',
              'LED_lys',
              'laserlys',
              'lasterholdere_eller_skistativ',
              'lettmet_felg_sommer',
              'lettmet_felg_vinter',
              'metalic_lakk',
              'sommerhjul',
              'vinterhjul',
              'takrails',
              'xenolys',
          )
      }),
      ('Fører', {
          'fields': (
              'fjernlysassitent',
              'lyssensor',
              'parkeringsensor_bak',
              'parkeringsensor_foran',
              'regnesensor',
              'ryggekamera',
          )
      }),
      ('Ekstra', {
          'fields': (
              'maks_tilhengervekt_i_kg',
              'hovedfarge',
              'fargebeskrivelse',
              'interiorfarge',
          )
      }),
      ('Karosseritype', {
          'fields': (
              'karosseritype',
              'avgiftsklasse',
              'antall_seter',
              'antall_dører',
              'bagasjeromsvolum_i_liter',
              'egenvekt_i_kg',
              'rekkevidde',
              'girkasse',
              'girkassebetegnelse',
              'hjuldrift',
              'hjuldriftbetegnelse',
              'modellspesifikasjon',
              'bilen_står_i',
              'drivstoff',
              'effekt_i_hk',
              'batterikapasitet_i_kWh',
          )
      }),
    )



admin.site.register(Car,CarPostAdmin)
admin.site.register(Bud)
admin.site.register(TestDrive)
admin.site.register(Buy)

    


