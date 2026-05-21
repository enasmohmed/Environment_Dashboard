from django.apps import AppConfig
from django.contrib import admin


class DashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"
    verbose_name = "Environment ESG"

    def ready(self):
        admin.site.site_header = admin.site.site_title = "Environment ESG Dashboard"
        admin.site.index_title = "Administration"
