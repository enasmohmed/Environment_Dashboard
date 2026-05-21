# Generated manually for ProductivityDashboard models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0020_warehouseaccountoverview_raw_values"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductivityDashboard",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("module_number", models.CharField(default="01", help_text='Shown before "Module" (e.g. 01).', max_length=16)),
                ("title", models.CharField(default="Productivity Dashboard", max_length=255)),
                ("description", models.TextField(blank=True, help_text="Paragraph under the module title.")),
                (
                    "highlight_title",
                    models.CharField(
                        blank=True,
                        help_text="Dark bar — left headline (e.g. Overtime cap rule).",
                        max_length=255,
                    ),
                ),
                (
                    "highlight_description",
                    models.TextField(blank=True, help_text="Dark bar — supporting text."),
                ),
                (
                    "highlight_value",
                    models.CharField(blank=True, help_text="Dark bar — right value (e.g. 150 hrs).", max_length=120),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="If several exist, the active one with the latest update is shown on the site.",
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Productivity dashboard",
                "verbose_name_plural": "Productivity dashboards",
                "ordering": ("-updated_at",),
            },
        ),
        migrations.CreateModel(
            name="ProductivityDashboardCard",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                (
                    "icon_kind",
                    models.CharField(
                        choices=[
                            ("red_ot", "Red arrow + OT"),
                            ("green_out", "Green arrow + OUT"),
                            ("bell", "Bell"),
                            ("stop", "Stop / cap bar"),
                            ("image", "Uploaded image"),
                        ],
                        default="bell",
                        max_length=16,
                    ),
                ),
                (
                    "icon_image",
                    models.ImageField(
                        blank=True,
                        help_text="Used when icon kind is “Uploaded image”.",
                        null=True,
                        upload_to="productivity/card_icons/",
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("body", models.TextField()),
                (
                    "dashboard",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cards",
                        to="dashboard.productivitydashboard",
                    ),
                ),
            ],
            options={
                "verbose_name": "Productivity dashboard card",
                "verbose_name_plural": "Productivity dashboard cards",
                "ordering": ("sort_order", "id"),
            },
        ),
    ]
