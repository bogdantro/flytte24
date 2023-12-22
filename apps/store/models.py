from django.utils import timezone
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe




class Car(models.Model):

    PLACE = [
        ("Norge", "Norge"),
        ("Utlandet", "Utlandet"),
    ]

    CHASIS = [
        ("Kombi-5 dørs", "Kombi-5 dørs"),
        ("SUV/Offroad", "SUV/Offroad"),
        ("Sedan", "Sedan"),
        ("Stasjonsvogn", "Stasjonsvogn"),
        ("Coupe", "Coupe"),
        ("Pickup", "Pickup"),
    ]

    SELLER = [
        ("Cecilie Gromsrud", "Cecilie Gromsrud"),
        ("Fredrik S. von der Lippe", "Fredrik S. von der Lippe"),
        ("Øystein Helgheim", "Øystein Helgheim"),
        ("Frederik F. Mørk", "Frederik F. Mørk"),
    ]

    GIRKASSE = [
        ("Automat", "Automat"),
        ("Manuell ", "Manuell"),
    ]

    DRIVSTOFF = [
        ("Bensin", "Bensin"),
        ("Diesel ", "Diesel"),
        ("Elektrisk ", "Elektrisk"),
        ("Hybrid ", "Hybrid"),
    ]

    user = models.ForeignKey(User, related_name='cars', on_delete=models.CASCADE, blank=True, null=True)
    sold = models.BooleanField(default=False, blank=True)
    skjul_annonsen = models.BooleanField(default=False, blank=True)
    
    seller = models.CharField(max_length=300, choices=SELLER, blank=True, null=True)

    
    # Main
    name = models.CharField(max_length=300)
    slug = models.SlugField(max_length=150)
    description = models.TextField(max_length=1000000000000000, blank=True, null=True)
    # Viktig
    expiry_date = models.DateField()
    # Price
    reg_pris = models.CharField(max_length=300, blank=True, null=True)
    fritak_for_reg_pris = models.BooleanField(default=False)
    price = models.IntegerField(max_length=300, default=0, blank=True, null=True)
    # Aditional info 
    service = models.CharField(max_length=700, blank=True, null=True, default="Bilens serviceprogram er fulgt. Det er tatt servicer på bilen i henhold til fabrikkens retningslinjer.")
    garanti = models.CharField(max_length=700, blank=True, null=True, default="Denne bilen kan selges med bruktbilgaranti 24måneder eller frem til 200000km.")

    # Quality
    karosseritype = models.CharField(max_length=100, choices=CHASIS, blank=True, null=True)
    reg_nr = models.CharField(max_length=100, blank=True, null=True)
    year = models.CharField(max_length=100, blank=True, null=True)
    car_brand = models.CharField(max_length=100, blank=True, null=True)
    car_spesifikasjoner = models.CharField(max_length=100, blank=True, null=True)
    km = models.CharField(max_length=100, blank=True, null=True)
    first_registered = models.DateField(blank=True, null=True)
    amount_of_owners = models.CharField(max_length=100, blank=True, null=True)
    last_EU_accepted = models.CharField(max_length=100, blank=True, null=True)
    next_EU_test_deadline = models.CharField(max_length=100, blank=True, null=True)
    # Contact
    adress = models.CharField(max_length=100, blank=True, null=True)
    post_nr = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True, default="Norge")
    mobile_nr = models.CharField(max_length=100, blank=True, null=True)
    owner_mobile_nr = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    # Garanti
    garanti_mnd = models.CharField(max_length=100, blank=True, null=True)
    garanti_km = models.CharField(max_length=100, blank=True, null=True)
    fulgt_bilens_vedlikeholdsprogram = models.BooleanField(default=False, blank=True)
    bytterett = models.BooleanField(default=False, blank=True)
    # Security
    ABS_bremser = models.BooleanField(default=False)
    airbag_foran = models.BooleanField(default=False)
    alarm = models.BooleanField(default=False)
    gjenfinningssystem = models.BooleanField(default=False)
    isofix = models.BooleanField(default=False)
    sentrallås = models.BooleanField(default=False)
    sideairbager = models.BooleanField(default=False)
    startsperre = models.BooleanField(default=False)
    # Media
    AUX_inngang = models.BooleanField(default=False)
    bluetooth = models.BooleanField(default=False)
    cd_spiller = models.BooleanField(default=False)
    handsfree_opplegg = models.BooleanField(default=False)
    head_up_display = models.BooleanField(default=False)
    kassetspiller = models.BooleanField(default=False)
    multifunksjonsratt = models.BooleanField(default=False)
    navigasjonssystem = models.BooleanField(default=False)
    original_telefon = models.BooleanField(default=False)
    radio_DAB = models.BooleanField(default=False)
    radio_FM = models.BooleanField(default=False)
    tv_skjerm_i_baksetet = models.BooleanField(default=False)
    # Motor
    antiskrens = models.BooleanField(default=False)
    antispin = models.BooleanField(default=False)
    diesel_partikkelfilter = models.BooleanField(default=False)
    diffsperre = models.BooleanField(default=False)
    kjørecomputer = models.BooleanField(default=False)
    servostyring = models.BooleanField(default=False)
    # Interior
    elvinduer = models.BooleanField(default=False)
    mørke_ruter_bak = models.BooleanField(default=False)
    seter_i_delskinn = models.BooleanField(default=False)
    seter_i_helskinn = models.BooleanField(default=False)
    soltak_eller_glasstak = models.BooleanField(default=False)
    sportsseter = models.BooleanField(default=False)
    # Komfort
    air_Condition = models.BooleanField(default=False)
    bagasjeromstrekk = models.BooleanField(default=False)
    cruisekontroll = models.BooleanField(default=False)
    cruisekontroll_Adaptiv = models.BooleanField(default=False)
    elektrisk_sete_med_memory = models.BooleanField(default=False)
    elektrisk_sete_uten_memory = models.BooleanField(default=False)
    klimaanlegg = models.BooleanField(default=False)
    kupevarmer = models.BooleanField(default=False)
    luftfjæring = models.BooleanField(default=False)
    midtarmlene = models.BooleanField(default=False)
    motorvarmer = models.BooleanField(default=False)
    nivåregulering = models.BooleanField(default=False)
    nøkkelløs_start = models.BooleanField(default=False)
    oppvarmende_seter = models.BooleanField(default=False)
    # Eksteriør
    elektriske_speil = models.BooleanField(default=False)
    helårsdekk = models.BooleanField(default=False)
    hengerfeste_eller_svingbart = models.BooleanField(default=False)
    led_lys = models.BooleanField(default=False)
    laserlys = models.BooleanField(default=False)
    lasterholdere_eller_skistativ = models.BooleanField(default=False)
    lettmet_felg_sommer = models.BooleanField(default=False)
    lettmet_felg_vinter = models.BooleanField(default=False)
    metalic_lakk = models.BooleanField(default=False)
    sommerhjul = models.BooleanField(default=False)
    vinterhjul = models.BooleanField(default=False)
    takrails = models.BooleanField(default=False)
    xenolys = models.BooleanField(default=False)
    # Fører
    fjernlysassitent = models.BooleanField(default=False)
    lyssensor = models.BooleanField(default=False)
    parkeringsensor_bak = models.BooleanField(default=False)
    parkeringsensor_foran = models.BooleanField(default=False)
    regnesensor = models.BooleanField(default=False)
    ryggekamera = models.BooleanField(default=False)
    # Ekstra
    maks_tilhengervekt_i_kg = models.CharField(max_length=100, blank=True, null=True)
    hovedfarge = models.CharField(max_length=100, blank=True, null=True)
    fargebeskrivelse = models.CharField(max_length=100, blank=True, null=True)
    interiorfarge = models.CharField(max_length=100, blank=True, null=True)
    # Karosseritype
    avgiftsklasse = models.CharField(max_length=100, blank=True, null=True)
    antall_seter = models.CharField(max_length=100, blank=True, null=True)
    antall_dører = models.CharField(max_length=100, blank=True, null=True)
    bagasjeromsvolum_i_liter = models.CharField(max_length=100, blank=True, null=True)
    egenvekt_i_kg = models.CharField(max_length=100, blank=True, null=True)
    rekkevidde = models.CharField(max_length=100, blank=True, null=True)
    girkasse = models.CharField(max_length=100, blank=True, null=True, choices=GIRKASSE)
    girkassebetegnelse = models.CharField(max_length=100, blank=True, null=True)
    hjuldrift = models.CharField(max_length=200, choices=[('Forhjulsdrift', 'Forhjulsdrift'), ('Bakhjulsdrift', 'Bakhjulsdrift'), ['Firehjulsdrift', 'Firehjulsdrift']], blank=True, null=True)
    hjuldriftbetegnelse = models.CharField(max_length=100, blank=True, null=True)
    modellspesifikasjon = models.CharField(max_length=100, blank=True, null=True)
    bilen_står_i = models.CharField(choices=PLACE,max_length=100, blank=True, null=True)
    drivstoff = models.CharField(max_length=100, blank=True, null=True, choices=DRIVSTOFF)
    effekt_i_hk = models.CharField(max_length=100, blank=True, null=True)
    batterikapasitet_i_kWh = models.CharField(max_length=100, blank=True, null=True)
    # Images
    map_images = models.ImageField(blank=True, default='', upload_to='static/images/other/')
    image1 = models.ImageField(blank=False, default='', upload_to='static/images/other/cars/')
    image2 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image3 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image4 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image5 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image6 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image7 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image8 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image9 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image10 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image11 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image12 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image13 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image14 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image15 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image16 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image17 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image18 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image19 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image20 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image21 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image22 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image23 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image24 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image25 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image26 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image27 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image28 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image29 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image30 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image31 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image32 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image33 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image34 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image35 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image36 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image37 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image38 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image39 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image40 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image41 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image42 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image43 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image44 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image45 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image46 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image47 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image48 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image49 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image50 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image51 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image52 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image53 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image54 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image55 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image56 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image57 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image58 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image59 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image60 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image61 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image62 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image63 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image64 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image65 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image66 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image67 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image68 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image69 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image70 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image71 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image72 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image73 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image74 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image75 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image76 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image77 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image78 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image79 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')
    image80 = models.ImageField(blank=True, default='', upload_to='static/images/other/cars/')



    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'reg_nr': self.reg_nr,
            'car_spesifikasjoner': self.car_spesifikasjoner,
        }
    
    @property
    def days_until_expiry(self):
        today = timezone.now().date()
        return (self.expiry_date - today).days
    
    
    def num_active_images(self):
        # Count the number of active images
        fields = [f.name for f in Car._meta.get_fields() if isinstance(f, models.ImageField)]
        return max(0, sum(bool(getattr(self, field)) for field in fields) - 1)

    
    def highest_bid_price(self):
        highest_bid = self.bud_set.aggregate(models.Max('bid_amount'))['bid_amount__max']
        return highest_bid or 0

    def __str__(self):
        return f"Bil: {self.name} {self.car_spesifikasjoner}"
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        if self.sold:
            # If sold and no SoldCar instance exists, create one
            sold_car, created = SoldCar.objects.get_or_create(car=self)
            if created:
                sold_car.date_sold = self.expiry_date
                sold_car.selling_price = self.price
                sold_car.save()
        else:
            # If not sold, delete any existing SoldCar instance
            SoldCar.objects.filter(car=self).delete()
        
        return super(Car, self).save(*args, **kwargs)
        
    
    def get_absolute_url(self):
        return f'/{self.slug}/'
    
    def admin_photo(self):
            return mark_safe('<img src="{}" width="100" />'.format(self.image1.url))
    admin_photo.short_description = 'image'
    admin_photo.allow_tags = True

    @property
    def image_url(self):
        return '%s%s' % (settings.ALLOWED_HOSTS, self.image.url) if self.image else ''    
      

