"""
Parse Environment-Tamer-Logistics-{year}.xlsx into dashboard JSON.

Each workbook sheet maps to a dashboard tab. Overview KPIs and charts are
aggregated from the parsed sections.
"""

from __future__ import annotations

import io
import re
from typing import Any

import pandas as pd

MONTHS = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
MONTH_LABELS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)

SHEET_ELECTRICITY = "1. Electricty "
SHEET_ENERGY = "2. Energy"
SHEET_TRANSPORTATION = "3. Transportation"
SHEET_WATER_LITERS = "4. Water - LITERS"
SHEET_WATER_COST = "4. Water - COST"
SHEET_WASTE = "5. Waste"
SHEET_FUGITIVE = "6. Fugitive gases "
SHEET_GOVERNANCE = "Data Governance"

_YEAR_RE = re.compile(r"\b(20\d{2})\b")


def _norm(cell: Any) -> str:
    if cell is None:
        return ""
    if isinstance(cell, float):
        if pd.isna(cell):
            return ""
        if cell == int(cell):
            return str(int(cell))
    if isinstance(cell, bool):
        return str(cell)
    return str(cell).strip()


def _parse_number(cell: Any) -> float | None:
    if cell is None or cell == "":
        return None
    if isinstance(cell, bool):
        return None
    if isinstance(cell, float) and pd.isna(cell):
        return None
    if isinstance(cell, (int, float)):
        return float(cell)
    s = str(cell).strip()
    if s in ("-", "—", "–", "N/A", "n/a"):
        return None
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


def _infer_year(text: str) -> int:
    m = _YEAR_RE.search(text or "")
    return int(m.group(1)) if m else 2025


def _month_columns(header_row: list[Any]) -> dict[str, int]:
    out: dict[str, int] = {}
    for j, h in enumerate(header_row):
        key = _norm(h).upper()
        if key in MONTHS:
            out[key] = j
    return out


def _empty_months() -> dict[str, float]:
    return {m: 0.0 for m in MONTHS}


def _sum_months(month_cols: dict[str, int], row: list[Any]) -> dict[str, float]:
    totals = _empty_months()
    for m, j in month_cols.items():
        if j < len(row):
            v = _parse_number(row[j])
            if v is not None:
                totals[m] += v
    return totals


def _merge_month_dict(a: dict[str, float], b: dict[str, float]) -> dict[str, float]:
    return {m: a.get(m, 0.0) + b.get(m, 0.0) for m in MONTHS}


def _month_series(totals: dict[str, float]) -> list[dict[str, Any]]:
    return [
        {
            "month": MONTH_LABELS[i],
            "key": MONTHS[i],
            "value": int(round(totals.get(MONTHS[i], 0.0))),
        }
        for i in range(12)
    ]


def _format_kpi(n: float) -> str:
    """Compact integer display: 32M, 2M, 35K, 2,127 — no decimals."""
    if n is None or (isinstance(n, float) and pd.isna(n)):
        return "—"
    n = float(n)
    if abs(n) >= 1_000_000:
        return f"{int(round(n / 1_000_000))}M"
    if abs(n) >= 10_000:
        return f"{int(round(n / 1_000))}K"
    return f"{int(round(n)):,}"


def _format_kpi_electricity(n: float) -> str:
    """Electricity tab KPIs: 32.1M, 1.63M, 597K (matches report design)."""
    if n is None or (isinstance(n, float) and pd.isna(n)):
        return "—"
    n = float(n)
    if abs(n) >= 1_000_000:
        m = n / 1_000_000
        if m >= 10:
            s = f"{m:.1f}".rstrip("0").rstrip(".")
            return f"{s}M"
        s = f"{m:.2f}".rstrip("0").rstrip(".")
        return f"{s}M"
    if abs(n) >= 1_000:
        return f"{int(round(n / 1_000))}K"
    return f"{int(round(n)):,}"


def _section_stop(cell_b: Any) -> bool:
    t = _norm(cell_b)
    if not t:
        return False
    upper = t.upper()
    if "FACILITY TYPE" in upper:
        return True
    markers = (
        "ELECTRICTY",
        "ENERGY FROM",
        "WATER ",
        "WASTE ",
        "DRINKING",
        "HAZARDOUS",
        "RECYCLING",
        "COST AND REVENUE",
        "POWER GENERATION",
        "POWER CONSUMPTION",
        "ADD OR REMOVE",
        "SOLAR ENERGY",
    )
    return any(m in upper for m in markers)


def _parse_facility_sections(df: pd.DataFrame) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    i = 0
    n = len(df)
    while i < n:
        row = df.iloc[i].tolist()
        title = _norm(row[1]) if len(row) > 1 else ""
        if title and "FACILITY TYPE" in title.upper():
            i += 1
            continue
        title_upper = title.upper()
        if title and (
            "MONTHLY DATA" in title_upper
            or "MONTLY DATA" in title_upper
            or "MONTHLY" in title_upper
            or "MONTLY" in title_upper
            or title_upper.startswith("POWER ")
            or ("2025" in title_upper and any(w in title_upper for w in ("KWH", "LITERS", "LITER", "KG", "GAS")))
        ):
            section_title = title
            header_row_idx = i + 1
            if header_row_idx >= n:
                break
            header = df.iloc[header_row_idx].tolist()
            if "FACILITY TYPE" not in _norm(header[1]).upper():
                i += 1
                continue
            month_cols = _month_columns(header)
            meta_cols = [
                {"key": "facility_type", "label": "Facility Type", "index": 1},
                {"key": "location", "label": "Location", "index": 2},
                {"key": "facility_name", "label": "Facility Name", "index": 3},
            ]
            extra_start = 4
            while extra_start < min(month_cols.values()) if month_cols else 4:
                label = _norm(header[extra_start])
                if label and label.upper() not in MONTHS:
                    meta_cols.append(
                        {"key": f"col_{extra_start}", "label": label, "index": extra_start}
                    )
                extra_start += 1

            rows: list[dict[str, Any]] = []
            monthly_totals = _empty_months()
            j = header_row_idx + 1
            while j < n:
                data_row = df.iloc[j].tolist()
                name = _norm(data_row[3]) if len(data_row) > 3 else ""
                cell_b = data_row[1] if len(data_row) > 1 else None
                if _section_stop(cell_b) and not name:
                    break
                if not name:
                    j += 1
                    continue
                record: dict[str, Any] = {}
                for col in meta_cols:
                    idx = col["index"]
                    record[col["key"]] = _norm(data_row[idx]) if idx < len(data_row) else ""
                months: dict[str, float | None] = {}
                row_months = _sum_months(month_cols, data_row)
                for m in MONTHS:
                    v = row_months[m]
                    months[m] = v if v else None
                record["months"] = months
                rows.append(record)
                monthly_totals = _merge_month_dict(monthly_totals, row_months)
                j += 1

            sections.append(
                {
                    "title": section_title,
                    "columns": meta_cols,
                    "rows": rows,
                    "monthly_totals": monthly_totals,
                    "annual_total": sum(monthly_totals.values()),
                    "facility_count": len(rows),
                    "monthly_series": _month_series(monthly_totals),
                }
            )
            i = j
            continue
        i += 1
    return sections


def _parse_electricity_row(df: pd.DataFrame, excel_row: int) -> dict[str, Any] | None:
    """Read one facility row (Excel 1-based row number). Cols B–Q."""
    idx = excel_row - 1
    if idx < 0 or idx >= len(df):
        return None
    row = df.iloc[idx]
    name = _norm(row.iloc[3]) if len(row) > 3 else ""
    if not name or name.upper() == "FACILITY NAME":
        return None
    months: dict[str, float | None] = {}
    for j, m in enumerate(MONTHS):
        col = 4 + j
        months[m] = _parse_number(row.iloc[col]) if col < len(row) else None
    total = _parse_number(row.iloc[16]) if len(row) > 16 else None
    if total is None:
        total = sum(v or 0 for v in months.values()) or None
    return {
        "excel_row": excel_row,
        "facility_type": _norm(row.iloc[1]) if len(row) > 1 else "",
        "location": _norm(row.iloc[2]) if len(row) > 2 else "",
        "facility_name": name,
        "months": months,
        "total": total,
    }


