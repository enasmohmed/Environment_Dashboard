# Rename fields to match UI: dashboard title, banner, card title/text.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0022_remove_legacy_models"),
    ]

    operations = [
        migrations.RenameField(
            model_name="productivitydashboard",
            old_name="title",
            new_name="dashboard_title",
        ),
        migrations.RenameField(
            model_name="productivitydashboard",
            old_name="description",
            new_name="intro_text",
        ),
        migrations.RenameField(
            model_name="productivitydashboard",
            old_name="highlight_title",
            new_name="banner_title",
        ),
        migrations.RenameField(
            model_name="productivitydashboard",
            old_name="highlight_description",
            new_name="banner_text",
        ),
        migrations.RenameField(
            model_name="productivitydashboard",
            old_name="highlight_value",
            new_name="banner_value",
        ),
        migrations.RenameField(
            model_name="productivitydashboardcard",
            old_name="title",
            new_name="card_title",
        ),
        migrations.RenameField(
            model_name="productivitydashboardcard",
            old_name="body",
            new_name="card_text",
        ),
    ]
