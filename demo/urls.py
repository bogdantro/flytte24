from django.urls import path
from apps.core.views import *
from django.conf.urls.static import *
from django.conf import *
from django.contrib import admin
from django.contrib.auth import views

from apps.core.views import *
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views
from apps.userprofile.views import *

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', home, name='home'),
    path('selg-bilen/', sell, name='sell'),
    path('selg-bilen/book-time/', book_time, name='book_time'),

    path('kontakt-oss/', contact, name='contact'),
    path('verdivurdering/', verdivurdering, name='verdivurdering'),
    
    path('success/', success, name='success'),

    path('om-oss/', about, name='about'),

    path('personvernerklaering/', personerk, name='personerk'),
    
    path('priser/', price, name='price'),

    # Auth
    path('logg-inn/', views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('snodrivlagbruker123456/', signup, name='signup'),
    path('logg-ut/', views.LogoutView.as_view(), name='logout'),
    path('min-bruker/', myaccount, name='myaccount'),


    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)