def _parse_electricity_sheet(df: pd.DataFrame) -> dict[str, Any]:
    """
    Sheet 1. Electricty — fixed Excel ranges (Overview uses separate formulas).

    Grid facilities: rows 11–31 (21 sites; row 10 = header).
    Grand total: row 33 (monthly sums in E–P).
    Solar generation: rows 40–41; consumption: rows 47–48.
    """
    # Grid rows 11–31 (user doc 10–30 maps to data after header on row 10)
    grid_rows: list[dict[str, Any]] = []
    for excel_row in range(11, 32):
        rec = _parse_electricity_row(df, excel_row)
        if rec:
            grid_rows.append(rec)

    grid_monthly = _empty_months()
    for col_letter in _OVERVIEW_MONTH_COLS:
        mi = _OVERVIEW_MONTH_COLS.index(col_letter)
        grid_monthly[MONTHS[mi]] = _sum_excel_range(df, col_letter, 11, 31)

    grand_total_row: dict[str, Any] | None = None
    gt_idx = 32  # Excel row 33
    if gt_idx < len(df):
        gt_months: dict[str, float | None] = {}
        for j, m in enumerate(MONTHS):
            gt_months[m] = _parse_number(df.iloc[gt_idx, 4 + j])
        grand_total_row = {
            "label": "Grand Total",
            "months": gt_months,
            "total": _parse_number(df.iloc[gt_idx, 16]) if len(df.iloc[gt_idx]) > 16 else None,
        }

    stacked_datasets = [
        {
            "label": r["facility_name"],
            "data": [int(r["months"].get(m) or 0) for m in MONTHS],
        }
        for r in grid_rows
    ]

    solar_gen_rows: list[dict[str, Any]] = []
    for excel_row in (40, 41):
        rec = _parse_electricity_row(df, excel_row)
        if rec:
            solar_gen_rows.append(rec)

    solar_use_rows: list[dict[str, Any]] = []
    for excel_row in (47, 48):
        rec = _parse_electricity_row(df, excel_row)
        if rec:
            solar_use_rows.append(rec)

    def _row_sum(row: dict[str, Any]) -> float:
        return sum(v or 0 for v in row["months"].values())

    jed_3pl_gen = next((r for r in solar_gen_rows if "3PL" in r["facility_name"]), None)
    jed_hc_gen = next((r for r in solar_gen_rows if "HC" in r["facility_name"]), None)

    def _facility_total(row: dict[str, Any] | None) -> float:
        if not row:
            return 0.0
        if row.get("total") is not None:
            return float(row["total"])
        return _row_sum(row)

    kpis = [
        {
            "id": "total_grid",
            "label": "Total Grid KWH",
            "value": _format_kpi_electricity(sum(grid_monthly.values())),
            "sub": "All 21 Facilities",
            "icon": "⚡",
            "theme": "elec-yellow",
        },
        {
            "id": "solar_3pl",
            "label": "Solar Generated (KWH)",
            "value": _format_kpi_electricity(_facility_total(jed_3pl_gen)),
            "sub": "JED 3PL MDC",
            "icon": "☀️",
            "theme": "elec-orange",
        },
        {
            "id": "solar_hc",
            "label": "Solar Generated (KWH)",
            "value": _format_kpi_electricity(_facility_total(jed_hc_gen)),
            "sub": "JED HC MDC",
            "icon": "☀️",
            "theme": "elec-amber",
        },
        {
            "id": "facility_count",
            "label": "Grid Facilities",
            "value": str(len(grid_rows)),
            "sub": "Warehouses & Accommodation",
            "icon": "🏢",
            "theme": "elec-purple",
        },
    ]

    return {
        "year": 2025,
        "kpis": kpis,
        "grid_table": {
            "rows": grid_rows,
            "grand_total": grand_total_row,
            "monthly_totals": grid_monthly,
            "monthly_series": _month_series(grid_monthly),
        },
        "stacked_chart": {
            "labels": list(MONTH_LABELS),
            "datasets": stacked_datasets,
        },
        "solar_generation_table": {"rows": solar_gen_rows},
        "solar_consumption_table": {"rows": solar_use_rows},
        "solar_generation_monthly": _month_series(_solar_monthly_totals(solar_gen_rows)),
        "solar_consumption_monthly": _month_series(_solar_monthly_totals(solar_use_rows)),
        # Legacy keys (Overview tab)
        "grid": {
            "rows": grid_rows,
            "monthly_totals": grid_monthly,
            "monthly_series": _month_series(grid_monthly),
            "annual_total": sum(grid_monthly.values()),
            "facility_count": len(grid_rows),
        },
        "solar_generation": {
            "rows": solar_gen_rows,
            "monthly_totals": _solar_monthly_totals(solar_gen_rows),
            "monthly_series": _month_series(_solar_monthly_totals(solar_gen_rows)),
            "annual_total": sum(_solar_monthly_totals(solar_gen_rows).values()),
        },
        "solar_consumption": {
            "rows": solar_use_rows,
            "monthly_totals": _solar_monthly_totals(solar_use_rows),
            "monthly_series": _month_series(_solar_monthly_totals(solar_use_rows)),
            "annual_total": sum(_solar_monthly_totals(solar_use_rows).values()),
        },
    }


def _solar_monthly_totals(rows: list[dict[str, Any]]) -> dict[str, float]:
    totals = _empty_months()
    for row in rows:
        for m in MONTHS:
            v = row.get("months", {}).get(m)
            if v is not None:
                totals[m] += v
    return totals


def _parse_simple_sheet(df: pd.DataFrame) -> dict[str, Any]:
    sections = _parse_facility_sections(df)
    year = 2025
    for s in sections:
        year = _infer_year(s["title"])
        break
    return {"year": year, "sections": sections}


# Sheet 2. Energy — months in cols H→S (col F empty; do not use G for months)
_GENERATOR_MONTH_COLS = ("H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S")
_GENERATOR_DATA_ROWS = (11, 12, 13)  # Excel rows: JNJ, IKEA, RYD-3PL (user rows 10–12)


def _parse_generator_row(df: pd.DataFrame, excel_row: int) -> dict[str, Any] | None:
    """One generator row — cols B,C,D,E,G + H→S + T (Excel 1-based)."""
    idx = excel_row - 1
    if idx < 0 or idx >= len(df):
        return None
    row = df.iloc[idx]
    name = _norm(row.iloc[3]) if len(row) > 3 else ""
    if not name or name.upper() == "FACILITY NAME":
        return None
    months: dict[str, float | None] = {}
    for j, m in enumerate(MONTHS):
        col = 7 + j  # H = index 7
        months[m] = _parse_number(row.iloc[col]) if col < len(row) else None
    total = _parse_number(row.iloc[19]) if len(row) > 19 else None
    if total is None:
        total = sum(v or 0 for v in months.values()) or None
    return {
        "excel_row": excel_row,
        "facility_type": _norm(row.iloc[1]) if len(row) > 1 else "",
        "location": _norm(row.iloc[2]) if len(row) > 2 else "",
        "facility_name": name,
        "source_type": _norm(row.iloc[4]) if len(row) > 4 else "",
        "fuel_type": _norm(row.iloc[6]) if len(row) > 6 else "",
        "months": months,
        "total": total,
    }


def _generator_monthly_totals(rows: list[dict[str, Any]]) -> dict[str, float]:
    totals = _empty_months()
    for row in rows:
        for m in MONTHS:
            v = row.get("months", {}).get(m)
            if v is not None:
                totals[m] += v
    return totals


def _format_kpi_generators(n: float) -> str:
    """Generator KPIs: 342K, 234K, 105K, 3K."""
    if n is None or (isinstance(n, float) and pd.isna(n)):
        return "—"
    n = float(n)
    if abs(n) >= 1_000_000:
        m = n / 1_000_000
        s = f"{m:.2f}".rstrip("0").rstrip(".")
        return f"{s}M"
    if abs(n) >= 1_000:
        return f"{int(round(n / 1_000))}K"
    return f"{int(round(n)):,}"


def _parse_generators_sheet(df: pd.DataFrame) -> dict[str, Any]:
    """
    Sheet 2. Energy — generator fuel (Liters).
    Data rows 11–13; months H→S (index 7–18); Total col T (index 19).
    """
    rows: list[dict[str, Any]] = []
    for excel_row in _GENERATOR_DATA_ROWS:
        rec = _parse_generator_row(df, excel_row)
        if rec:
            rows.append(rec)

    monthly = _generator_monthly_totals(rows)
    monthly_series = _month_series(monthly)

    def _row_total(row: dict[str, Any] | None) -> float:
        if not row:
            return 0.0
        if row.get("total") is not None:
            return float(row["total"])
        return sum(v or 0 for v in row["months"].values())

    jnj = next((r for r in rows if "221" in r["location"] or "JNJ" in r["facility_name"]), rows[0] if rows else None)
    ikea = next((r for r in rows if "234" in r["location"] or "IKEA" in r["facility_name"].upper()), None)
    ryd = next((r for r in rows if "324" in r["location"] or "RYD" in r["facility_name"].upper()), None)

    kpis = [
        {
            "id": "total_diesel",
            "label": "Total Diesel (L)",
            "value": _format_kpi_generators(sum(monthly.values())),
            "sub": "All generator sites",
            "icon": "⛽",
            "theme": "gen-amber",
        },
        {
            "id": "jnj",
            "label": "JED - JNJ (221)",
            "value": _format_kpi_generators(_row_total(jnj)),
            "sub": "Generator · Diesel",
            "icon": "⛽",
            "theme": "gen-orange",
        },
        {
            "id": "ikea",
            "label": "JED IKEA WH (234)",
            "value": _format_kpi_generators(_row_total(ikea)),
            "sub": "Flow warehouse",
            "icon": "⛽",
            "theme": "gen-brown",
        },
        {
            "id": "ryd",
            "label": "RYD-3PL MDC (324)",
            "value": _format_kpi_generators(_row_total(ryd)),
            "sub": "Riyadh 3PL",
            "icon": "⛽",
            "theme": "gen-slate",
        },
    ]

    return {
        "year": 2025,
        "kpis": kpis,
        "rows": rows,
        "monthly_totals": monthly,
        "monthly_series": monthly_series,
        "annual_total": sum(monthly.values()),
        # Legacy
        "sections": [
            {
                "title": "Generator Fuel (Liters)",
                "rows": rows,
                "monthly_totals": monthly,
                "monthly_series": monthly_series,
                "annual_total": sum(monthly.values()),
                "facility_count": len(rows),
            }
        ],
    }


