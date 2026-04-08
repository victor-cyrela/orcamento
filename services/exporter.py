from __future__ import annotations

from io import BytesIO

import pandas as pd

from services.models import ComparisonResult, ForecastResult



def _format_for_export(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.copy()



def build_export_file(
    results: list[ForecastResult],
    comparison: ComparisonResult,
) -> tuple[str, bytes]:
    buffer = BytesIO()
    file_name = f"comparacao_{comparison.base_label.lower().replace(' ', '_')}_vs_{comparison.target_label.lower().replace(' ', '_')}.xlsx"

    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        summary = _format_for_export(comparison.summary)
        summary.to_excel(writer, sheet_name="Resumo Comparação", index=False)

        workbook = writer.book
        currency_format = workbook.add_format({"num_format": 'R$ #,##0.00', "border": 1})
        header_format = workbook.add_format({"bold": True, "bg_color": "#EDEDED", "border": 1})
        text_format = workbook.add_format({"border": 1})

        summary_sheet = writer.sheets["Resumo Comparação"]
        for col_idx, column in enumerate(summary.columns):
            summary_sheet.write(0, col_idx, column, header_format)
            width = max(16, min(38, len(str(column)) + 3))
            summary_sheet.set_column(col_idx, col_idx, width)
        for col_idx, column in enumerate(summary.columns):
            if column.startswith("valor_") or column.startswith("diff_"):
                summary_sheet.set_column(col_idx, col_idx, 18, currency_format)
            else:
                summary_sheet.set_column(col_idx, col_idx, 28, text_format)

        for result in results:
            consolidated_sheet_name = f"{result.metadata.label} - Resumo"[:31]
            detailed_sheet_name = f"{result.metadata.label} - Detalhes"[:31]

            consolidated = _format_for_export(result.consolidated)
            consolidated.to_excel(writer, sheet_name=consolidated_sheet_name, index=False)
            consolidated_sheet = writer.sheets[consolidated_sheet_name]
            for col_idx, column in enumerate(consolidated.columns):
                consolidated_sheet.write(0, col_idx, column, header_format)
                consolidated_sheet.set_column(
                    col_idx,
                    col_idx,
                    18 if column.startswith("valor_") else 30,
                    currency_format if column.startswith("valor_") else text_format,
                )

            details = _format_for_export(result.standardized_rows)
            details.to_excel(writer, sheet_name=detailed_sheet_name, index=False)
            details_sheet = writer.sheets[detailed_sheet_name]
            for col_idx, column in enumerate(details.columns):
                details_sheet.write(0, col_idx, column, header_format)
                details_sheet.set_column(
                    col_idx,
                    col_idx,
                    18 if column.startswith("valor_") else 28,
                    currency_format if column.startswith("valor_") else text_format,
                )

        non_classified_frames = [
            result.non_classified.assign(previsao=result.metadata.label)
            for result in results
            if not result.non_classified.empty
        ]
        if non_classified_frames:
            non_classified = pd.concat(non_classified_frames, ignore_index=True)
            non_classified.to_excel(writer, sheet_name="Não Classificados", index=False)
            sheet = writer.sheets["Não Classificados"]
            for col_idx, column in enumerate(non_classified.columns):
                sheet.write(0, col_idx, column, header_format)
                sheet.set_column(
                    col_idx,
                    col_idx,
                    18 if column.startswith("valor_") else 28,
                    currency_format if column.startswith("valor_") else text_format,
                )

    buffer.seek(0)
    return file_name, buffer.getvalue()
