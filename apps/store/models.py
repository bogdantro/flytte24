from django.db import models
from django.conf import settings
from django.utils.text import slugify
 

class Car(models.Model):
    # Main
    name = models.CharField(max_length=300)
    slug = models.SlugField(max_length=150)
    description = models.TextField(blank=False)
    # Price
    reg_pris = models.CharField(max_length=300, blank=True, null=True)
    fritak_for_reg_pris = models.BooleanField(default=False)
    price = models.FloatField(max_length=300, default=0, blank=True, null=True)

    chasis = models.CharField(max_length=100, blank=True, null=True)
    reg_nr = models.CharField(max_length=100, blank=True, null=True)
    year = models.CharField(max_length=100, blank=True, null=True)
    car_brand = models.CharField(max_length=100, blank=True, null=True)
    car_model = models.CharField(max_length=100, blank=True, null=True)
    # Description
    description = models.CharField(max_length=100, blank=True, null=True)
    # Contact
    adress = models.CharField(max_length=100, blank=True, null=True)
    post_nr = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    mobile_nr = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    # Add ons
    
    # Images
    image1 = models.ImageField(blank=False, default='', upload_to='other/products/')
    image2 = models.ImageField(blank=True, default='', upload_to='other/products/')
    image3 = models.ImageField(blank=True, default='', upload_to='other/products/')
    image4 = models.ImageField(blank=True, default='', upload_to='other/products/')
    image5 = models.ImageField(blank=True, default='', upload_to='other/products/')
    image6 = models.ImageField(blank=True, default='', upload_to='other/products/')
    image7 = models.ImageField(blank=True, default='', upload_to='other/products/')
    image8 = models.ImageField(blank=True, default='', upload_to='other/products/')
    image9 = models.ImageField(blank=True, default='', upload_to='other/products/')
    image10 = models.ImageField(blank=True, default='', upload_to='other/products/')
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        return super(Car, self).save(*args, **kwargs)
    
    def get_absolute_url(self):
        return f'/{self.slug}/'

    @property
    def image_url(self):
        return '%s%s' % (settings.ALLOWED_HOSTS, self.image.url) if self.image else ''    
      