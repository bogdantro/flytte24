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
    'cities': CitySitemap,
    'districts': DistrictSitemap,
    'agencies': AgencySitemap,
    'articles': ArticleSitemap,
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
    path('for-bedrifter/soknad-sendt/', partner_wizard_thank_you, name='partner_wizard_thank_you'),


    path('for-bedrifter/bruker/logg-inn/', views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('reg/fullfor/lag-bruker/', signup, name='signup'),
    path('for-bedrifter/min-bruker/logg-ut/', views.LogoutView.as_view(), name='logout'),

    # Password reset (anonymous — "Glemt passord?" on the login page) and
    # password change (logged-in — from myaccount). Django's own built-in
    # auth views; allauth is installed but its urls were never include()'d,
    # so these are the actual auth flow rather than a second, unused one.
    path(
        'for-bedrifter/bruker/tilbakestill-passord/',
        views.PasswordResetView.as_view(
            template_name='core/password_reset_form.html',
            email_template_name='core/password_reset_email.html',
            subject_template_name='core/password_reset_subject.txt',
            success_url='/for-bedrifter/bruker/tilbakestill-passord/sendt/',
        ),
        name='password_reset',
    ),
    path(
        'for-bedrifter/bruker/tilbakestill-passord/sendt/',
        views.PasswordResetDoneView.as_view(template_name='core/password_reset_done.html'),
        name='password_reset_done',
    ),
    path(
        'for-bedrifter/bruker/tilbakestill-passord/<uidb64>/<token>/',
        views.PasswordResetConfirmView.as_view(
            template_name='core/password_reset_confirm.html',
            success_url='/for-bedrifter/bruker/tilbakestill-passord/fullfort/',
        ),
        name='password_reset_confirm',
    ),
    path(
        'for-bedrifter/bruker/tilbakestill-passord/fullfort/',
        views.PasswordResetCompleteView.as_view(template_name='core/password_reset_complete.html'),
        name='password_reset_complete',
    ),
    path(
        'for-bedrifter/min-bruker/bytt-passord/',
        views.PasswordChangeView.as_view(
            template_name='core/password_change_form.html',
            success_url='/for-bedrifter/min-bruker/bytt-passord/fullfort/',
            extra_context={'active_nav': 'settings'},
        ),
        name='account_settings',
    ),
    path(
        'for-bedrifter/min-bruker/bytt-passord/fullfort/',
        views.PasswordChangeDoneView.as_view(
            template_name='core/password_change_done.html',
            extra_context={'active_nav': 'settings'},
        ),
        name='password_change_done',
    ),

    path('for-bedrifter/min-bruker/', myaccount, name='myaccount'),
    path('for-bedrifter/min-bruker/bedriftsinformasjon/', edit_public_profile, name='edit_public_profile'),
    path('for-bedrifter/min-bruker/dekning/', update_business_coverage, name='update_business_coverage'),
    path('for-bedrifter/min-bruker/bilde/legg-til/', business_image_add, name='business_image_add'),
    path('for-bedrifter/min-bruker/bilde/<int:image_pk>/slett/', business_image_delete, name='business_image_delete'),
    path("for-bedrifter/foresporsel-database/", foresporsel_database, name="foresporsel_database"),
    path("for-bedrifter/min-bruker/faktura.pdf", my_invoice_pdf, name="my_invoice_pdf"),
    path("for-bedrifter/min-bruker/lead/<int:pk>/", business_lead_detail, name="business_lead_detail"),
    path("for-bedrifter/min-bruker/lead/<int:pk>/meld/", report_bad_lead, name="report_bad_lead"),

    path('bedrifter/', business_directory, name='business_directory'),
    path('bedrift/<int:business_id>/', public_business_profile, name='public_business_profile'),




    path('blogg/', blog_index, name='blog_index'),
    path('blogg/<slug:slug>/', blog_article, name='blog_article'),
    path('byraer/', agency_list, name='agency_list'),
    path('byraer/<slug:slug>/', agency_detail, name='agency_detail'),

    # City landing pages (spec §7) — 5 explicit literal paths rather than one
    # <slug:city_slug>/ pattern, so an unrelated single-segment CMS page path
    # (e.g. a duplicated page at /forside-kopi/) still falls through to the
    # render_page catch-all below instead of being swallowed here.
    path('oslo/', city_detail, {'city_slug': 'oslo'}, name='city_oslo'),
    path('bergen/', city_detail, {'city_slug': 'bergen'}, name='city_bergen'),
    path('trondheim/', city_detail, {'city_slug': 'trondheim'}, name='city_trondheim'),
    path('stavanger/', city_detail, {'city_slug': 'stavanger'}, name='city_stavanger'),
    path('tromso/', city_detail, {'city_slug': 'tromso'}, name='city_tromso'),

    # Oslo district pages (spec §8) — the only city with sub-pages. Must come
    # after 'oslo/' above: Django tries patterns in order, and 'oslo/' only
    # matches the bare path (no further segment), so there's no ambiguity —
    # this just needs to exist before the catch-all below.
    path('oslo/<slug:district_slug>/', district_detail, name='district_detail'),

    # Catch-all for CMS pages (apps.pages) at any path other than "/" —
    # e.g. a duplicated page (dashboard:page_duplicate). Must stay LAST:
    # every route above is tried first, and this only matches paths
    # ending in "/", so it never shadows media file URLs (which don't).
    path('<path:page_path>/', render_page, name='render_page'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


