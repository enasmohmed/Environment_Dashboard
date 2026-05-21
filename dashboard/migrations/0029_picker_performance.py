# Picker performance tab: program + shift rows + Excel import support

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0028_process_improvement_program"),
    ]

    operations = [
        migrations.CreateModel(
            name="PickerPerformanceProgram",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(default="Picker performance", max_length=255, verbose_name="Section title")),
                (
                    "subtitle",
                    models.CharField(
                        blank=True,
                        help_text="e.g. Reach truck · target lines per shift.",
                        max_length=255,
                        verbose_name="Subtitle",
                    ),
                ),
                (
                    "target_lines",
                    models.PositiveSmallIntegerField(
                        default=200,
                        help_text="Shifts at or above this count as green for KPIs and legend.",
                        verbose_name="Target lines (green shift)",
                    ),
                ),
                (
                    "period_label",
                    models.CharField(
                        blank=True,
                        help_text='Shown in the header (e.g. "Oct 1–30, 2025").',
                        max_length=120,
                        verbose_name="Period label",
                    ),
                ),
                (
                    "excel_sheet_name",
                    models.CharField(
                        default="Dashboard",
                        help_text='Sheet to read on import (e.g. "Dashboard").',
                        max_length=64,
                        verbose_name="Excel sheet name",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="If several exist, the active one with the latest update is used on the home page.",
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Picker performance program",
                "verbose_name_plural": "Picker performance programs",
                "ordering": ("-updated_at",),
            },
        ),
        migrations.CreateModel(
            name="PickerShiftRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "work_date",
                    models.DateField(
                        blank=True,
                        help_text="Required for trend, best weekday, and weekly shift comparison.",
                        null=True,
                        verbose_name="Date",
                    ),
                ),
                ("picker_name", models.CharField(max_length=128, verbose_name="Picker name")),
                ("lines", models.PositiveIntegerField(verbose_name="Lines this shift")),
                (
                    "shift_band",
                    models.CharField(
                        choices=[
                            ("MORNING", "Morning"),
                            ("EVENING", "Evening / night"),
                            ("OTHER", "Other / unknown"),
                        ],
                        default="OTHER",
                        help_text="Morning vs evening for weekly comparison (mapped from Excel or set manually).",
                        max_length=16,
                        verbose_name="Shift",
                    ),
                ),
                (
                    "program",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="shifts",
                        to="dashboard.pickerperformanceprogram",
                    ),
                ),
            ],
            options={
                "verbose_name": "Picker shift record",
                "verbose_name_plural": "Picker shift records",
                "ordering": ("work_date", "picker_name", "id"),
            },
        ),
    ]
