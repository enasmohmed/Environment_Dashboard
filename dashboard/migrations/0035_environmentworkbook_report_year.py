from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0034_environment_workbook"),
    ]

    operations = [
        migrations.AddField(
            model_name="environmentworkbook",
            name="report_year",
            field=models.PositiveIntegerField(
                default=2025,
                help_text="Reporting year for this workbook (e.g. 2025 or 2026). One active file per year.",
                verbose_name="Report year",
            ),
        ),
    ]