class SoldCar(models.Model):
    car = models.OneToOneField(Car, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.car.name}" 


class Bud(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, blank=True, default='')
    user = models.ForeignKey(User, related_name='bud', on_delete=models.CASCADE, blank=True, null=True)
    bid_amount = models.IntegerField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined')], default='pending')

    def __str__(self):
        return f"Bid på {self.bid_amount}kr,- på {self.car} ({self.id}) av {self.user}"      
    
    def days_until_expiry(self):
        today = timezone.now().date()
        return (self.expiry_date - today).days
    
    def accept_bid(self):
        self.status = 'accepted'
        self.save()
        self.car.sold = True
        self.car.save()

    def decline_bid(self):
        self.status = 'declined'
        self.save()


class TestDrive(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, blank=True, default='')
    name = models.CharField(max_length=400, blank=False)
    email = models.EmailField(max_length=100, blank=False)
    phone_number = models.CharField(max_length=400, blank=False)
    message = models.TextField(blank=False)
    date1_Y_m_d = models.CharField(max_length=100, blank=True, null=True)
    time1 = models.CharField(max_length=100, blank=True, null=True)
    date2_Y_m_d = models.CharField(max_length=100, blank=True, null=True)
    time2 = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Prøvekjøring på {self.car} av {self.name}"      