# Sheet 4. Water — cols B,C,D + E→P (months) + Q (total); same layout as electricity grid
_WATER_LITERS_DATA_ROWS = range(11, 33)  # Excel rows 11–32 (22 facilities; row 10 = header)
_WATER_COST_DATA_ROWS = range(38, 56)  # Excel rows 38–55 (cost table; row 37 = header)
_WATER_LITERS_GRAND_ROW = 34  # Monthly grand totals (user doc row 33)


def _parse_water_row(df: pd.DataFrame, excel_row: int) -> dict[str, Any] | None:
    """One water row — cols B–Q (Excel 1-based)."""
    idx = excel_row - 1
    if idx < 0 or idx >= len(df):
        return None
    row = df.iloc[idx]
    name = _norm(row.iloc[3]) if len(row) > 3 else ""
    if not name or name.upper() == "FACILITY NAME":
        return None
    months: dict[str, float | None] = {}
    for j, m in enumerate(MONTHS):
        col = 4 + j
        months[m] = _parse_number(row.iloc[col]) if col < len(row) else None
    total = _parse_number(row.iloc[16]) if len(row) > 16 else None
    if total is None:
        nums = [v for v in months.values() if v is not None]
        total = sum(nums) if nums else None
    return {
        "excel_row": excel_row,
        "facility_type": _norm(row.iloc[1]) if len(row) > 1 else "",
        "location": _norm(row.iloc[2]) if len(row) > 2 else "",
        "facility_name": name,
        "months": months,
        "total": total,
    }


def _water_monthly_from_rows(rows: list[dict[str, Any]]) -> dict[str, float]:
    totals = _empty_months()
    for row in rows:
        for m in MONTHS:
            v = row.get("months", {}).get(m)
            if v is not None:
                totals[m] += v
    return totals


def _water_row_total(row: dict[str, Any] | None) -> float:
    if not row:
        return 0.0
    if row.get("total") is not None:
        return float(row["total"])
    return sum(v for v in row.get("months", {}).values() if v is not None)


def _parse_water_sheet(
    liters_df: pd.DataFrame, cost_df: pd.DataFrame | None = None
) -> dict[str, Any]:
    """
    Water tab — LITERS sheet rows 11–32, grand total row 34; COST sheet rows 38–55.
    Monthly charts: SUM(E11:E32) … per sheet (matches SUM(E10:P31) when row 10 is header).
    """
    liters_rows: list[dict[str, Any]] = []
    for excel_row in _WATER_LITERS_DATA_ROWS:
        rec = _parse_water_row(liters_df, excel_row)
        if rec:
            liters_rows.append(rec)

    liters_monthly = _empty_months()
    for i, col in enumerate(_OVERVIEW_MONTH_COLS):
        liters_monthly[MONTHS[i]] = _sum_excel_range(liters_df, col, 11, 32)

    grand_total_row: dict[str, Any] | None = None
    gt_idx = _WATER_LITERS_GRAND_ROW - 1
    if gt_idx < len(liters_df):
        gt_months: dict[str, float | None] = {}
        for j, m in enumerate(MONTHS):
            gt_months[m] = _parse_number(liters_df.iloc[gt_idx, 4 + j])
        grand_total_row = {
            "label": "Grand Total",
            "months": gt_months,
            "total": _parse_number(liters_df.iloc[gt_idx, 16])
            if len(liters_df.iloc[gt_idx]) > 16
            else None,
        }
        if grand_total_row["total"] is None:
            nums = [v for v in gt_months.values() if v is not None]
            grand_total_row["total"] = sum(nums) if nums else None

    cost_rows: list[dict[str, Any]] = []
    cost_monthly = _empty_months()
    if cost_df is not None:
        for excel_row in _WATER_COST_DATA_ROWS:
            rec = _parse_water_row(cost_df, excel_row)
            if rec:
                cost_rows.append(rec)
        for i, col in enumerate(_OVERVIEW_MONTH_COLS):
            cost_monthly[MONTHS[i]] = _sum_excel_range(cost_df, col, 38, 55)

    medina = next(
        (r for r in liters_rows if "medina labor" in r["facility_name"].lower()),
        None,
    )
    jed_mdc = next(
        (
            r
            for r in liters_rows
            if "3PL MDC WH" in r["facility_name"].upper()
            and "JEDDAH" in r["location"].upper()
        ),
        None,
    )

    liters_annual = sum(liters_monthly.values())
    kpis = [
        {
            "id": "total_water",
            "label": "Total Water (Liters)",
            "value": _format_kpi_electricity(liters_annual),
            "sub": "All Facilities",
            "icon": "💧",
            "theme": "water-blue",
        },
        {
            "id": "medina_labor",
            "label": "Medina Labor Accomm.",
            "value": _format_kpi_electricity(_water_row_total(medina)),
            "sub": "Largest Single Site",
            "icon": "💧",
            "theme": "water-teal",
        },
        {
            "id": "jed_mdc",
            "label": "JED 3PL MDC WH",
            "value": _format_kpi_electricity(_water_row_total(jed_mdc)),
            "sub": "2nd Largest",
            "icon": "💧",
            "theme": "water-red",
        },
        {
            "id": "facility_count",
            "label": "Facilities Tracked",
            "value": str(len(liters_rows)),
            "sub": "Users Data",
            "icon": "🏢",
            "theme": "water-purple",
        },
    ]

    liters_block = {
        "rows": liters_rows,
        "grand_total": grand_total_row,
        "monthly_totals": liters_monthly,
        "monthly_series": _month_series(liters_monthly),
        "annual_total": liters_annual,
        "facility_count": len(liters_rows),
    }
    cost_block = {
        "rows": cost_rows,
        "grand_total": None,
        "monthly_totals": cost_monthly,
        "monthly_series": _month_series(cost_monthly),
        "annual_total": sum(cost_monthly.values()),
        "facility_count": len(cost_rows),
    }

    return {
        "year": 2025,
        "kpis": kpis,
        "liters": liters_block,
        "cost": cost_block,
        # Legacy keys (generic tab renderer / overview)
        "sections": [
            {
                "title": "Water Consumption (Liters)",
                "rows": liters_rows,
                "monthly_totals": liters_monthly,
                "monthly_series": _month_series(liters_monthly),
                "annual_total": liters_annual,
                "facility_count": len(liters_rows),
            }
        ],
        "monthly_totals": liters_monthly,
        "monthly_series": _month_series(liters_monthly),
        "annual_total": liters_annual,
    }


# Sheet 5. Waste — months F→Q (cols 5–16); Total R (17)
# Data rows (header row sits one above each block in the workbook):
#   Recycling: 29–31 (Cardboard, Shrink wrap, Pallet) — header on row 28
#   General cost: 39–56 — header on row 38
#   Destruction cost: 64–77 — header on row 63
_WASTE_MONTH_COLS = ("F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q")
_WASTE_RECYCLING_ROWS = (29, 30, 31)
_WASTE_COST_ROWS = range(39, 57)
_WASTE_DESTRUCTION_ROWS = range(64, 78)


def _format_kpi_waste_kg(n: float) -> str:
    """Waste recycling KPIs: 35.5K, 24.8K, 7.7K, 3.0K."""
    if n is None or (isinstance(n, float) and pd.isna(n)):
        return "—"
    n = float(n)
    if abs(n) >= 1_000_000:
        m = n / 1_000_000
        s = f"{m:.2f}".rstrip("0").rstrip(".")
        return f"{s}M"
    if abs(n) >= 1_000:
        k = n / 1_000
        s = f"{k:.1f}".rstrip("0").rstrip(".")
        return f"{s}K"
    return f"{int(round(n)):,}"


