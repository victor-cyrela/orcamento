from __future__ import annotations

import re
from typing import Any

import pandas as pd

from utils.text import clean_display_text, is_blank_row, normalize_text, parse_number


STOP_PATTERNS = [
    "previsao de receita",
    "base de calculo",
    "rateio das cotas",
    "receitas",
]

TOP_LEVEL_HINTS = [
    "despesas",
    "pessoal",
    "contratos",
    "concessionarias",
    "tarifas",
    "administrativas",
    "patrimoniais",
    "manutencao",
    "diversos",
]



def find_dual_amount_header(df: pd.DataFrame) -> tuple[int, int, int] | None:
    for row_idx in range(min(len(df), 30)):
        row = [normalize_text(value) for value in df.iloc[row_idx].tolist()]
        col_90 = None
        col_cota = None
        for col_idx, value in enumerate(row):
            if value == "90 dias":
                col_90 = col_idx
            if "cota" in value and "plena" in value:
                col_cota = col_idx
        if col_90 is not None and col_cota is not None:
            return row_idx, col_90, col_cota
    return None



def find_best_single_amount_column(df: pd.DataFrame) -> int:
    start_row = min(5, max(len(df) - 1, 0))
    scores: list[tuple[int, int]] = []
    for col_idx in range(df.shape[1]):
        numeric_count = 0
        for value in df.iloc[start_row:, col_idx].tolist():
            if parse_number(value) is not None:
                numeric_count += 1
        scores.append((numeric_count, col_idx))

    best_score, best_col = max(scores, key=lambda item: (item[0], item[1]))
    if best_score < 3:
        raise ValueError(
            "Não foi possível identificar uma coluna confiável de valores nesta previsão."
        )
    return best_col



def should_stop(description: str) -> bool:
    normalized = normalize_text(description)
    return any(pattern in normalized for pattern in STOP_PATTERNS)



def is_total_row(description: str) -> bool:
    normalized = normalize_text(description)
    return normalized.startswith("total") or normalized.startswith("sub total") or normalized == "totais" or "total das despesas" in normalized



