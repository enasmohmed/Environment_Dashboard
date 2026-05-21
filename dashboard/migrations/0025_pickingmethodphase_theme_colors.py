# Wider theme field + extended accent colors for PickingMethodPhase

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0024_picking_method_program"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pickingmethodphase",
            name="theme",
            field=models.CharField(
                choices=[
                    ("red", "Red"),
                    ("orange", "Orange"),
                    ("amber", "Amber"),
                    ("yellow", "Yellow"),
                    ("lime", "Lime"),
                    ("green", "Green"),
                    ("emerald", "Emerald"),
                    ("teal", "Teal"),
                    ("cyan", "Cyan"),
                    ("sky", "Sky"),
                    ("blue", "Blue"),
                    ("indigo", "Indigo"),
                    ("violet", "Violet"),
                    ("purple", "Purple"),
                    ("fuchsia", "Fuchsia"),
                    ("pink", "Pink"),
                    ("rose", "Rose"),
                    ("slate", "Slate"),
                    ("stone", "Stone"),
                    ("zinc", "Zinc"),
                    ("neutral", "Neutral gray"),
                ],
                default="red",
                help_text="Left border and dot color — pick a different color for each extra week.",
                max_length=24,
                verbose_name="Accent color",
            ),
        ),
    ]