def _parse_waste_row(df: pd.DataFrame, excel_row: int) -> dict[str, Any] | None:
    """One waste row — cols B–R (Excel 1-based row)."""
    idx = excel_row - 1
    if idx < 0 or idx >= len(df):
        return None
    row = df.iloc[idx]
    facility_type = _norm(row.iloc[1]) if len(row) > 1 else ""
    location = _norm(row.iloc[2]) if len(row) > 2 else ""
    facility_name = _norm(row.iloc[3]) if len(row) > 3 else ""
    detail = _norm(row.iloc[4]) if len(row) > 4 else ""
    if not facility_name and not detail:
        return None
    months: dict[str, float | None] = {}
    for j, m in enumerate(MONTHS):
        col = 5 + j
        months[m] = _parse_number(row.iloc[col]) if col < len(row) else None
    total = _parse_number(row.iloc[17]) if len(row) > 17 else None
    if total is None:
        nums = [v for v in months.values() if v is not None]
        total = sum(nums) if nums else None
    return {
        "excel_row": excel_row,
        "facility_type": facility_type,
        "location": location,
        "facility_name": facility_name,
        "material": detail,
        "waste_type": detail,
        "months": months,
        "total": total,
    }


def _waste_monthly_totals(
    df: pd.DataFrame, row_start: int, row_end: int
) -> dict[str, float]:
    monthly = _empty_months()
    for i, col in enumerate(_WASTE_MONTH_COLS):
        monthly[MONTHS[i]] = _sum_excel_range(df, col, row_start, row_end)
    return monthly


def _waste_row_annual(df: pd.DataFrame, excel_row: int) -> float:
    return sum(_sum_excel_range(df, col, excel_row, excel_row) for col in _WASTE_MONTH_COLS)


def _parse_waste_sheet(df: pd.DataFrame) -> dict[str, Any]:
    """Sheet 5. Waste — recycling (rows 28–30) and disposal cost (rows 38–55)."""
    recycling_rows: list[dict[str, Any]] = []
    for excel_row in _WASTE_RECYCLING_ROWS:
        rec = _parse_waste_row(df, excel_row)
        if rec:
            recycling_rows.append(rec)

    cost_rows: list[dict[str, Any]] = []
    for excel_row in _WASTE_COST_ROWS:
        rec = _parse_waste_row(df, excel_row)
        if rec:
            cost_rows.append(rec)

    monthly_recycling = _waste_monthly_totals(df, 29, 31)
    monthly_cost = _waste_monthly_totals(df, 39, 56)

    total_recycling = sum(monthly_recycling.values())
    cardboard_total = _waste_row_annual(df, 29)
    shrink_total = _waste_row_annual(df, 30)
    pallet_total = _waste_row_annual(df, 31)
    total_cost_general = sum(monthly_cost.values())
    total_cost_destruction = sum(_waste_monthly_totals(df, 64, 77).values())
    total_cost = total_cost_general + total_cost_destruction

    recycling_gt_months: dict[str, float | None] = {}
    for m in MONTHS:
        recycling_gt_months[m] = sum(
            (r["months"].get(m) or 0) for r in recycling_rows
        )
    recycling_grand_total = {
        "label": "TOTAL",
        "facility_type": "",
        "location": "",
        "facility_name": "",
        "material": "",
        "months": recycling_gt_months,
        "total": total_recycling,
    }

    kpis = [
        {
            "id": "total_recycling",
            "label": "Total Recycling (kg)",
            "value": _format_kpi_waste_kg(total_recycling),
            "sub": "Dammam Facility",
            "icon": "♻️",
            "theme": "waste-green",
        },
        {
            "id": "cardboard",
            "label": "Cardboard (kg)",
            "value": _format_kpi_waste_kg(cardboard_total),
            "sub": "Cardboard (kg)",
            "icon": "📦",
            "theme": "waste-orange",
        },
        {
            "id": "shrink_wrap",
            "label": "Shrink Wrap (kg)",
            "value": _format_kpi_waste_kg(shrink_total),
            "sub": "Shrink Wrap (kg)",
            "icon": "🧴",
            "theme": "waste-teal",
        },
        {
            "id": "pallets",
            "label": "Pallets (kg)",
            "value": _format_kpi_waste_kg(pallet_total),
            "sub": "Pallets (kg)",
            "icon": "🪵",
            "theme": "waste-brown",
        },
        {
            "id": "waste_cost",
            "label": "Waste Cost (SAR)",
            "value": _format_kpi_electricity(total_cost),
            "sub": "General + Destruction",
            "icon": "💰",
            "theme": "waste-red",
        },
    ]

    recycling_block = {
        "rows": recycling_rows,
        "grand_total": recycling_grand_total,
        "monthly_totals": monthly_recycling,
        "monthly_series": _month_series(monthly_recycling),
        "annual_total": total_recycling,
    }
    cost_block = {
        "rows": cost_rows,
        "grand_total": None,
        "monthly_totals": monthly_cost,
        "monthly_series": _month_series(monthly_cost),
        "annual_total": total_cost_general,
    }

    return {
        "year": 2025,
        "kpis": kpis,
        "recycling": recycling_block,
        "cost": cost_block,
        "monthly_recycling": _month_series(monthly_recycling),
        "monthly_cost": _month_series(monthly_cost),
        "annual_recycling": total_recycling,
        "annual_cost": total_cost,
        "annual_cost_general": total_cost_general,
        "annual_cost_destruction": total_cost_destruction,
        # Legacy (overview / generic tab renderer)
        "sections": [
            {
                "title": "RECYCLING — DAMMAM FACILITY DETAIL (KG)",
                "rows": recycling_rows,
                "monthly_totals": monthly_recycling,
                "monthly_series": _month_series(monthly_recycling),
                "annual_total": total_recycling,
                "facility_count": len(recycling_rows),
            },
            {
                "title": "WASTE COST — GENERAL WASTE DISPOSAL COST (SAR)",
                "rows": cost_rows,
                "monthly_totals": monthly_cost,
                "monthly_series": _month_series(monthly_cost),
                "annual_total": total_cost_general,
                "facility_count": len(cost_rows),
            },
        ],
        "monthly_fuel": _month_series(monthly_recycling),
        "annual_fuel": total_recycling,
    }


# Sheet 6. Fugitive gases — months J→U (cols 9–20); Total V (21); Remarks W (22)
# Data rows 11–22 (header row 10); user doc rows 10–21 map to these
_FUGITIVE_MONTH_COLS = ("J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U")
_FUGITIVE_DATA_ROWS = range(11, 23)


def _normalize_gas_name(name: str) -> str:
    g = _norm(name)
    if not g:
        return ""
    if "(" in g:
        g = g.split("(", 1)[0].strip()
    upper = g.upper().replace(" ", "")
    if upper in ("R-134A", "R134A"):
        return "R-134a"
    return g


def _most_common_label(values: list[str]) -> str:
    from collections import Counter

    items = [_norm(v) for v in values if _norm(v)]
    if not items:
        return "—"
    return Counter(items).most_common(1)[0][0]


def _parse_fugitive_row(df: pd.DataFrame, excel_row: int) -> dict[str, Any] | None:
    """One equipment row — cols B–W (Excel 1-based row)."""
    idx = excel_row - 1
    if idx < 0 or idx >= len(df):
        return None
    row = df.iloc[idx]
    facility_name = _norm(row.iloc[3]) if len(row) > 3 else ""
    if not facility_name or facility_name.upper() == "FACILITY NAME":
        return None
    months: dict[str, float | None] = {}
    for j, m in enumerate(MONTHS):
        col = 9 + j
        months[m] = _parse_number(row.iloc[col]) if col < len(row) else None
    total = _parse_number(row.iloc[21]) if len(row) > 21 else None
    if total is None:
        nums = [v for v in months.values() if v is not None]
        total = sum(nums) if nums else None
    equipment = _norm(row.iloc[4]) if len(row) > 4 else ""
    return {
        "excel_row": excel_row,
        "facility_type": _norm(row.iloc[1]) if len(row) > 1 else "",
        "location": _norm(row.iloc[2]) if len(row) > 2 else "",
        "facility_name": facility_name,
        "equipment_type": equipment,
        "asset_id": _norm(row.iloc[5]) if len(row) > 5 else "",
        "refrigerant_type": _norm(row.iloc[6]) if len(row) > 6 else "",
        "gas_name": _normalize_gas_name(row.iloc[7]) if len(row) > 7 else "",
        "reason": _norm(row.iloc[8]) if len(row) > 8 else "",
        "remarks": _norm(row.iloc[22]) if len(row) > 22 else "",
        "months": months,
        "total": total,
        "chart_label": f"{facility_name} — {equipment}"[:48],
    }


def _fugitive_monthly_totals(df: pd.DataFrame, row_start: int, row_end: int) -> dict[str, float]:
    monthly = _empty_months()
    for i, col in enumerate(_FUGITIVE_MONTH_COLS):
        monthly[MONTHS[i]] = _sum_excel_range(df, col, row_start, row_end)
    return monthly


