from django.urls import path

from .views import HomeView, environment_api

app_name = "dashboard"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("api/environment/", environment_api, name="environment_api"),
]
