"""Environment ESG dashboard models (Admin-managed)."""

from django.db import models


class ReportYear(models.Model):
    """
    Configurable reporting years (past, current, future).
    Only years with is_visible=True appear on the public dashboard.
    """

    year = models.PositiveIntegerField(
        unique=True,
        verbose_name="Year",
        help_text="e.g. 2024, 2025, 2026, 2027",
    )
    label = models.CharField(
        max_length=64,
        blank=True,
        help_text="Optional display label (defaults to year number).",
    )
    is_visible = models.BooleanField(
        default=True,
        verbose_name="Show on dashboard",
        help_text="If unchecked, this year is hidden from the public year list (Admin can still upload data).",
    )
    sort_order = models.IntegerField(
        default=0,
        help_text="Higher appears first in the year selector.",
    )

    class Meta:
        ordering = ("-sort_order", "-year")
        verbose_name = "Report year"
        verbose_name_plural = "Report years"

    def __str__(self) -> str:
        label = self.label or str(self.year)
        flag = "" if self.is_visible else " (hidden)"
        return f"{label}{flag}"


class EnvironmentWorkbook(models.Model):
    """
    Environment / ESG workbook (Environment-Tamer-Logistics-{year}.xlsx).
    Each sheet becomes a dashboard tab; Overview is aggregated on parse.
    """

    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Title (optional)",
        help_text="Optional label in Admin only.",
    )
    report_year = models.PositiveIntegerField(
        default=2025,
        verbose_name="Report year",
        help_text="Reporting year (e.g. 2025 or 2026). Only one active workbook per year.",
    )
    file = models.FileField(
        upload_to="environment_workbooks/%Y/%m/",
        verbose_name="Workbook (.xlsx / .xlsm)",
        help_text=(
            "Upload Environment-Tamer-Logistics-{report_year}.xlsx (e.g. "
            "Environment-Tamer-Logistics-2026.xlsx). Expected sheets: Data Governance, "
            "1. Electricty, 2. Energy, 3. Transportation, 4. Water - LITERS, "
            "5. Waste, 6. Fugitive gases."
        ),
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active",
        help_text="Active workbook for this report year on the public dashboard.",
    )
    parsed_snapshot = models.JSONField(
        null=True,
        blank=True,
        editable=False,
        verbose_name="Parsed ESG data (auto)",
        help_text="Filled when the file is saved if the workbook structure is valid.",
    )

    class Meta:
        ordering = ("-uploaded_at",)
        verbose_name = "Environment ESG workbook"
        verbose_name_plural = "Environment ESG workbooks"

    def __str__(self):
        label = f"ESG {self.report_year}"
        if self.title:
            return f"{label} — {self.title}"
        if self.file:
            return f"{label} — {self.file.name.rsplit('/', 1)[-1]}"
        return label
