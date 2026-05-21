# Rollout implementation plan (module 04) + plan cards

import django.db.models.deletion
from django.db import migrations, models


_ACCENT_CHOICES = [
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
]

_ICON_CHOICES = [
    ("grid_bays", "Numbered grid (1–4)"),
    ("monitor", "Screen / monitor"),
    ("smartphone", "Smartphone"),
    ("warehouse", "Warehouse"),
    ("truck", "Truck"),
    ("checklist", "Checklist"),
    ("custom", "Uploaded image"),
]


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0026_barrier_program"),
    ]

    operations = [
        migrations.CreateModel(
            name="RolloutProgram",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "module_number",
                    models.CharField(
                        default="04",
                        help_text="Large number on the left (e.g. 04).",
                        max_length=16,
                        verbose_name="Module number",
                    ),
                ),
                (
                    "module_keyword",
                    models.CharField(
                        default="ROLLOUT",
                        help_text="Small label (e.g. ROLLOUT).",
                        max_length=32,
                        verbose_name="Keyword",
                    ),
                ),
                (
                    "section_title",
                    models.CharField(
                        default="IMPLEMENTATION PLAN",
                        help_text="Main headline after the keyword.",
                        max_length=255,
                        verbose_name="Section title",
                    ),
                ),
                (
                    "intro_text",
                    models.TextField(
                        blank=True,
                        help_text="Text under the main title (e.g. conditional rollout explanation).",
                        verbose_name="Intro paragraph",
                    ),
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
                "verbose_name": "Rollout program",
                "verbose_name_plural": "Rollout programs",
                "ordering": ("-updated_at",),
            },
        ),
        migrations.CreateModel(
            name="RolloutPlanCard",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                (
                    "accent_theme",
                    models.CharField(
                        choices=_ACCENT_CHOICES,
                        default="blue",
                        help_text="Top border color on the card.",
                        max_length=24,
                        verbose_name="Accent color",
                    ),
                ),
                (
                    "icon_kind",
                    models.CharField(
                        choices=_ICON_CHOICES,
                        default="grid_bays",
                        max_length=24,
                        verbose_name="Icon",
                    ),
                ),
                (
                    "icon_image",
                    models.ImageField(
                        blank=True,
                        help_text="When icon is “Uploaded image”.",
                        null=True,
                        upload_to="rollout/card_icons/",
                        verbose_name="Custom icon",
                    ),
                ),
                ("card_title", models.CharField(max_length=255, verbose_name="Card title")),
                ("card_description", models.TextField(verbose_name="Card description")),
                (
                    "program",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="plan_cards",
                        to="dashboard.rolloutprogram",
                    ),
                ),
            ],
            options={
                "verbose_name": "Rollout plan card",
                "verbose_name_plural": "Rollout plan cards",
                "ordering": ("sort_order", "id"),
            },
        ),
    ]
