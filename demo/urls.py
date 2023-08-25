from django.urls import path
from apps.core.views import *
from django.conf.urls.static import *
from django.conf import *
from django.contrib.auth import views

from apps.core.views import *
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views
from apps.userprofile.views import *
from apps.store.views import *

from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', home, name='home'),
    path('selg-bilen/', sell, name='sell'),
    path('selg-bilen/book-time/', book_time, name='book_time'),
    path('selg-bilen/book-time/avbestill-time/', un_book, name='un_book'),

    path('kjøp-bil/', buy_car, name='buy_car'),
    path('bil/:<slug>/', car_detail, name='car_detail'),

    path('kontakt-oss/', contact, name='contact'),
    path('verdivurdering/', verdivurdering, name='verdivurdering'),
    
    path('success/', success, name='success'),

    path('om-oss/', about, name='about'),

    path('personvernerklaering/', personerk, name='personerk'),
    path('salgvilkaar/', salgvilkaar, name='salgvilkaar'),
    
    path('priser/', price, name='price'),

    # Auth
    path('logg-inn/', views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('lag-bruker/', signup, name='signup'),
    path('logg-ut/', views.LogoutView.as_view(), name='logout'),

    path('min-bruker/', myaccount, name='myaccount'),
    path('min-bruker/rediger-min-info/', edit_user_info, name='edit_user_info'),
    path('min-bruker/mine-annonser/', mine_annonser, name='mine_annonser'),
    path('min-bruker/mine-bud/', mine_bud, name='mine_bud'),
    path('min-bruker/mine-kjøp/', mine_kjøp, name='mine_kjøp'),
    path('min-bruker/kommende-visninger/', kommende_visninger, name='kommende_visninger'),

    path('accept_bid/<int:car_id>/', accept_highest_bid, name='accept_highest_bid'),
    path('decline_bid/<int:car_id>/', decline_highest_bid, name='decline_highest_bid'),

    path('passord-reset/', pass_reset, name='pass_reset'),



    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)