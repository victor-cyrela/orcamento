from __future__ import annotations

import pandas as pd

from services.models import ComparisonResult, ForecastResult



def compare_forecasts(base: ForecastResult, target: ForecastResult) -> ComparisonResult:
    base_summary = base.consolidated.rename(
        columns={
            "valor_90_dias": "valor_90_dias_base",
            "valor_cota_plena": "valor_cota_plena_base",
        }
    )
    target_summary = target.consolidated.rename(
        columns={
            "valor_90_dias": "valor_90_dias_target",
            "valor_cota_plena": "valor_cota_plena_target",
        }
    )

    summary = base_summary.merge(
        target_summary,
        on="classificacao_exibicao",
        how="outer",
    ).fillna(0.0)

    summary["diff_90_dias"] = summary["valor_90_dias_target"] - summary["valor_90_dias_base"]
    summary["diff_cota_plena"] = summary["valor_cota_plena_target"] - summary["valor_cota_plena_base"]
    summary["abs_sort"] = summary[["diff_90_dias", "diff_cota_plena"]].abs().max(axis=1)
    summary = summary.sort_values(
        by=["abs_sort", "classificacao_exibicao"],
        ascending=[False, True],
        ignore_index=True,
    ).drop(columns="abs_sort")

    details_by_classificacao: dict[str, pd.DataFrame] = {}
    for classification in summary["classificacao_exibicao"].tolist():
        base_details = base.details_by_classificacao.get(classification, pd.DataFrame()).copy()
        target_details = target.details_by_classificacao.get(classification, pd.DataFrame()).copy()

        if not base_details.empty:
            base_details["fonte"] = base.metadata.label
        if not target_details.empty:
            target_details["fonte"] = target.metadata.label

        combined = pd.concat([base_details, target_details], ignore_index=True)
        details_by_classificacao[classification] = combined

    return ComparisonResult(
        base_label=base.metadata.label,
        target_label=target.metadata.label,
        summary=summary,
        details_by_classificacao=details_by_classificacao,
    )
