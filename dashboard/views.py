import logging

from django.conf import settings
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from .environment_parse import parse_environment_workbook
from .models import EnvironmentWorkbook
from .report_years import (
    configured_years,
    default_report_year,
    expected_workbook_filename,
    is_expected_workbook_filename,
    year_exists,
    years_for_api,
)

logger = logging.getLogger(__name__)

SESSION_ENV_SELECTED_YEAR = "environment_selected_year"
SESSION_ENV_VIEW_MODE = "environment_view_mode"
SESSION_ENV_COMPARE_YEARS = "environment_compare_years"


@method_decorator(ensure_csrf_cookie, name="dispatch")
class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["dashboard_title"] = "Tamer Logistics ESG"
        ctx["default_year"] = default_report_year()
        return ctx


def _parse_year_value(value, *, visible_only: bool = False) -> int | None:
    if value is None or value == "":
        return None
    try:
        year = int(value)
    except (TypeError, ValueError):
        return None
    if not year_exists(year, allow_hidden=not visible_only):
        return None
    if visible_only and year not in configured_years(visible_only=True):
        return None
    return year


def _parse_years_csv(value) -> list[int]:
    if not value:
        return []
    out: list[int] = []
    for part in str(value).split(","):
        y = _parse_year_value(part.strip(), visible_only=True)
        if y is not None and y not in out:
            out.append(y)
    return out


def _save_view_preferences(
    request,
    selected_year: int,
    *,
    view_mode: str | None = None,
    compare_years: list[int] | None = None,
) -> None:
    request.session[SESSION_ENV_SELECTED_YEAR] = selected_year
    if view_mode is not None:
        request.session[SESSION_ENV_VIEW_MODE] = view_mode
    if compare_years is not None:
        request.session[SESSION_ENV_COMPARE_YEARS] = compare_years
    request.session.modified = True


def _workbooks_by_year() -> dict[int, tuple[dict, str]]:
    """Active parsed workbooks per report year (database — shared for all visitors)."""
    out: dict[int, tuple[dict, str]] = {}
    for year in configured_years(visible_only=False):
        wb = (
            EnvironmentWorkbook.objects.filter(is_active=True, report_year=year)
            .exclude(parsed_snapshot__isnull=True)
            .order_by("-uploaded_at")
            .first()
        )
        if wb and wb.parsed_snapshot:
            name = wb.file.name.rsplit("/", 1)[-1] if wb.file else f"ESG {year}"
            out[year] = (wb.parsed_snapshot, name)
    return out


def _persist_workbook(
    year: int, filename: str, raw: bytes, parsed: dict
) -> EnvironmentWorkbook:
    """Save upload to DB so every visitor sees the same dashboard data."""
    EnvironmentWorkbook.objects.filter(report_year=year).update(is_active=False)
    wb = EnvironmentWorkbook(
        report_year=year,
        is_active=True,
        parsed_snapshot=parsed,
    )
    wb.file.save(filename, ContentFile(raw), save=True)
    EnvironmentWorkbook.objects.filter(report_year=year, is_active=True).exclude(
        pk=wb.pk
    ).update(is_active=False)
    return wb


def _delete_workbook_for_year(year: int) -> bool:
    """Remove active workbook for a year (public clear or replace on re-upload)."""
    deleted = False
    for wb in EnvironmentWorkbook.objects.filter(report_year=year, is_active=True):
        if wb.file:
            wb.file.delete(save=False)
        wb.delete()
        deleted = True
    return deleted


def _resolve_year_data(
    db_map: dict[int, tuple[dict, str]], year: int
) -> tuple[dict | None, str | None, str | None]:
    entry = db_map.get(year)
    if entry:
        return entry[0], entry[1], "server"
    return None, None, None


def _build_years_meta(db_map: dict[int, tuple[dict, str]]) -> list[dict]:
    years_meta = []
    for cfg in years_for_api():
        year = cfg["year"]
        if not cfg["is_visible"]:
            continue
        data, file_name, source = _resolve_year_data(db_map, year)
        years_meta.append(
            {
                "year": year,
                "label": cfg.get("label") or str(year),
                "has_data": data is not None,
                "file_name": file_name,
                "source": source,
                "is_visible": True,
                "expected_workbook": expected_workbook_filename(year),
            }
        )
    return years_meta


def _pick_selected_year(request, explicit: int | None = None) -> int:
    if explicit is not None:
        return explicit
    stored = _parse_year_value(
        request.session.get(SESSION_ENV_SELECTED_YEAR), visible_only=True
    )
    if stored is not None:
        return stored
    db_map = _workbooks_by_year()
    for year in configured_years(visible_only=True):
        if year in db_map:
            return year
    return default_report_year()


def _build_years_response(
    request,
    selected_year: int,
    *,
    mode: str = "single",
    compare_years: list[int] | None = None,
) -> dict:
    db_map = _workbooks_by_year()
    years_meta = _build_years_meta(db_map)

    data, file_name, source = _resolve_year_data(db_map, selected_year)

    payload: dict = {
        "ok": True,
        "mode": mode,
        "years": years_meta,
        "configured_years": years_for_api(),
        "visible_years": configured_years(visible_only=True),
        "selected_year": selected_year,
        "expected_workbook": expected_workbook_filename(selected_year),
        "data": data,
        "file_name": file_name,
        "source": source,
    }

    if mode == "compare" and compare_years:
        datasets: dict[str, dict] = {}
        for year in compare_years:
            ydata, yname, ysrc = _resolve_year_data(db_map, year)
            if ydata:
                datasets[str(year)] = {
                    "data": ydata,
                    "file_name": yname,
                    "source": ysrc,
                }
        payload["compare_years"] = compare_years
        payload["datasets"] = datasets
        if datasets:
            first = str(compare_years[0])
            if first in datasets:
                payload["data"] = datasets[first]["data"]
                payload["file_name"] = datasets[first].get("file_name")
                payload["source"] = datasets[first].get("source")

    return payload