def _parse_fugitive_sheet(df: pd.DataFrame) -> dict[str, Any]:
    """Sheet 6. Fugitive gases — equipment rows 11–22."""
    rows: list[dict[str, Any]] = []
    for excel_row in _FUGITIVE_DATA_ROWS:
        rec = _parse_fugitive_row(df, excel_row)
        if rec:
            rows.append(rec)

    monthly_totals = _fugitive_monthly_totals(df, 11, 22)
    annual_total = sum(monthly_totals.values())

    gt_months: dict[str, float | None] = {m: monthly_totals[m] for m in MONTHS}
    grand_total_row = {
        "label": "TOTAL",
        "facility_type": "",
        "location": "",
        "facility_name": "",
        "equipment_type": "",
        "gas_name": "",
        "reason": "",
        "months": gt_months,
        "total": annual_total,
    }

    chiller_rows = [r for r in rows if "chiller" in r["equipment_type"].lower()]
    chiller_gas = _most_common_label([r["gas_name"] for r in chiller_rows]) if chiller_rows else "R-134a"
    primary_reason = _most_common_label([r["reason"] for r in rows])

    gas_totals: dict[str, float] = {}
    for r in rows:
        gas = r["gas_name"] or "Other"
        gas_totals[gas] = gas_totals.get(gas, 0.0) + (r["total"] or 0.0)
    gas_breakdown = [
        {"label": gas, "value": round(kg, 1)}
        for gas, kg in sorted(gas_totals.items(), key=lambda x: -x[1])
    ]

    stacked_datasets = [
        {
            "label": r["chart_label"],
            "data": [int(round(r["months"].get(m) or 0)) for m in MONTHS],
        }
        for r in rows
    ]

    kpis = [
        {
            "id": "total_refills",
            "label": "Total Refills (kg)",
            "value": _format_kpi(annual_total),
            "sub": "All Equipment",
            "icon": "❄️",
            "theme": "fug-purple",
        },
        {
            "id": "equipment_units",
            "label": "Equipment Units",
            "value": str(len(rows)),
            "sub": "Tracked Assets",
            "icon": "🏭",
            "theme": "fug-red",
        },
        {
            "id": "chiller_gas",
            "label": "Chiller Gas Type",
            "value": chiller_gas,
            "sub": "Primary Gas Type",
            "icon": "❄️",
            "theme": "fug-teal",
        },
        {
            "id": "primary_reason",
            "label": "Primary Refill Reason",
            "value": primary_reason,
            "sub": "Most Common",
            "icon": "🔧",
            "theme": "fug-crimson",
        },
    ]

    return {
        "year": 2025,
        "kpis": kpis,
        "rows": rows,
        "grand_total": grand_total_row,
        "monthly_totals": monthly_totals,
        "monthly_series": _month_series(monthly_totals),
        "annual_total": annual_total,
        "stacked_chart": {
            "labels": list(MONTH_LABELS),
            "datasets": stacked_datasets,
        },
        "gas_breakdown": gas_breakdown,
        # Legacy
        "sections": [
            {
                "title": "Fugitive Gas Refills (kg)",
                "rows": rows,
                "monthly_totals": monthly_totals,
                "monthly_series": _month_series(monthly_totals),
                "annual_total": annual_total,
                "facility_count": len(rows),
            }
        ],
    }


def _transport_monthly_totals(df: pd.DataFrame, col_letters: tuple[str, ...]) -> dict[str, float]:
    """SUM per month col (rows 7–600); OCT–DEC stay 0."""
    monthly = _empty_months()
    for i, col in enumerate(col_letters):
        monthly[MONTHS[i]] = _sum_excel_range(df, col, 7, 600)
    return monthly


def _parse_transportation_sheet(df: pd.DataFrame) -> dict[str, Any]:
    """
    Sheet 3. Transportation — rows 7–600.
    Fixed cols B–I; monthly blocks of 5 (distance, trips, fuel, plt, weight).
    """
    monthly_fuel = _transport_monthly_totals(df, _TRANSPORT_FUEL_COLS)
    monthly_distance = _transport_monthly_totals(df, _TRANSPORT_DISTANCE_COLS)
    monthly_trips = _transport_monthly_totals(df, _TRANSPORT_TRIPS_COLS)

    dist_indices = [_excel_col(c) for c in _TRANSPORT_DISTANCE_COLS]
    trips_indices = [_excel_col(c) for c in _TRANSPORT_TRIPS_COLS]
    fuel_indices = [_excel_col(c) for c in _TRANSPORT_FUEL_COLS]

    vehicles: list[dict[str, Any]] = []
    for excel_row in _TRANSPORT_DATA_ROWS:
        idx = excel_row - 1
        if idx < 0 or idx >= len(df):
            continue
        row = df.iloc[idx].tolist()
        no_val = _norm(row[1]) if len(row) > 1 else ""
        plate = _norm(row[2]) if len(row) > 2 else ""
        if not no_val and not plate:
            continue

        distance_by_month: dict[str, float | None] = {}
        trips_by_month: dict[str, float | None] = {}
        fuel_by_month: dict[str, float | None] = {}
        for mi in range(9):
            m = MONTHS[mi]
            dc = dist_indices[mi]
            tc = trips_indices[mi]
            fc = fuel_indices[mi]
            distance_by_month[m] = _parse_number(row[dc]) if dc < len(row) else None
            trips_by_month[m] = _parse_number(row[tc]) if tc < len(row) else None
            fuel_by_month[m] = _parse_number(row[fc]) if fc < len(row) else None

        total_distance = sum(v or 0 for v in distance_by_month.values())
        total_trips = sum(v or 0 for v in trips_by_month.values())
        total_fuel = sum(v or 0 for v in fuel_by_month.values())

        vehicles.append(
            {
                "no": no_val,
                "plate": plate,
                "truck_type": _norm(row[3]) if len(row) > 3 else "",
                "model": _norm(row[4]) if len(row) > 4 else "",
                "branch": _norm(row[5]) if len(row) > 5 else "",
                "fuel_type": _norm(row[6]) if len(row) > 6 else "",
                "max_plt": _parse_number(row[7]) if len(row) > 7 else None,
                "max_kg": _parse_number(row[8]) if len(row) > 8 else None,
                "distance": distance_by_month,
                "trips": trips_by_month,
                "fuel": fuel_by_month,
                "total_distance": total_distance,
                "total_trips": total_trips,
                "total_fuel": total_fuel,
                # Legacy keys
                "months": fuel_by_month,
                "annual_fuel": total_fuel,
            }
        )

    no_col = _excel_col("B")
    vehicle_count = int(
        df.iloc[6:600, no_col].map(lambda x: _norm(x) != "").sum()
    )
    type_col = _excel_col("D")
    fuel_col = _excel_col("G")
    branch_col = _excel_col("F")

    annual_fuel = sum(monthly_fuel.values())
    annual_distance = sum(monthly_distance.values())
    annual_trips = sum(monthly_trips.values())

    kpis = [
        {
            "id": "total_vehicles",
            "label": "Total Vehicles",
            "value": str(vehicle_count),
            "sub": "All Types",
            "icon": "🚛",
            "theme": "trans-red",
        },
        {
            "id": "total_fuel",
            "label": "Fuel Consumed (L)",
            "value": _format_kpi_electricity(annual_fuel),
            "sub": "Jan-Sep",
            "icon": "⛽",
            "theme": "trans-red",
        },
        {
            "id": "total_distance",
            "label": "Total Distance (km)",
            "value": _format_kpi_electricity(annual_distance),
            "sub": "Jan-Sep",
            "icon": "🛣️",
            "theme": "trans-green",
        },
        {
            "id": "total_trips",
            "label": "Total Trips",
            "value": _format_kpi_electricity(annual_trips),
            "sub": "Jan-Sep",
            "icon": "📍",
            "theme": "trans-yellow",
        },
        {
            "id": "reefer_dyna",
            "label": "Reefer Dyna-5T",
            "value": str(
                _count_excel_column(df, type_col, 7, 600, ("Reefer Dyna-5T",))
            ),
            "sub": "Largest Fleet Type",
            "icon": "🚚",
            "theme": "trans-blue",
        },
        {
            "id": "ev_vehicles",
            "label": "EV Vehicles",
            "value": str(_count_excel_column(df, fuel_col, 7, 600, ("EV",))),
            "sub": "Electric",
            "icon": "🔋",
            "theme": "trans-blue",
        },
    ]

    fleet_by_branch = [
        {
            "label": label,
            "value": _count_excel_column(df, branch_col, 7, 600, variants),
        }
        for label, variants in _OVERVIEW_BRANCHES
    ]
    fleet_by_vehicle_type = [
        {
            "label": label,
            "value": _count_excel_column(df, type_col, 7, 600, variants),
        }
        for label, variants in _OVERVIEW_VEHICLE_TYPES
    ]
    fleet_by_fuel = [
        {
            "label": label,
            "value": _count_excel_column(df, fuel_col, 7, 600, variants),
        }
        for label, variants in _TRANSPORT_FUEL_TYPES
    ]

    return {
        "year": 2025,
        "vehicle_count": vehicle_count,
        "kpis": kpis,
        "vehicles": vehicles,
        "fleet_by_branch": fleet_by_branch,
        "fleet_by_vehicle_type": fleet_by_vehicle_type,
        "fleet_by_fuel": fleet_by_fuel,
        "filters": {
            "types": list(_TRANSPORT_FILTER_TYPES),
            "branches": list(_TRANSPORT_FILTER_BRANCHES),
            "fuels": list(_TRANSPORT_FILTER_FUELS),
        },
        "monthly_fuel": _month_series(monthly_fuel),
        "monthly_distance": _month_series(monthly_distance),
        "monthly_trips": _month_series(monthly_trips),
        "monthly_fuel_totals": monthly_fuel,
        "monthly_distance_totals": monthly_distance,
        "monthly_trips_totals": monthly_trips,
        "annual_fuel": annual_fuel,
        "annual_distance": annual_distance,
        "annual_trips": annual_trips,
        # Legacy
        "vehicles_truncated": False,
        "sections": [
            {
                "title": "Fleet Fuel (Liters)",
                "monthly_totals": monthly_fuel,
                "monthly_series": _month_series(monthly_fuel),
                "annual_total": annual_fuel,
                "facility_count": vehicle_count,
            }
        ],
    }


