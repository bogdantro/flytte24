from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("logg-inn/", views.dashboard_login, name="login"),
    path("logg-ut/", views.dashboard_logout, name="logout"),
    path("", views.lead_list, name="lead_list"),
    path("lead/<int:pk>/", views.lead_detail, name="lead_detail"),
    path("lead/<int:pk>/status/", views.update_status, name="update_status"),
    path("lead/<int:pk>/slett/", views.delete_lead, name="delete_lead"),
    path("sider/", views.page_list, name="page_list"),
    path("sider/<int:pk>/", views.page_edit, name="page_edit"),
    path("sider/<int:pk>/dupliser/", views.page_duplicate, name="page_duplicate"),
    path("sider/<int:pk>/slett/", views.page_delete, name="page_delete"),
    path("bedrifter/", views.business_list, name="business_list"),
    path("bedrifter/<int:pk>/", views.business_detail, name="business_detail"),
    path("bedrifter/<int:pk>/aktiver/", views.business_toggle_active, name="business_toggle_active"),
    path("bedrifter/<int:pk>/bilde/legg-til/", views.business_image_add, name="business_image_add"),
    path("bedrifter/<int:pk>/bilde/<int:image_pk>/slett/", views.business_image_delete, name="business_image_delete"),
]
