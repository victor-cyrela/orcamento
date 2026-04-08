from __future__ import annotations

import re
from typing import Iterable

import pandas as pd

from services.models import ForecastMetadata, ForecastResult, LibraryEntry
from utils.text import clean_display_text, normalize_text


FALLBACK_RULES: list[tuple[str, str]] = [
    (r"pessoal|encargos|beneficios|salario|porteiro|vigia|asg|faxineir|zelador|gerente predial|assistente administrativo", "Pessoal"),
    (r"contrat|terceiriz|concierge|courrier|vigia|staff|supervisao|auditoria|juridica|servicos tecnicos", "Contratos"),
    (r"agua|esgoto|light|energia|gas|telefone|internet|concessionaria|tarifas e taxas", "Concessionárias"),
    (r"manutencao|elevador|cftv|portoes|interfone|piscina|gerador|bombas|incendio|hidr[oô]metro|exaustao|paisagismo|jardinagem", "Manutenção e Conservação"),
    (r"limpeza|higiene|dedetizacao|controle de vetores|reservatorio|material de limpeza|conservacao", "Conservação Predial"),
    (r"administrativ|boleto|cadastro|bancaria|escritorio|adm local|postagem|consultoria", "Administrativas"),
    (r"seguro", "Seguros"),
    (r"rateio", "Rateios"),
    (r"fundo", "Fundos e Reservas"),
]



def _match_library(description: str, section: str, library: Iterable[LibraryEntry]) -> str | None:
    desc_norm = normalize_text(description)
    section_norm = normalize_text(section)

    for entry in library:
        haystacks: list[str] = []
        if entry.scope in {"description", "both"}:
            haystacks.append(desc_norm)
        if entry.scope in {"section", "both"}:
            haystacks.append(section_norm)
        for haystack in haystacks:
            if haystack and re.search(entry.pattern, haystack, flags=re.IGNORECASE):
                return entry.classification_display
    return None



def _fallback_classification(description: str, section: str) -> str | None:
    combined = f"{normalize_text(section)} {normalize_text(description)}".strip()
    for pattern, label in FALLBACK_RULES:
        if re.search(pattern, combined, flags=re.IGNORECASE):
            return label
    return None



def _sort_consolidated(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    return frame.sort_values(
        by=["valor_cota_plena", "valor_90_dias", "classificacao_exibicao"],
        ascending=[False, False, True],
        ignore_index=True,
    )



def standardize_forecast(
    forecast_df: pd.DataFrame,
    metadata: ForecastMetadata,
    library: list[LibraryEntry],
) -> ForecastResult:
    working = forecast_df.copy()

    classifications: list[str] = []
    for _, row in working.iterrows():
        classification = _match_library(
            description=clean_display_text(row.get("descricao_original")),
            section=clean_display_text(row.get("section_original")),
            library=library,
        )
        if classification is None:
            classification = _fallback_classification(
                description=clean_display_text(row.get("descricao_original")),
                section=clean_display_text(row.get("section_original")),
            )
        classifications.append(classification or "Não classificado")

    working["classificacao_exibicao"] = classifications

    consolidated = (
        working.groupby("classificacao_exibicao", dropna=False, as_index=False)[["valor_90_dias", "valor_cota_plena"]]
        .sum()
        .pipe(_sort_consolidated)
    )

    details_by_classificacao: dict[str, pd.DataFrame] = {}
    for classification in consolidated["classificacao_exibicao"].tolist():
        details = working.loc[working["classificacao_exibicao"] == classification].copy()
        details_by_classificacao[classification] = details.reset_index(drop=True)

    non_classified = working.loc[working["classificacao_exibicao"] == "Não classificado"].copy()

    return ForecastResult(
        metadata=metadata,
        standardized_rows=working.reset_index(drop=True),
        consolidated=consolidated.reset_index(drop=True),
        details_by_classificacao=details_by_classificacao,
        non_classified=non_classified.reset_index(drop=True),
    )
