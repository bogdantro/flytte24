from django.urls import path
from apps.core.views import *
from django.conf.urls.static import *
from django.conf import *
from django.contrib.auth import views

from apps.core.views import *
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views
from apps.store.views import *
from apps.core.sitemaps import *
from django.contrib.sitemaps.views import sitemap

from django.contrib import admin

sitemaps = {
    'static': StaticViewsSitemap,
}


urlpatterns = [
    path('bilmeglerne/admin/login/', admin.site.urls),

    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}),

    path('', home, name='home'),
    path('selg-bilen/', sell, name='sell'),
    path('selg-bilen/book-time/', book_time, name='book_time'),
    path('selg-bilen/book-time/avbestill-time/', un_book, name='un_book'),


    path('kontakt-oss/', contact, name='contact'),
    path('verdivurdering/', verdivurdering, name='verdivurdering'),
    
    path('success/', success, name='success'),

    path('tjenester/', services, name='services'),
    path('tjenester/verksted/', verksted, name='verksted'),
    path('tjenester/transport/', transport, name='transport'),
    path('tjenester/forsikring/', forsikring, name='forsikring'),
    path('tjenester/finansiering/', finansiering, name='finansiering'),
    path('tjenester/garanti/', garanti, name='garanti'),
    path('tjenester/avtale/', avtale, name='avtale'),

    path('om-oss/', about, name='about'),

    path('personvernerklaering/', personerk, name='personerk'),
    path('salgvilkaar/', salgvilkaar, name='salgvilkaar'),
    
    path('priser/', price, name='price'),




    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)