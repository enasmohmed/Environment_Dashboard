from django import forms

from .models import EnvironmentWorkbook
from .report_years import expected_workbook_filename, is_expected_workbook_filename


class EnvironmentWorkbookAdminForm(forms.ModelForm):
    """Validate Environment-Tamer-Logistics-{year}.xlsx and attach parsed JSON."""

    class Meta:
        model = EnvironmentWorkbook
        fields = ("title", "report_year", "file", "is_active")

    def clean(self):
        from .environment_parse import parse_environment_workbook

        cleaned_data = super().clean()
        f = cleaned_data.get("file")
        if f is False:
            self.instance.parsed_snapshot = None
            return cleaned_data
        if not f:
            if not self.instance.pk:
                year = cleaned_data.get("report_year") or self.instance.report_year or 2025
                raise forms.ValidationError(
                    {
                        "file": (
                            f"Upload {expected_workbook_filename(year)} "
                            "(or .xlsm with the same base name)."
                        )
                    }
                )
            return cleaned_data
        year = cleaned_data.get("report_year") or self.instance.report_year or 2025
        upload_name = getattr(f, "name", "") or ""
        if not is_expected_workbook_filename(upload_name, year):
            expected = expected_workbook_filename(year)
            raise forms.ValidationError(
                {
                    "file": (
                        f"The file must be named {expected} (or .xlsm) for report year {year}."
                    )
                }
            )
        raw = f.read()
        if hasattr(f, "seek"):
            f.seek(0)
        try:
            year = cleaned_data.get("report_year") or self.instance.report_year or 2025
            snapshot = parse_environment_workbook(raw, report_year=year)
            snapshot["report_year"] = year
            self.instance.parsed_snapshot = snapshot
        except ValueError as exc:
            raise forms.ValidationError({"file": str(exc)}) from exc
        return cleaned_data
