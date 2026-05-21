from django.contrib import admin

from .forms import EnvironmentWorkbookAdminForm
from .models import EnvironmentWorkbook, ReportYear


@admin.register(ReportYear)
class ReportYearAdmin(admin.ModelAdmin):
    list_display = ("year", "label", "is_visible", "sort_order")
    list_editable = ("is_visible", "sort_order", "label")
    list_filter = ("is_visible",)
    search_fields = ("year", "label")
    ordering = ("-sort_order", "-year")
    fieldsets = (
        (
            None,
            {
                "fields": ("year", "label", "is_visible", "sort_order"),
                "description": (
                    "Add any reporting year (past or future). "
                    "Only years with “Show on dashboard” checked appear on the public site. "
                    "Then upload a workbook for that year under Environment ESG workbooks."
                ),
            },
        ),
    )


@admin.register(EnvironmentWorkbook)
class EnvironmentWorkbookAdmin(admin.ModelAdmin):
    form = EnvironmentWorkbookAdminForm
    list_display = (
        "report_year",
        "title",
        "file_basename",
        "is_active",
        "uploaded_at",
        "snapshot_brief",
    )
    list_filter = ("is_active", "report_year")
    readonly_fields = ("uploaded_at", "snapshot_brief")
    fieldsets = (
        (
            None,
            {
                "fields": ("title", "report_year", "file", "is_active"),
                "description": (
                    "Upload Environment-Tamer-Logistics-{year}.xlsx per reporting year "
                    "(e.g. Environment-Tamer-Logistics-2026.xlsx). "
                    "Each sheet maps to a dashboard tab. One active workbook per year."
                ),
            },
        ),
        ("Status", {"fields": ("uploaded_at", "snapshot_brief")}),
    )

    def file_basename(self, obj):
        if not obj or not obj.file:
            return "—"
        return obj.file.name.rsplit("/", 1)[-1]

    file_basename.short_description = "File"

    def snapshot_brief(self, obj):
        if not obj or not obj.pk:
            return "—"
        snap = obj.parsed_snapshot
        if not snap:
            return "—"
        tabs = snap.get("tabs") or []
        year = snap.get("report_year") or (snap.get("overview") or {}).get("year") or obj.report_year
        return f"Year {year} · {len(tabs)} tab(s) ready"

    snapshot_brief.short_description = "Parsed snapshot"

    def save_model(self, request, obj, form, change):
        snapshot = form.instance.parsed_snapshot
        super().save_model(request, obj, form, change)
        EnvironmentWorkbook.objects.filter(pk=obj.pk).update(parsed_snapshot=snapshot)
        if obj.is_active:
            EnvironmentWorkbook.objects.exclude(pk=obj.pk).filter(
                is_active=True, report_year=obj.report_year
            ).update(is_active=False)
