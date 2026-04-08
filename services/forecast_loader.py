from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd

from services.models import ForecastMetadata
from services.parsers import find_dual_amount_header, parse_dual_amount_layout, parse_single_amount_layout
from utils.text import clean_display_text, normalize_text


PREFERRED_SHEET_TOKENS = ["previs", "orc", "orça", "prev"]



def _read_workbook(source: Any) -> tuple[pd.ExcelFile, bytes, str]:
    if isinstance(source, (str, Path)):
        path = Path(source)
        return pd.ExcelFile(path), path.read_bytes(), path.name

    file_name = getattr(source, "name", "previsao")
    raw_bytes = source.getvalue() if hasattr(source, "getvalue") else source.read()
    return pd.ExcelFile(BytesIO(raw_bytes)), raw_bytes, file_name



def _choose_sheet(workbook: pd.ExcelFile) -> str:
    prioritized = [
        name
        for name in workbook.sheet_names
        if any(token in normalize_text(name) for token in PREFERRED_SHEET_TOKENS)
    ]
    candidates = prioritized or workbook.sheet_names

    best_sheet = candidates[0]
    best_score = -1
    for sheet_name in candidates:
        frame = pd.read_excel(workbook, sheet_name=sheet_name, header=None)
        score = int(frame.notna().sum().sum())
        if score > best_score:
            best_score = score
            best_sheet = sheet_name
    return best_sheet



def _search_value(frame: pd.DataFrame, labels: list[str]) -> str | None:
    for row_idx in range(min(len(frame), 20)):
        row = frame.iloc[row_idx].tolist()
        for col_idx, value in enumerate(row):
            current = normalize_text(value)
            if current in labels:
                if col_idx + 1 < len(row):
                    next_value = clean_display_text(row[col_idx + 1])
                    if next_value:
                        return next_value
                if row_idx + 1 < len(frame):
                    below_value = clean_display_text(frame.iloc[row_idx + 1, col_idx])
                    if below_value:
                        return below_value
                if row_idx + 1 < len(frame) and col_idx + 1 < frame.shape[1]:
                    diagonal = clean_display_text(frame.iloc[row_idx + 1, col_idx + 1])
                    if diagonal:
                        return diagonal
    return None



def _infer_metadata(frame: pd.DataFrame, file_name: str, logical_label: str, sheet_name: str) -> ForecastMetadata:
    empreendimento = _search_value(frame, ["empreendimento", "condominio", "condomínio"])
    administradora = _search_value(frame, ["administradora", "incorporadora"])

    stem = Path(file_name).stem
    if not empreendimento and " - " in stem:
        empreendimento = stem.split(" - ", maxsplit=1)[1].strip()
    if not administradora and " - " in stem:
        administradora = stem.split(" - ", maxsplit=1)[0].strip()

    if not empreendimento:
        joined = " ".join(
            clean_display_text(value)
            for value in frame.iloc[:10, :6].fillna("").values.flatten().tolist()
        )
        match = re.search(r"(?:condom[ií]nio|empreendimento)[:\s]+([^\n\r]+)", joined, flags=re.IGNORECASE)
        if match:
            empreendimento = clean_display_text(match.group(1))

    return ForecastMetadata(
        filename=file_name,
        label=logical_label,
        administradora=administradora,
        empreendimento=empreendimento,
        source_sheet=sheet_name,
    )



def load_forecast(source: Any, logical_label: str) -> tuple[pd.DataFrame, ForecastMetadata, str | None]:
    workbook, raw_bytes, file_name = _read_workbook(source)
    sheet_name = _choose_sheet(workbook)
    frame = pd.read_excel(BytesIO(raw_bytes), sheet_name=sheet_name, header=None)
    metadata = _infer_metadata(frame, file_name, logical_label, sheet_name)

    header_info = find_dual_amount_header(frame)
    if header_info is not None:
        header_row, col_90, col_cota = header_info
        parsed = parse_dual_amount_layout(frame, header_row, col_90, col_cota)
        metadata.parser_name = "dual_amount_layout"
        metadata.amount_mode = "90_dias_e_cota_plena"
        warning = None
    else:
        parsed, warning = parse_single_amount_layout(frame)
        metadata.parser_name = "single_amount_layout"
        metadata.amount_mode = "valor_unico_replicado"

    if parsed.empty:
        raise ValueError(
            "Nenhuma linha comparável foi encontrada neste arquivo. "
            "Confira se a planilha possui a previsão de despesas em um formato compatível."
        )

    parsed.insert(0, "administradora", metadata.administradora or "")
    parsed.insert(1, "empreendimento", metadata.empreendimento or "")
    return parsed, metadata, warning
