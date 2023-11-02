from django.contrib import admin
from .models import *
from django import forms
from .forms import *
from ckeditor.widgets import CKEditorWidget  # Import CKEditorWidget

# Register your models here.


class TestDriveForm(forms.ModelForm):
    class Meta:
        model = TestDrive
        fields = ['name', 'date1_Y_m_d', 'time1', 'date2_Y_m_d', 'time2']


class BidInline(admin.TabularInline):
    model = Bud
    extra = 0

class BuyInline(admin.TabularInline):
    model = Buy
    extra = 0


class TestDriveInline(admin.TabularInline):
    model = TestDrive
    extra = 0
    form = TestDriveForm





class CarPostAdmin(admin.ModelAdmin):
    inlines = [BidInline, BuyInline, TestDriveInline]
    list_display = ['id', 'name', 'car_spesifikasjoner', 'car_brand', 'price']
    search_fields = ('id', 'name', 'car_brand', 'car_spesifikasjoner', 'km')

    formfield_overrides = {
        models.TextField: {'widget': CKEditorWidget()},
    }

    fieldsets = (
      ('Hoved informasjon', {
          'fields': ('sold', 'user', 'name', 'car_spesifikasjoner', 'car_brand', 'slug', 'price','fritak_for_reg_pris','reg_pris','expiry_date','description')
      }),
      ('Ekstra informasjon', {
          'fields': ('service', 'garanti')
      }),
      ('Kvalitet', {
          'fields': (
              'reg_nr',
              'year',
              'km',
              'first_registered',
              'amount_of_owners',
              'last_EU_accepted',
              'next_EU_test_deadline',
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
              'image31',
              'image32',
              'image33',
              'image34',
              'image35',
              'image36',
              'image37',
              'image38',
              'image39',
              'image40',
              'image41',
              'image42',
              'image43',
              'image44',
              'image45',
              'image46',
              'image47',
              'image48',
              'image49',
              'image50',
              'image51',
              'image52',
              'image53',
              'image54',
              'image55',
              'image56',
              'image57',
              'image58',
              'image59',
              'image60',
              'image61',
              'image62',
              'image63',
              'image64',
              'image65',
              'image66',
              'image67',
              'image68',
              'image69',
              'image70',
              'image71',
              'image72',
              'image73',
              'image74',
              'image75',
              'image76',
              'image77',
              'image78',
              'image79',
              'image80',
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
admin.site.register(Egenerkeling)

    