def _clean_governance_text(text: str) -> str:
    s = _norm(text)
    if not s:
        return s
    return (
        s.replace("Solid Watse", "Solid Waste")
        .replace("KWM", "KWH")
        .replace("Fugutive", "Fugitive")
    )


def _governance_owner_icon(department: str, data_scope: str) -> str:
    text = f"{department} {data_scope}".lower()
    if "transport" in text:
        return "🚛"
    if "maintenance" in text or "fugitive" in text or "renewable" in text:
        return "🔧"
    if "water" in text:
        return "💧"
    if "waste" in text or "solid" in text:
        return "♻️"
    if "electric" in text or "energy" in text:
        return "⚡"
    return "📋"


def _parse_governance_sheet(df: pd.DataFrame) -> dict[str, Any]:
    """Sheet Data Governance — champions, data owners, coverage notes."""
    group_champion: dict[str, str] = {
        "name": "",
        "position": "",
        "role": "Group ESG Champion",
        "icon": "👑",
    }
    subsidiary_champion: dict[str, str] = {
        "name": "",
        "position": "",
        "role": "Subsidiary ESG Champion",
        "icon": "🏢",
    }
    data_owners: list[dict[str, Any]] = []
    coverage_notes: list[dict[str, str]] = []

    section = ""
    for i in range(len(df)):
        row = df.iloc[i].tolist()
        label = _norm(row[2]) if len(row) > 2 else ""
        value = _norm(row[4]) if len(row) > 4 else ""
        status_text = _norm(row[3]) if len(row) > 3 else ""
        note_text = _norm(row[4]) if len(row) > 4 else ""
        department = _norm(row[8]) if len(row) > 8 else ""
        data_scope = _norm(row[12]) if len(row) > 12 else ""

        if label == "Group ESG Champion":
            section = "group"
            continue
        if label in ("Subsdiary ESG Champion", "Subsidiary ESG Champion"):
            section = "subsidiary"
            continue
        if label == "Data owner(s)":
            section = "owners"
            continue
        if label in ("Tabs List", "Data Governance") or label.startswith("Data Governance"):
            section = "coverage"
            continue

        if section == "group":
            if label == "Name":
                group_champion["name"] = value
            elif label == "Position":
                group_champion["position"] = value
            continue

        if section == "subsidiary":
            if label == "Name":
                subsidiary_champion["name"] = value
            elif label == "Position":
                subsidiary_champion["position"] = value
            continue

        if section == "owners" and label == "Name/position" and value:
            dept_label = department + " Department" if department and "department" not in department.lower() else department
            data_owners.append(
                {
                    "name": value,
                    "department": dept_label or department,
                    "data_scope": _clean_governance_text(data_scope),
                    "icon": _governance_owner_icon(department, data_scope),
                }
            )
            continue

        if section == "coverage" and label and label[0].isdigit() and "." in label[:4]:
            tab_label = label.split(".", 1)[-1].strip()
            if note_text:
                topic = tab_label
                if "electric" in tab_label.lower():
                    topic = "Electricity"
                elif "transport" in tab_label.lower():
                    topic = "Transportation"
                elif "waste" in tab_label.lower():
                    topic = "Waste"
                elif "fug" in tab_label.lower():
                    topic = "Fugitive Gases"
                elif "energy" in tab_label.lower():
                    topic = "Energy (Generators)"
                elif "water" in tab_label.lower():
                    topic = "Water"
                coverage_notes.append(
                    {"topic": topic, "text": _clean_governance_text(note_text)}
                )
            continue

    if not coverage_notes:
        coverage_notes = [
            {
                "topic": "Electricity",
                "text": "Finance had only cost-related data. KWH usage data is not available.",
            },
            {
                "topic": "Transportation",
                "text": "All fields completed except Pallets & Weight data which are not available.",
            },
            {
                "topic": "Waste",
                "text": "Only cost-related data available. Weight is not available.",
            },
        ]

    champions = [c for c in (group_champion, subsidiary_champion) if c.get("name")]

    return {
        "champions": champions,
        "group_champion": group_champion,
        "subsidiary_champion": subsidiary_champion,
        "data_owners": data_owners,
        "coverage_notes": coverage_notes,
        # Legacy
        "blocks": [
            {"title": "Group ESG Champion", "rows": [{"label": "Name", "value": group_champion["name"]}]},
            {"title": "Data owner(s)", "rows": [{"label": o["name"], "value": o["data_scope"]} for o in data_owners]},
        ],
    }


# Overview tab — Excel cell ranges (1-based rows/cols as in Environment-Tamer-Logistics.xlsx)
_OVERVIEW_MONTH_COLS = ("E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P")
_OVERVIEW_FUEL_COLS = ("L", "Q", "V", "AA", "AF", "AK", "AP", "AU", "AZ")  # JAN–SEP; OCT–DEC = 0
_OVERVIEW_FUGITIVE_COLS = ("J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U")

_OVERVIEW_BRANCHES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Jeddah", ("Jeddah",)),
    ("Riyadh", ("Riyadh",)),
    ("Khobar", ("Khobar",)),
    ("ABHA", ("ABHA",)),
    ("Buraidah", ("Buraidah",)),
    ("Madinah", ("Madinah",)),
    ("Tabuk", ("Tabuk",)),
    ("AL BAHA", ("AL BAHA", "AL Baha")),
)

_OVERVIEW_VEHICLE_TYPES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Reefer Dyna-5T", ("Reefer Dyna-5T",)),
    ("VAN", ("VAN",)),
    ("Reefer Trailer", ("REEFER TRAILER-R",)),
    ("Reefer Lorry", ("Reefer Lorry-10T",)),
    ("Trailer-CS", ("Trailer - CS",)),
)

_TRANSPORT_DISTANCE_COLS = ("J", "O", "T", "Y", "AD", "AI", "AN", "AS", "AX")
_TRANSPORT_TRIPS_COLS = ("K", "P", "U", "Z", "AE", "AJ", "AO", "AT", "AY")
_TRANSPORT_FUEL_COLS = _OVERVIEW_FUEL_COLS  # L, Q, V, AA, AF, AK, AP, AU, AZ
_TRANSPORT_FUEL_TYPES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Diesel", ("Diesel",)),
    ("91", ("91",)),
    ("EV", ("EV",)),
)
_TRANSPORT_FILTER_TYPES: tuple[str, ...] = (
    "REEFER TRAILER-R",
    "Reefer Dyna-5T",
    "Reefer Lorry-10T",
    "Trailer - CS",
    "VAN",
)
_TRANSPORT_FILTER_BRANCHES: tuple[str, ...] = (
    "ABHA",
    "AL BAHA",
    "AL Baha",
    "Buraidah",
    "Jeddah",
    "Khobar",
    "Madinah",
    "Riyadh",
    "Tabuk",
)
_TRANSPORT_FILTER_FUELS: tuple[str, ...] = ("91", "Diesel", "EV")
_TRANSPORT_DATA_ROWS = range(7, 601)  # Excel rows 7–600


def _excel_col(letter: str) -> int:
    n = 0
    for c in letter.upper():
        n = n * 26 + (ord(c) - ord("A") + 1)
    return n - 1


def _sum_excel_range(df: pd.DataFrame, col_letter: str, row_start: int, row_end: int) -> float:
    """SUM(col row_start:row_end) — Excel 1-based inclusive rows."""
    col = _excel_col(col_letter)
    vals = df.iloc[row_start - 1 : row_end, col]
    return float(pd.to_numeric(vals, errors="coerce").sum())


