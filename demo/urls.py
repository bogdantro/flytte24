from django.urls import path, include
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

    path('flytteforesporsel/', include('apps.leads.urls')),
    path('dashboard/', include('apps.dashboard.urls')),

    path('', home, name='home'),

    path('send-flytteforesporsel/', send_flytteforesporsel, name='send_flytteforesporsel'),
    path("takk-for-din-foresporsel/<int:inquiry_id>/", takk_for_foresporsel, name="takk_for_foresporsel"),

    path('contact-us/', contact, name='contact'), 
    path('about-us/', about, name='about'), 
    path('for-bedrifter/', for_business, name='for_business'), 
    path('for-bedrifter/bli-partner/', for_business_partner, name='for_business_partner'), 
    

    path('for-bedrifter/bruker/logg-inn/', views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('reg/fullfor/lag-bruker/', signup, name='signup'),
    path('for-bedrifter/min-bruker/logg-ut/', views.LogoutView.as_view(), name='logout'),

    path('for-bedrifter/min-bruker/', myaccount, name='myaccount'),
    path('for-bedrifter/min-bruker/bedriftsinformasjon/', edit_public_profile, name='edit_public_profile'),
    path("for-bedrifter/foresporsel-database/", foresporsel_database, name="foresporsel_database"),

    path('bedrift/<int:business_id>/', public_business_profile, name='public_business_profile'),




    # API
    path('api/check-user/', check_user_exists, name='check_user_exists'),

    path('blogg/', blog_index, name='blog_index'),
    path('blogg/<slug:slug>/', blog_article, name='blog_article'),
    path('byraer/', agency_list, name='agency_list'),
    path('byraer/<slug:slug>/', agency_detail, name='agency_detail'),

    # Catch-all for CMS pages (apps.pages) at any path other than "/" —
    # e.g. a duplicated page (dashboard:page_duplicate). Must stay LAST:
    # every route above is tried first, and this only matches paths
    # ending in "/", so it never shadows media file URLs (which don't).
    path('<path:page_path>/', render_page, name='render_page'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


