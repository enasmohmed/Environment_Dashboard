# Process improvements (module 05) + stacked items

import django.db.models.deletion
from django.db import migrations, models


_SURFACE_CHOICES = [
    ("dark", "Dark (black)"),
    ("blue", "Blue"),
    ("indigo", "Indigo"),
    ("teal", "Teal"),
    ("slate", "Slate"),
    ("stone", "Stone"),
    ("emerald", "Emerald"),
    ("violet", "Violet"),
    ("orange", "Orange"),
    ("rose", "Rose"),
]


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0027_rollout_program"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProcessImprovementProgram",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "module_number",
                    models.CharField(
                        default="05",
                        help_text="Large number on the left (e.g. 05).",
                        max_length=16,
                        verbose_name="Module number",
                    ),
                ),
                (
                    "module_keyword",
                    models.CharField(
                        default="ENHANCEMENTS",
                        help_text="Small uppercase line (e.g. ENHANCEMENTS).",
                        max_length=32,
                        verbose_name="Keyword",
                    ),
                ),
                (
                    "section_title",
                    models.CharField(
                        default="PROCESS IMPROVEMENTS",
                        help_text="Main headline after the keyword.",
                        max_length=255,
                        verbose_name="Section title",
                    ),
                ),
                ("intro_text", models.TextField(blank=True, verbose_name="Intro (optional)")),
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
                "verbose_name": "Process improvement program",
                "verbose_name_plural": "Process improvement programs",
                "ordering": ("-updated_at",),
            },
        ),
        migrations.CreateModel(
            name="ProcessImprovementItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                (
                    "surface",
                    models.CharField(
                        choices=_SURFACE_CHOICES,
                        default="dark",
                        help_text="Dark = black card like improvement 01; colored surfaces for emphasis.",
                        max_length=16,
                        verbose_name="Card background",
                    ),
                ),
                (
                    "improvement_label",
                    models.CharField(
                        default="IMPROVEMENT 01",
                        help_text='First part of the meta line (e.g. "IMPROVEMENT 01").',
                        max_length=64,
                        verbose_name="Improvement label",
                    ),
                ),
                (
                    "category_label",
                    models.CharField(
                        blank=True,
                        help_text='Second part after the middle dot (e.g. "SMALL ACCOUNTS"). Leave empty to hide the dot.',
                        max_length=128,
                        verbose_name="Category tag",
                    ),
                ),
                (
                    "card_title",
                    models.CharField(
                        help_text="Bold white headline on the card.",
                        max_length=255,
                        verbose_name="Main title",
                    ),
                ),
                (
                    "body_text",
                    models.TextField(help_text="Supporting paragraph on the card.", verbose_name="Body text"),
                ),
                (
                    "program",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="dashboard.processimprovementprogram",
                    ),
                ),
            ],
            options={
                "verbose_name": "Process improvement item",
                "verbose_name_plural": "Process improvement items",
                "ordering": ("sort_order", "id"),
            },
        ),
    ]
