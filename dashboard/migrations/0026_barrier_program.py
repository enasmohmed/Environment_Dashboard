# Barrier program (identified challenges) + challenges

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0025_pickingmethodphase_theme_colors"),
    ]

    operations = [
        migrations.CreateModel(
            name="BarrierProgram",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "module_number",
                    models.CharField(
                        default="03",
                        help_text="Large number on the left (e.g. 03).",
                        max_length=16,
                        verbose_name="Module number",
                    ),
                ),
                (
                    "module_keyword",
                    models.CharField(
                        default="BARRIERS",
                        help_text="Small label (e.g. BARRIERS).",
                        max_length=32,
                        verbose_name="Keyword",
                    ),
                ),
                (
                    "section_title",
                    models.CharField(
                        default="IDENTIFIED CHALLENGES",
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
                "verbose_name": "Barrier program",
                "verbose_name_plural": "Barrier programs",
                "ordering": ("-updated_at",),
            },
        ),
        migrations.CreateModel(
            name="BarrierChallenge",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                (
                    "title",
                    models.CharField(
                        help_text='Shown with a warning icon (e.g. "Truck Arrival — Unknown Timing"). You may include ⚠ in the text.',
                        max_length=255,
                        verbose_name="Challenge title",
                    ),
                ),
                (
                    "problem_description",
                    models.TextField(help_text="Describe the issue.", verbose_name="Problem details"),
                ),
                (
                    "mitigation_text",
                    models.TextField(
                        blank=True,
                        help_text="How you plan to fix it. Leave empty to show the placeholder text instead.",
                        verbose_name="Mitigation (solution)",
                    ),
                ),
                (
                    "mitigation_placeholder",
                    models.CharField(
                        blank=True,
                        help_text="If mitigation is empty, this shows (default: generic “coming soon” message if you leave this blank too).",
                        max_length=255,
                        verbose_name="Placeholder when no mitigation",
                    ),
                ),
                (
                    "impact",
                    models.CharField(
                        choices=[
                            ("high", "High impact"),
                            ("medium", "Medium impact"),
                            ("low", "Low impact"),
                        ],
                        default="high",
                        max_length=16,
                        verbose_name="Impact level",
                    ),
                ),
                (
                    "program",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="challenges",
                        to="dashboard.barrierprogram",
                    ),
                ),
            ],
            options={
                "verbose_name": "Barrier challenge",
                "verbose_name_plural": "Barrier challenges",
                "ordering": ("sort_order", "id"),
            },
        ),
    ]
