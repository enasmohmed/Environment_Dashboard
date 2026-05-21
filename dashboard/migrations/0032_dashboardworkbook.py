# Generated manually for DashboardWorkbook (Daily Tracker admin upload)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0031_alter_barrierchallenge_options_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="DashboardWorkbook",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(blank=True, help_text="Optional label in Admin only.", max_length=200, verbose_name="Title (optional)")),
                (
                    "file",
                    models.FileField(
                        help_text='Must include a sheet named "Daily Tracker" with a Picker Name row and date columns.',
                        upload_to="dashboard_workbooks/%Y/%m/",
                        verbose_name="Workbook (.xlsx / .xlsm)",
                    ),
                ),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Only one active record is used. When active, visitors see this data unless they upload another file in the same browser session (Zone Dispatch tab).",
                        verbose_name="Active",
                    ),
                ),
                (
                    "parsed_snapshot",
                    models.JSONField(
                        blank=True,
                        editable=False,
                        help_text="Filled when the file is saved if the Daily Tracker sheet is valid.",
                        null=True,
                        verbose_name="Parsed Daily Tracker (auto)",
                    ),
                ),
            ],
            options={
                "verbose_name": "[Tab 4 — Daily Tracker] Workbook upload",
                "verbose_name_plural": "[Tab 4 — Daily Tracker] Workbook uploads",
                "ordering": ("-uploaded_at",),
            },
        ),
    ]
