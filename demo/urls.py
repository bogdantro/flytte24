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
from apps.userprofile.views import *
from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns


sitemaps = {
    'static': StaticViewsSitemap,
}


urlpatterns = [
    path('admin/', admin.site.urls),

    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}),

    path('', home, name='home'), 

    path('flytteforesporsel/', flytteforesporsel, name='flytteforesporsel'),
    path('send-flytteforesporsel/', send_flytteforesporsel, name='send_flytteforesporsel'),

    path('contact-us/', contact, name='contact'), 
    path('about-us/', about, name='about'), 
    path('for-bedrifter/', for_business, name='for_business'), 
    path('for-bedrifter/bli-partner/', for_business_partner, name='for_business_partner'), 
    

    path('for-bedrifter/bruker/logg-inn/', views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('reg/fullfor/lag-bruker/', signup, name='signup'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    path('for-bedrifter/min-bruker/', myaccount, name='myaccount'),


    # API
    path('api/check-user/', check_user_exists, name='check_user_exists'),

    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