class Buy(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, blank=True, default='')
    user = models.ForeignKey(User, related_name='buy', on_delete=models.SET_NULL, blank=True, null=True)
    forsikring = models.CharField(max_length=20, choices=[('no', 'Nei'), ('yes', 'Ja')], default='no')
    garanti = models.CharField(max_length=20, choices=[('no', 'Nei'), ('yes', 'Ja')], default='no')
    steps = models.CharField(max_length=20, choices=[('zero', '0'), ('one', '1'), ('two', '2'), ('three', '3'), ('three-half', '3.5'), ('four', '4')], default='zero')

    def __str__(self):
        return f"Kjøp på {self.car} av {self.user}"      

    def step_one(self):
        self.steps = 'one'
        self.save()

    def step_one_forsikring(self):
        self.forsikring = 'yes'
        self.save()

    def step_two(self):
        self.steps = 'two'
        self.save()

    def step_two_garanti(self):
        self.garanti = 'yes'
        self.save()
 
    def step_three(self):
        self.steps = 'three-half'
        self.save()



class Egenerkeling(models.Model):
    # Steps
    stepOne = models.BooleanField(blank=True, default=False)
    stepTwo = models.BooleanField(blank=True, default=False)
    stepThree = models.BooleanField(blank=True, default=False)
    stepFour = models.BooleanField(blank=True, default=False)
    stepFive = models.BooleanField(blank=True, default=False)
    
    car = models.ForeignKey(Car, related_name='egenerkling', on_delete=models.CASCADE, blank=True, default='')
    user = models.ForeignKey(User, related_name='egenerkling', on_delete=models.SET_NULL, blank=True, null=True)
    # Contact info
    name = models.CharField(max_length=200, blank=True, null=True)
    mobile_nr = models.CharField(max_length=200, blank=True, null=True)
    adress = models.CharField(max_length=200, blank=True, null=True)
    personal_number = models.CharField(max_length=200, blank=True, null=True)
    account_number = models.CharField(max_length=200, blank=True, null=True)
    # Car info
    reg_nr = models.CharField(max_length=200, blank=True, null=True)
    km = models.CharField(max_length=200, blank=True, null=True)
    owners = models.CharField(max_length=200, blank=True, null=True)
    bruktimportert = models.CharField(max_length=200, blank=True, null=True)
    demobil = models.CharField(max_length=200, blank=True, null=True)
    bruksmerker_bilde1 = models.ImageField(blank=True, null=True, upload_to='static/images/other/cars/')
    bruksmerker_bilde2 = models.ImageField(blank=True, null=True, upload_to='static/images/other/cars/')
    bruksmerker_bilde3 = models.ImageField(blank=True, null=True, upload_to='static/images/other/cars/')
    bruksmerker_bilde4 = models.ImageField(blank=True, null=True, upload_to='static/images/other/cars/')
    bruksmerker_bilde5 = models.ImageField(blank=True, null=True, upload_to='static/images/other/cars/')
    bruksmerker_bilde6 = models.ImageField(blank=True, null=True, upload_to='static/images/other/cars/')
    bruksmerker_bilde7 = models.ImageField(blank=True, null=True, upload_to='static/images/other/cars/')
    bruksmerker_bilde8 = models.ImageField(blank=True, null=True, upload_to='static/images/other/cars/')
    bruksmerker_bilde9 = models.ImageField(blank=True, null=True, upload_to='static/images/other/cars/')
    bruksmerker_bilde10 = models.ImageField(blank=True, null=True, upload_to='static/images/other/cars/')
    bruksmerker_bilde11 = models.ImageField(blank=True, null=True, upload_to='static/images/other/cars/')
    bruksmerker_bilde12 = models.ImageField(blank=True, null=True, upload_to='static/images/other/cars/')
    bruksmerker_bilde13 = models.ImageField(blank=True, null=True, upload_to='static/images/other/cars/')
    bruksmerker_bilde14 = models.ImageField(blank=True, null=True, upload_to='static/images/other/cars/')
    bruksmerker_bilde15 = models.ImageField(blank=True, null=True, upload_to='static/images/other/cars/')
    bruksmerker_bilde16 = models.ImageField(blank=True, null=True, upload_to='static/images/other/cars/')
    bruksmerker_bilde17 = models.ImageField(blank=True, null=True, upload_to='static/images/other/cars/')
    bruksmerker_bilde18 = models.ImageField(blank=True, null=True, upload_to='static/images/other/cars/')
    bruksmerker_bilde19 = models.ImageField(blank=True, null=True, upload_to='static/images/other/cars/')
    bruksmerker_bilde20 = models.ImageField(blank=True, null=True, upload_to='static/images/other/cars/')
    bruksmerker_text = models.TextField(blank=True, null=True)
    # Tools
    file_tools = models.FileField(max_length=200, blank=True, null=True)
    manual_tools = models.TextField(max_length=1000, blank=True, null=True)
    # Service
    verksted_history = models.FileField(max_length=200, blank=True, null=True)
    service_history = models.FileField(max_length=200, blank=True, null=True)
    next_service = models.CharField(max_length=100, blank=True, null=True)
    # Garanti
    left_garantier = models.CharField(max_length=900, blank=True, null=True)
    new_car_garanti = models.CharField(max_length=900, blank=True, null=True)
    batery = models.CharField(max_length=900, blank=True, null=True)
    karrosseri = models.CharField(max_length=900, blank=True, null=True)
    drivverk = models.CharField(max_length=900, blank=True, null=True)

    def __str__(self):
        return f"Egenærkling på bil {self.car} av {self.name}"      