def _count_excel_column(
    df: pd.DataFrame,
    col_index: int,
    row_start: int,
    row_end: int,
    matchers: tuple[str, ...],
) -> int:
    series = df.iloc[row_start - 1 : row_end, col_index].map(_norm)
    match_set = {m.strip().upper() for m in matchers}
    return int(series.map(lambda s: s.upper() in match_set).sum())


def _compute_overview_charts(
    elec_df: pd.DataFrame,
    water_df: pd.DataFrame,
    trans_df: pd.DataFrame,
    fug_df: pd.DataFrame,
) -> dict[str, Any]:
    """Overview charts using the same ranges as the Excel dashboard formulas."""
    grid_monthly = _empty_months()
    solar_gen_monthly = _empty_months()
    solar_use_monthly = _empty_months()
    water_monthly = _empty_months()
    fleet_fuel_monthly = _empty_months()
    fugitive_monthly = _empty_months()

    for i, col in enumerate(_OVERVIEW_MONTH_COLS):
        m = MONTHS[i]
        grid_monthly[m] = _sum_excel_range(elec_df, col, 11, 31)
        solar_gen_monthly[m] = _sum_excel_range(elec_df, col, 40, 41)
        solar_use_monthly[m] = _sum_excel_range(elec_df, col, 47, 48)
        water_monthly[m] = _sum_excel_range(water_df, col, 11, 32)

    for i, col in enumerate(_OVERVIEW_FUEL_COLS):
        fleet_fuel_monthly[MONTHS[i]] = _sum_excel_range(trans_df, col, 7, 600)
    for m in MONTHS[9:]:
        fleet_fuel_monthly[m] = 0.0

    for i, col in enumerate(_OVERVIEW_FUGITIVE_COLS):
        fugitive_monthly[MONTHS[i]] = _sum_excel_range(fug_df, col, 11, 22)

    branch_col = _excel_col("F")  # Branch
    type_col = _excel_col("D")  # Type of Truck
    fleet_by_branch = [
        {
            "label": label,
            "value": _count_excel_column(trans_df, branch_col, 7, 600, variants),
        }
        for label, variants in _OVERVIEW_BRANCHES
    ]
    fleet_by_vehicle_type = [
        {
            "label": label,
            "value": _count_excel_column(trans_df, type_col, 7, 600, variants),
        }
        for label, variants in _OVERVIEW_VEHICLE_TYPES
    ]

    vehicle_count = int(
        trans_df.iloc[6:600, _excel_col("B")].map(lambda x: _norm(x) != "").sum()
    )

    return {
        "grid_monthly": grid_monthly,
        "solar_gen_monthly": solar_gen_monthly,
        "solar_use_monthly": solar_use_monthly,
        "water_monthly": water_monthly,
        "fleet_fuel_monthly": fleet_fuel_monthly,
        "fugitive_monthly": fugitive_monthly,
        "fleet_by_branch": fleet_by_branch,
        "fleet_by_vehicle_type": fleet_by_vehicle_type,
        "vehicle_count": vehicle_count,
    }


def _range_fill_ratio(df: pd.DataFrame, col_letters: tuple[str, ...], row_start: int, row_end: int) -> float:
    """Share of numeric cells filled in a rectangular Excel range (0–1)."""
    filled = 0
    total = 0
    for col in col_letters:
        c = _excel_col(col)
        for row_idx in range(row_start - 1, row_end):
            if row_idx >= len(df):
                continue
            total += 1
            if _parse_number(df.iloc[row_idx, c]) is not None:
                filled += 1
    return filled / total if total else 0.0


def _months_with_data(monthly: dict[str, float], min_months: int = 1) -> int:
    return sum(1 for m in MONTHS if monthly.get(m, 0) > 0)