@csrf_exempt
@require_http_methods(["GET", "POST", "DELETE"])
def environment_api(request):
    """
    GET:
      ?year=2025 — single-year view (data from database)
      ?mode=compare&years=2025,2026 — multi-year comparison
    POST: file + year — parse, save file + JSON snapshot to database
    DELETE: ?year=2025 — remove saved workbook for that year
    """
    if request.method == "DELETE":
        year = _parse_year_value(request.GET.get("year"), visible_only=False)
        view_mode = request.session.get(SESSION_ENV_VIEW_MODE) or "single"
        compare_years = list(request.session.get(SESSION_ENV_COMPARE_YEARS) or [])

        if year is not None:
            _delete_workbook_for_year(year)
            if year in compare_years:
                compare_years = [y for y in compare_years if y != year]
            selected = _pick_selected_year(request)
            if selected == year:
                db_map = _workbooks_by_year()
                selected = default_report_year()
                for y in configured_years(visible_only=True):
                    if y in db_map:
                        selected = y
                        break
            _save_view_preferences(
                request,
                selected,
                view_mode=view_mode,
                compare_years=compare_years,
            )
        else:
            for y in configured_years(visible_only=False):
                _delete_workbook_for_year(y)
            request.session.pop(SESSION_ENV_SELECTED_YEAR, None)
            request.session.pop(SESSION_ENV_VIEW_MODE, None)
            request.session.pop(SESSION_ENV_COMPARE_YEARS, None)
            request.session.modified = True
            selected = default_report_year()
            view_mode = "single"
            compare_years = []

        if view_mode == "compare" and len(compare_years) >= 2:
            return JsonResponse(
                _build_years_response(
                    request, selected, mode="compare", compare_years=compare_years
                )
            )
        return JsonResponse(_build_years_response(request, selected))

    if request.method == "GET":
        mode = (request.GET.get("mode") or "").strip().lower()
        compare_years = _parse_years_csv(request.GET.get("years"))
        year_param = request.GET.get("year")

        if mode == "compare" and len(compare_years) >= 2:
            selected = compare_years[0]
            _save_view_preferences(
                request,
                selected,
                view_mode="compare",
                compare_years=compare_years,
            )
            return JsonResponse(
                _build_years_response(
                    request, selected, mode="compare", compare_years=compare_years
                )
            )

        if year_param not in (None, ""):
            year = _pick_selected_year(
                request, _parse_year_value(year_param, visible_only=True)
            )
            _save_view_preferences(
                request, year, view_mode="single", compare_years=[]
            )
            return JsonResponse(_build_years_response(request, year, mode="single"))

        view_mode = request.session.get(SESSION_ENV_VIEW_MODE) or "single"
        compare_stored = list(request.session.get(SESSION_ENV_COMPARE_YEARS) or [])
        if view_mode == "compare" and len(compare_stored) >= 2:
            selected = compare_stored[0]
            return JsonResponse(
                _build_years_response(
                    request, selected, mode="compare", compare_years=compare_stored
                )
            )

        year = _pick_selected_year(request)
        _save_view_preferences(request, year, view_mode="single", compare_years=[])
        return JsonResponse(_build_years_response(request, year, mode="single"))

    f = request.FILES.get("file")
    if not f:
        return JsonResponse(
            {"ok": False, "error": "Missing file field (expected name: file)."},
            status=400,
        )

    year = _parse_year_value(
        request.POST.get("year") or request.GET.get("year"), visible_only=False
    )
    if year is None:
        visible = ", ".join(str(y) for y in configured_years(visible_only=False))
        return JsonResponse(
            {
                "ok": False,
                "error": f"Missing or invalid year. Add the year in Admin → Report years first. Configured: {visible or 'none'}.",
            },
            status=400,
        )

    fname = f.name or ""
    lower = fname.lower()
    if not lower.endswith((".xlsx", ".xlsm")):
        return JsonResponse(
            {"ok": False, "error": "Only .xlsx and .xlsm workbooks are supported."},
            status=400,
        )
    if not is_expected_workbook_filename(fname, year):
        expected = expected_workbook_filename(year)
        return JsonResponse(
            {
                "ok": False,
                "error": f"Rename the file to {expected} (or .xlsm) for report year {year}.",
            },
            status=400,
        )

    try:
        raw = f.read()
        if len(raw) > 25 * 1024 * 1024:
            return JsonResponse(
                {"ok": False, "error": "File is too large (max 25 MB)."},
                status=400,
            )
        data = parse_environment_workbook(raw, report_year=year)
        _persist_workbook(year, fname, raw, data)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)
    except Exception as exc:
        logger.exception("environment workbook parse failed")
        return JsonResponse(
            {
                "ok": False,
                "error": "Could not read that Excel file. It may be corrupt or password-protected.",
                "detail": str(exc) if settings.DEBUG else None,
            },
            status=400,
        )

    view_mode = request.session.get(SESSION_ENV_VIEW_MODE) or "single"
    compare_years = list(request.session.get(SESSION_ENV_COMPARE_YEARS) or [])
    if year not in compare_years and view_mode == "compare":
        compare_years.append(year)
        compare_years.sort(reverse=True)
    _save_view_preferences(
        request,
        year,
        view_mode=view_mode,
        compare_years=compare_years if view_mode == "compare" else [],
    )

    if view_mode == "compare" and len(compare_years) >= 2:
        return JsonResponse(
            _build_years_response(
                request, compare_years[0], mode="compare", compare_years=compare_years
            )
        )
    return JsonResponse(_build_years_response(request, year, mode="single"))
