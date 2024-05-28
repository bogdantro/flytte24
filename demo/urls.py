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

sitemaps = {
    'static': StaticViewsSitemap,
}


urlpatterns = [
    path('admin/', admin.site.urls),

    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}),

    path('', home, name='home'),


    path('login/', views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('make-an-account/', signup, name='signup'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    path('myaccount/', myaccount, name='myaccount'),


    path('become-a-member/', beome_member, name='beome_member'),

    path('create-checkout-session/', create_checkout_session, name='create_checkout_session'),
    path('webhook/', stripe_webhook, name='stripe_webhook'),
    path('success/', success, name='success'),
    path('cancel/', cancel, name='cancel'),






    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)