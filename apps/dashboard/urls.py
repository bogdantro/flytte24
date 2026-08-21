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
]