def _compute_data_coverage(
    sheets: dict[str, pd.DataFrame],
    parsed: dict[str, Any],
    *,
    overview_charts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Data coverage status cards for Overview (matches dashboard design).
    Status is inferred from sheet completeness; footnote explains partial gaps.
    """
    elec_df = sheets[SHEET_ELECTRICITY]
    energy_df = sheets[SHEET_ENERGY]
    trans_df = sheets[SHEET_TRANSPORTATION]
    water_df = sheets[SHEET_WATER_LITERS]
    waste_df = sheets[SHEET_WASTE]
    fug_df = sheets[SHEET_FUGITIVE]

    if overview_charts:
        grid_monthly = overview_charts.get("grid_monthly") or _empty_months()
    else:
        grid_monthly = _empty_months()
        for col_letter in _OVERVIEW_MONTH_COLS:
            mi = _OVERVIEW_MONTH_COLS.index(col_letter)
            grid_monthly[MONTHS[mi]] = _sum_excel_range(elec_df, col_letter, 11, 31)

    grid_kwh_total = sum(grid_monthly.values())
    grid_months = _months_with_data(grid_monthly)
    # Grid KWH lives on Excel rows 11–31 (row 10 is headers — do not use for fill checks).
    grid_fill = _range_fill_ratio(elec_df, _OVERVIEW_MONTH_COLS, 11, 31)
    if grid_months >= 10 and grid_kwh_total > 0:
        elec_status = "completed"
    elif grid_months >= 3 or grid_kwh_total > 0 or grid_fill >= 0.4:
        elec_status = "partially_completed"
    else:
        elec_status = "pending"

    gen_monthly = _empty_months()
    for i, col in enumerate(_OVERVIEW_MONTH_COLS):
        if i < len(MONTHS):
            gen_monthly[MONTHS[i]] = _sum_excel_range(energy_df, col, 10, 17)
    gen_status = (
        "completed"
        if _months_with_data(gen_monthly) >= 3 and sum(gen_monthly.values()) > 0
        else "pending"
    )

    fleet_monthly = _empty_months()
    for i, col in enumerate(_OVERVIEW_FUEL_COLS):
        fleet_monthly[MONTHS[i]] = _sum_excel_range(trans_df, col, 7, 600)
    vehicle_count = int(
        trans_df.iloc[6:600, _excel_col("B")].map(lambda x: _norm(x) != "").sum()
    )
    trans_status = (
        "completed"
        if vehicle_count > 0 and _months_with_data(fleet_monthly) >= 6
        else "partially_completed" if vehicle_count > 0 else "pending"
    )

    water_monthly = _empty_months()
    for i, col in enumerate(_OVERVIEW_MONTH_COLS):
        water_monthly[MONTHS[i]] = _sum_excel_range(water_df, col, 11, 32)
    water_status = (
        "completed" if _months_with_data(water_monthly) >= 10 else "partially_completed"
    )

    waste_parsed = parsed.get("waste") or {}
    recycling_total = (waste_parsed.get("recycling") or {}).get("annual_total") or 0
    cost_total = (waste_parsed.get("cost") or {}).get("annual_total") or 0
    if recycling_total > 0 and cost_total > 0:
        waste_status = "completed"
    elif recycling_total > 0 or cost_total > 0:
        waste_status = "partially_completed"
    else:
        waste_status = "pending"

    fug_monthly = _empty_months()
    for i, col in enumerate(_OVERVIEW_FUGITIVE_COLS):
        fug_monthly[MONTHS[i]] = _sum_excel_range(fug_df, col, 11, 22)
    fug_status = "completed" if sum(fug_monthly.values()) > 0 else "pending"

    items = [
        {
            "id": "electricity",
            "label": "Electricity",
            "icon": "electricity",
            "theme": "yellow",
            "status": elec_status,
            "status_label": _coverage_status_label(elec_status),
        },
        {
            "id": "generators",
            "label": "Energy (Generators)",
            "icon": "generators",
            "theme": "red",
            "status": gen_status,
            "status_label": _coverage_status_label(gen_status),
        },
        {
            "id": "transportation",
            "label": "Transportation",
            "icon": "transportation",
            "theme": "red",
            "status": trans_status,
            "status_label": _coverage_status_label(trans_status),
        },
        {
            "id": "water",
            "label": "Water",
            "icon": "water",
            "theme": "blue",
            "status": water_status,
            "status_label": _coverage_status_label(water_status),
        },
        {
            "id": "waste",
            "label": "Waste",
            "icon": "waste",
            "theme": "blue",
            "status": waste_status,
            "status_label": _coverage_status_label(waste_status),
        },
        {
            "id": "fugitive",
            "label": "Fugitive Gases",
            "icon": "fugitive",
            "theme": "cyan",
            "status": fug_status,
            "status_label": _coverage_status_label(fug_status),
        },
    ]

    notes: list[str] = []
    if elec_status == "partially_completed":
        notes.append(
            "Electricity KWH incomplete — fill monthly KWH for grid facilities "
            "(sheet 1. Electricty, rows 11–31, columns E–P)."
        )
    if waste_status == "partially_completed":
        if recycling_total > 0 and cost_total == 0:
            notes.append("Waste cost data not available")
        elif cost_total > 0 and recycling_total == 0:
            notes.append("Recycling data not available (cost only)")

    return {
        "items": items,
        "footnote": " · ".join(notes),
    }


def _coverage_status_label(status: str) -> str:
    return {
        "completed": "Completed",
        "partially_completed": "Partially Completed",
        "pending": "Pending",
    }.get(status, "Pending")


def _build_overview(parsed: dict[str, Any], sheets: dict[str, pd.DataFrame] | None = None) -> dict[str, Any]:
    elec = parsed.get("electricity") or {}
    energy = parsed.get("generators") or {}
    waste = parsed.get("waste") or {}
    fugitive = parsed.get("fugitive") or {}

    gen_total = energy.get("annual_total") or 0
    gen_sites = len(energy.get("rows") or [])

    recycling = waste.get("recycling") or {}
    if not recycling.get("annual_total"):
        waste_sections = waste.get("sections") or []
        recycling = next(
            (s for s in waste_sections if "RECYCLING" in (s.get("title") or "").upper()),
            {},
        )

    if sheets:
        ov = _compute_overview_charts(
            sheets[SHEET_ELECTRICITY],
            sheets[SHEET_WATER_LITERS],
            sheets[SHEET_TRANSPORTATION],
            sheets[SHEET_FUGITIVE],
        )
        grid_monthly = ov["grid_monthly"]
        solar_gen_monthly = ov["solar_gen_monthly"]
        solar_use_monthly = ov["solar_use_monthly"]
        water_monthly = ov["water_monthly"]
        fleet_fuel_monthly = ov["fleet_fuel_monthly"]
        fugitive_monthly = ov["fugitive_monthly"]
        fleet_by_branch = ov["fleet_by_branch"]
        fleet_by_vehicle_type = ov["fleet_by_vehicle_type"]
        vehicle_count = ov["vehicle_count"]
    else:
        grid_monthly = _empty_months()
        solar_gen_monthly = _empty_months()
        solar_use_monthly = _empty_months()
        water_monthly = _empty_months()
        fleet_fuel_monthly = _empty_months()
        fugitive_monthly = _empty_months()
        fleet_by_branch = []
        fleet_by_vehicle_type = []
        vehicle_count = 0

    kpis = [
        {
            "id": "grid_electricity",
            "label": "Grid Electricity (KWH)",
            "value": _format_kpi(sum(grid_monthly.values())),
            "sub": "21 Facilities",
            "theme": "yellow",
        },
        {
            "id": "solar",
            "label": "Solar Generated (KWH)",
            "value": _format_kpi(sum(solar_gen_monthly.values())),
            "sub": "JED 3PL MDC + HC MDC",
            "theme": "orange",
        },
        {
            "id": "water",
            "label": "Water (Liters)",
            "value": _format_kpi(sum(water_monthly.values())),
            "sub": "22 Facilities",
            "theme": "blue",
        },
        {
            "id": "fleet_fuel",
            "label": "Fleet Fuel (Liters)",
            "value": _format_kpi(sum(fleet_fuel_monthly.values())),
            "sub": f"{vehicle_count} Vehicles - Jan-Sep",
            "theme": "red",
        },
        {
            "id": "fugitive",
            "label": "Fugitive Gases (kg)",
            "value": _format_kpi(
                fugitive.get("annual_total") or sum(fugitive_monthly.values())
            ),
            "sub": f"{len(fugitive.get('rows') or [])} Equipment Units",
            "theme": "purple",
        },
        {
            "id": "recycling",
            "label": "Recycling (kg)",
            "value": _format_kpi(recycling.get("annual_total") or 0),
            "sub": "Cardboard, Shrink, Pallet",
            "theme": "green",
        },
        {
            "id": "generator_fuel",
            "label": "Generator Fuel (L)",
            "value": _format_kpi(gen_total),
            "sub": f"{gen_sites} Sites · Diesel",
            "theme": "amber",
        },
        {
            "id": "fleet_vehicles",
            "label": "Total Fleet Vehicles",
            "value": _format_kpi(vehicle_count),
            "sub": "Diesel + EV",
            "theme": "navy",
        },
    ]

    data_coverage = (
        _compute_data_coverage(sheets, parsed, overview_charts=ov if sheets else None)
        if sheets
        else {"items": [], "footnote": ""}
    )

    return {
        "year": elec.get("year") or 2025,
        "kpis": kpis,
        "charts": {
            "grid_electricity": _month_series(grid_monthly),
            "solar_generation": _month_series(solar_gen_monthly),
            "solar_consumption": _month_series(solar_use_monthly),
            "water": _month_series(water_monthly),
            "fleet_fuel": _month_series(fleet_fuel_monthly),
            "fugitive": _month_series(fugitive_monthly),
            "fleet_by_branch": fleet_by_branch,
            "fleet_by_vehicle_type": fleet_by_vehicle_type,
        },
        "data_coverage": data_coverage,
    }


def parse_environment_workbook(
    raw: bytes, report_year: int | None = None
) -> dict[str, Any]:
    """Parse full Environment workbook into tab-keyed JSON."""
    try:
        xl = pd.ExcelFile(io.BytesIO(raw), engine="openpyxl")
    except Exception as exc:
        raise ValueError(f"Could not read Excel file: {exc}") from exc

    sheets = set(xl.sheet_names)
    required = {
        SHEET_ELECTRICITY,
        SHEET_ENERGY,
        SHEET_TRANSPORTATION,
        SHEET_WATER_LITERS,
        SHEET_WASTE,
        SHEET_FUGITIVE,
        SHEET_GOVERNANCE,
    }
    missing = sorted(required - sheets)
    if missing:
        from .report_years import expected_workbook_filename

        hint = (
            expected_workbook_filename(report_year)
            if report_year
            else "Environment-Tamer-Logistics-{year}.xlsx"
        )
        raise ValueError(
            "Workbook is missing expected sheet(s): "
            + ", ".join(missing)
            + f". Use {hint} with the same sheet layout."
        )

    def read_sheet(name: str) -> pd.DataFrame:
        return pd.read_excel(xl, sheet_name=name, header=None)

    sheet_frames = {
        SHEET_ELECTRICITY: read_sheet(SHEET_ELECTRICITY),
        SHEET_ENERGY: read_sheet(SHEET_ENERGY),
        SHEET_TRANSPORTATION: read_sheet(SHEET_TRANSPORTATION),
        SHEET_WATER_LITERS: read_sheet(SHEET_WATER_LITERS),
        SHEET_WASTE: read_sheet(SHEET_WASTE),
        SHEET_FUGITIVE: read_sheet(SHEET_FUGITIVE),
        SHEET_GOVERNANCE: read_sheet(SHEET_GOVERNANCE),
    }

    electricity = _parse_electricity_sheet(sheet_frames[SHEET_ELECTRICITY])
    generators = _parse_generators_sheet(sheet_frames[SHEET_ENERGY])
    transportation = _parse_transportation_sheet(sheet_frames[SHEET_TRANSPORTATION])
    water_cost_df = (
        read_sheet(SHEET_WATER_COST) if SHEET_WATER_COST in sheets else None
    )
    water = _parse_water_sheet(sheet_frames[SHEET_WATER_LITERS], water_cost_df)
    waste = _parse_waste_sheet(sheet_frames[SHEET_WASTE])
    fugitive = _parse_fugitive_sheet(sheet_frames[SHEET_FUGITIVE])
    governance = _parse_governance_sheet(sheet_frames[SHEET_GOVERNANCE])

    parsed = {
        "source_sheets": list(xl.sheet_names),
        "electricity": electricity,
        "generators": generators,
        "transportation": transportation,
        "water": water,
        "water_cost": water.get("cost"),
        "waste": waste,
        "fugitive": fugitive,
        "governance": governance,
    }
    parsed["overview"] = _build_overview(parsed, sheets=sheet_frames)
    parsed["governance"]["data_coverage"] = parsed["overview"].get("data_coverage") or {}

    tabs = [
        {"id": "overview", "label": "Overview", "icon": "overview"},
        {"id": "electricity", "label": "Electricity", "icon": "electricity"},
        {"id": "generators", "label": "Generators", "icon": "generators"},
        {"id": "water", "label": "Water", "icon": "water"},
        {"id": "transportation", "label": "Transportation", "icon": "transportation"},
        {"id": "waste", "label": "Waste", "icon": "waste"},
        {"id": "fugitive", "label": "Fugitive Gases", "icon": "fugitive"},
        {"id": "governance", "label": "Governance", "icon": "governance"},
    ]
    parsed["tabs"] = tabs
    year = report_year or parsed.get("overview", {}).get("year") or 2025
    parsed["report_year"] = int(year)
    if parsed.get("overview") is not None:
        parsed["overview"]["year"] = parsed["report_year"]
    return parsed


def validate_environment_workbook_path(path: str) -> dict[str, Any]:
    with open(path, "rb") as f:
        return parse_environment_workbook(f.read())
