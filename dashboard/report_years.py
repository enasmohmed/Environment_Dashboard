"""Report year configuration for multi-year ESG dashboard."""

from __future__ import annotations

from .models import ReportYear

_FALLBACK_YEARS = (2025, 2026)
WORKBOOK_NAME_PREFIX = "Environment-Tamer-Logistics"


def expected_workbook_filename(year: int, *, ext: str = ".xlsx") -> str:
    """Canonical upload name, e.g. Environment-Tamer-Logistics-2026.xlsx."""
    return f"{WORKBOOK_NAME_PREFIX}-{year}{ext}"


def is_expected_workbook_filename(filename: str, year: int) -> bool:
    """True if the uploaded basename matches Environment-Tamer-Logistics-{year}.xlsx|.xlsm."""
    if not filename:
        return False
    base = filename.rsplit("/", 1)[-1].strip().lower()
    for ext in (".xlsx", ".xlsm"):
        if base == expected_workbook_filename(year, ext=ext).lower():
            return True
    return False


def ensure_default_report_years() -> None:
    """Create default years if the table is empty."""
    if ReportYear.objects.exists():
        return
    for i, year in enumerate(_FALLBACK_YEARS):
        ReportYear.objects.create(
            year=year,
            label=str(year),
            is_visible=True,
            sort_order=100 - i,
        )


def configured_years(*, visible_only: bool = False) -> list[int]:
    ensure_default_report_years()
    qs = ReportYear.objects.all()
    if visible_only:
        qs = qs.filter(is_visible=True)
    return list(qs.order_by("-sort_order", "-year").values_list("year", flat=True))


def default_report_year() -> int:
    years = configured_years(visible_only=True)
    return years[0] if years else _FALLBACK_YEARS[0]


def year_exists(year: int, *, allow_hidden: bool = True) -> bool:
    ensure_default_report_years()
    qs = ReportYear.objects.filter(year=year)
    if not allow_hidden:
        qs = qs.filter(is_visible=True)
    return qs.exists()


def years_for_api() -> list[dict]:
    ensure_default_report_years()
    return [
        {
            "year": row.year,
            "label": row.label or str(row.year),
            "is_visible": row.is_visible,
        }
        for row in ReportYear.objects.order_by("-sort_order", "-year")
    ]
