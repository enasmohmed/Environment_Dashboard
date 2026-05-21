# Picking method program (phase 02 style) + phases, tags, summary cards

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0023_rename_productivity_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="PickingMethodProgram",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "module_number",
                    models.CharField(
                        default="02",
                        help_text="Large number on the left (e.g. 02).",
                        max_length=16,
                        verbose_name="Phase number",
                    ),
                ),
                (
                    "module_keyword",
                    models.CharField(
                        default="PHASE",
                        help_text="Small caps word after the number (e.g. PHASE).",
                        max_length=32,
                        verbose_name="Keyword",
                    ),
                ),
                (
                    "section_title",
                    models.CharField(
                        default="PICKING METHOD – 3-WEEK TEST",
                        help_text="Bold headline after the keyword.",
                        max_length=255,
                        verbose_name="Section title",
                    ),
                ),
                (
                    "intro_text",
                    models.TextField(
                        blank=True,
                        help_text="Text under the header (e.g. three zone structures…).",
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
                "verbose_name": "Picking method program",
                "verbose_name_plural": "Picking method programs",
                "ordering": ("-updated_at",),
            },
        ),
        migrations.CreateModel(
            name="PickingMethodPhase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                (
                    "week_label",
                    models.CharField(help_text="e.g. WEEK 1", max_length=64, verbose_name="Week label"),
                ),
                (
                    "theme",
                    models.CharField(
                        choices=[
                            ("red", "Red (week 1 style)"),
                            ("orange", "Orange (week 2 style)"),
                            ("green", "Green (week 3 style)"),
                        ],
                        default="red",
                        max_length=16,
                        verbose_name="Accent color",
                    ),
                ),
                (
                    "main_title",
                    models.CharField(help_text="e.g. BY ROOM", max_length=255, verbose_name="Main title"),
                ),
                (
                    "test_badge",
                    models.CharField(
                        blank=True,
                        help_text="e.g. TEST A",
                        max_length=64,
                        verbose_name="Test badge",
                    ),
                ),
                ("description", models.TextField(help_text="Paragraph for this week.", verbose_name="Description")),
                (
                    "program",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="phases",
                        to="dashboard.pickingmethodprogram",
                    ),
                ),
            ],
            options={
                "verbose_name": "Picking method phase (week)",
                "verbose_name_plural": "Picking method phases",
                "ordering": ("sort_order", "id"),
            },
        ),
        migrations.CreateModel(
            name="PickingMethodPhaseTag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("label", models.CharField(max_length=128)),
                (
                    "phase",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tags",
                        to="dashboard.pickingmethodphase",
                    ),
                ),
            ],
            options={
                "verbose_name": "Phase tag",
                "verbose_name_plural": "Phase tags",
                "ordering": ("sort_order", "id"),
            },
        ),
        migrations.CreateModel(
            name="PickingMethodSummaryCard",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                (
                    "display_value",
                    models.CharField(
                        help_text="Large text or symbol (e.g. 3, 1W, →1, ∞).",
                        max_length=32,
                        verbose_name="Display value",
                    ),
                ),
                (
                    "label",
                    models.CharField(
                        help_text="e.g. METHODS TESTED",
                        max_length=128,
                        verbose_name="Label",
                    ),
                ),
                (
                    "program",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="summary_cards",
                        to="dashboard.pickingmethodprogram",
                    ),
                ),
            ],
            options={
                "verbose_name": "Picking method summary card",
                "verbose_name_plural": "Picking method summary cards",
                "ordering": ("sort_order", "id"),
            },
        ),
    ]
