from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd

from services.models import LibraryEntry
from utils.text import clean_display_text, normalize_text


PATTERN_CANDIDATES = {
    "pattern",
    "regex",
    "palavra_chave",
    "palavra chave",
    "descricao",
    "descrição",
    "texto",
    "termo",
}
CLASSIFICATION_CANDIDATES = {
    "classificacao",
    "classificação",
    "tipo_de_gasto",
    "tipo de gasto",
    "categoria",
    "grupo",
    "classification_display",
}
PRIORITY_CANDIDATES = {"priority", "prioridade", "ordem"}
SCOPE_CANDIDATES = {"scope", "escopo", "match_scope", "campo"}



def _read_table(source: Any) -> tuple[pd.DataFrame, str]:
    if isinstance(source, (str, Path)):
        path = Path(source)
        suffix = path.suffix.lower()
        if suffix == ".csv":
            return pd.read_csv(path), path.name
        workbook = pd.ExcelFile(path)
        sheet_name = workbook.sheet_names[0]
        return pd.read_excel(path, sheet_name=sheet_name), path.name

    file_name = getattr(source, "name", "biblioteca")
    raw_bytes = source.getvalue() if hasattr(source, "getvalue") else source.read()
    suffix = Path(file_name).suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(BytesIO(raw_bytes)), file_name

    workbook = pd.ExcelFile(BytesIO(raw_bytes))
    sheet_name = workbook.sheet_names[0]
    return pd.read_excel(BytesIO(raw_bytes), sheet_name=sheet_name), file_name



def _standardize_headers(frame: pd.DataFrame) -> pd.DataFrame:
    renamed: dict[str, str] = {}
    for column in frame.columns:
        normalized = normalize_text(column).replace("_", " ")
        if normalized in PATTERN_CANDIDATES:
            renamed[column] = "pattern"
        elif normalized in CLASSIFICATION_CANDIDATES:
            renamed[column] = "classification_display"
        elif normalized in PRIORITY_CANDIDATES:
            renamed[column] = "priority"
        elif normalized in SCOPE_CANDIDATES:
            renamed[column] = "scope"
    return frame.rename(columns=renamed)



def load_library(source: Any) -> list[LibraryEntry]:
    frame, file_name = _read_table(source)
    frame = _standardize_headers(frame)

    missing = {"pattern", "classification_display"} - set(frame.columns)
    if missing:
        raise ValueError(
            "A biblioteca precisa ter, no mínimo, as colunas 'pattern' e "
            "'classification_display'."
        )

    if frame.empty:
        raise ValueError("A biblioteca enviada está vazia.")

    entries: list[LibraryEntry] = []
    for _, row in frame.iterrows():
        pattern = clean_display_text(row.get("pattern"))
        classification_display = clean_display_text(row.get("classification_display"))
        if not pattern or not classification_display:
            continue

        scope = normalize_text(row.get("scope"))
        if scope not in {"description", "section", "both"}:
            scope = "both"

        try:
            priority = int(row.get("priority", 100))
        except (TypeError, ValueError):
            priority = 100

        entries.append(
            LibraryEntry(
                pattern=pattern,
                classification_display=classification_display,
                priority=priority,
                scope=scope,
            )
        )

    if not entries:
        raise ValueError(f"Nenhuma regra válida foi encontrada na biblioteca {file_name}.")

    entries.sort(key=lambda item: (item.priority, item.classification_display.lower(), item.pattern.lower()))
    return entries
