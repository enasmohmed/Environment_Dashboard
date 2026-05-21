from django.db import migrations, models


def seed_report_years(apps, schema_editor):
    ReportYear = apps.get_model("dashboard", "ReportYear")
    for i, year in enumerate((2025, 2026)):
        ReportYear.objects.get_or_create(
            year=year,
            defaults={
                "label": str(year),
                "is_visible": True,
                "sort_order": 100 - i,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0036_alter_environmentworkbook_is_active_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReportYear",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "year",
                    models.PositiveIntegerField(
                        help_text="e.g. 2024, 2025, 2026, 2027",
                        unique=True,
                        verbose_name="Year",
                    ),
                ),
                (
                    "label",
                    models.CharField(
                        blank=True,
                        help_text="Optional display label (defaults to year number).",
                        max_length=64,
                    ),
                ),
                (
                    "is_visible",
                    models.BooleanField(
                        default=True,
                        help_text="If unchecked, this year is hidden from the public year list (Admin can still upload data).",
                        verbose_name="Show on dashboard",
                    ),
                ),
                (
                    "sort_order",
                    models.IntegerField(
                        default=0,
                        help_text="Higher appears first in the year selector.",
                    ),
                ),
            ],
            options={
                "verbose_name": "Report year",
                "verbose_name_plural": "Report years",
                "ordering": ("-sort_order", "-year"),
            },
        ),
        migrations.RunPython(seed_report_years, migrations.RunPython.noop),
    ]