def split_code_description(first_text: str, second_text: str = "") -> tuple[str, str]:
    first = clean_display_text(first_text)
    second = clean_display_text(second_text)

    if second:
        if re.match(r"^(\d+(?:\.\d+)*|[A-Z]\)|[A-Z]\.|\d+\.)$", first, flags=re.IGNORECASE):
            return first.rstrip("."), second
        return "", first

    match = re.match(
        r"^(?P<code>[A-Z]\)|[A-Z]\.|\d+(?:\.\d+)*)(?:\s*[-.]?)\s+(?P<desc>.+)$",
        first,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group("code").rstrip("."), clean_display_text(match.group("desc"))

    return "", first



def is_section_candidate(code: str, description: str, all_codes: set[str]) -> bool:
    code_norm = clean_display_text(code).rstrip(".")
    desc_norm = normalize_text(description)
    if not code_norm or not desc_norm:
        return False

    if re.match(r"^[A-Z]\)$", code_norm, flags=re.IGNORECASE):
        return True

    if any(other != code_norm and other.startswith(f"{code_norm}.") for other in all_codes):
        return True

    if re.match(r"^\d+$", code_norm) and any(token in desc_norm for token in TOP_LEVEL_HINTS):
        return True

    return False



def _finalize_records(records: list[dict[str, Any]], section_totals: list[dict[str, Any]]) -> pd.DataFrame:
    if not records and not section_totals:
        return pd.DataFrame(
            columns=[
                "descricao_original",
                "section_original",
                "valor_90_dias",
                "valor_cota_plena",
            ]
        )

    used_sections = {
        normalize_text(record["section_original"])
        for record in records
        if clean_display_text(record.get("section_original"))
    }

    for section_total in section_totals:
        if normalize_text(section_total["descricao_original"]) not in used_sections:
            records.append(section_total)

    frame = pd.DataFrame(records)
    if frame.empty:
        return frame

    frame["valor_90_dias"] = frame["valor_90_dias"].fillna(0.0).astype(float)
    frame["valor_cota_plena"] = frame["valor_cota_plena"].fillna(0.0).astype(float)
    return frame



def parse_dual_amount_layout(df: pd.DataFrame, header_row: int, col_90: int, col_cota: int) -> pd.DataFrame:
    description_col = max(0, min(col_90, col_cota) - 1)
    code_col = max(0, description_col - 1)

    code_candidates: set[str] = set()
    parsed_rows: list[dict[str, Any]] = []
    for row_idx in range(header_row + 1, len(df)):
        row_values = df.iloc[row_idx].tolist()
        if is_blank_row(row_values):
            continue

        raw_code = clean_display_text(row_values[code_col]) if code_col < len(row_values) else ""
        raw_desc = clean_display_text(row_values[description_col]) if description_col < len(row_values) else ""
        code, description = split_code_description(raw_code, raw_desc)
        if not description:
            continue
        code_candidates.add(code)
        parsed_rows.append(
            {
                "code": code,
                "description": description,
                "value_90": parse_number(row_values[col_90]) if col_90 < len(row_values) else None,
                "value_cota": parse_number(row_values[col_cota]) if col_cota < len(row_values) else None,
            }
        )

    records: list[dict[str, Any]] = []
    section_totals: list[dict[str, Any]] = []
    current_section = ""

    for item in parsed_rows:
        code = item["code"]
        description = item["description"]
        value_90 = item["value_90"]
        value_cota = item["value_cota"]

        if should_stop(description):
            break
        if is_total_row(description):
            continue

        if is_section_candidate(code, description, code_candidates):
            current_section = description
            if value_90 is not None or value_cota is not None:
                section_totals.append(
                    {
                        "descricao_original": description,
                        "section_original": description,
                        "valor_90_dias": value_90,
                        "valor_cota_plena": value_cota,
                    }
                )
            continue

        if value_90 is None and value_cota is None:
            continue

        records.append(
            {
                "descricao_original": description,
                "section_original": current_section,
                "valor_90_dias": value_90,
                "valor_cota_plena": value_cota,
            }
        )

    return _finalize_records(records, section_totals)



def parse_single_amount_layout(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    amount_col = find_best_single_amount_column(df)

    code_candidates: set[str] = set()
    parsed_rows: list[dict[str, Any]] = []
    for row_idx in range(len(df)):
        row_values = df.iloc[row_idx].tolist()
        if is_blank_row(row_values):
            continue

        first_text = clean_display_text(row_values[0]) if row_values else ""
        second_text = clean_display_text(row_values[1]) if len(row_values) > 1 else ""
        code, description = split_code_description(first_text, second_text)
        if not description:
            continue

        code_candidates.add(code)
        parsed_rows.append(
            {
                "code": code,
                "description": description,
                "amount": parse_number(row_values[amount_col]) if amount_col < len(row_values) else None,
            }
        )

    records: list[dict[str, Any]] = []
    section_totals: list[dict[str, Any]] = []
    current_section = ""

    for item in parsed_rows:
        code = item["code"]
        description = item["description"]
        amount = item["amount"]

        if should_stop(description):
            break
        if is_total_row(description):
            continue

        if is_section_candidate(code, description, code_candidates):
            current_section = description
            if amount is not None:
                section_totals.append(
                    {
                        "descricao_original": description,
                        "section_original": description,
                        "valor_90_dias": amount,
                        "valor_cota_plena": amount,
                    }
                )
            continue

        if amount is None:
            continue

        records.append(
            {
                "descricao_original": description,
                "section_original": current_section,
                "valor_90_dias": amount,
                "valor_cota_plena": amount,
            }
        )

    warning = (
        "Arquivo sem colunas separadas de 90 dias e Cota Plena. "
        "O valor identificado foi replicado nas duas colunas para permitir a comparação."
    )
    return _finalize_records(records, section_totals), warning
