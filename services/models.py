from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import pandas as pd


@dataclass(slots=True)
class LibraryEntry:
    pattern: str
    classification_display: str
    priority: int = 100
    scope: Literal["description", "section", "both"] = "both"


@dataclass(slots=True)
class ForecastMetadata:
    filename: str
    label: str
    administradora: str | None = None
    empreendimento: str | None = None
    source_sheet: str | None = None
    parser_name: str | None = None
    amount_mode: str | None = None


@dataclass(slots=True)
class ForecastResult:
    metadata: ForecastMetadata
    standardized_rows: pd.DataFrame
    consolidated: pd.DataFrame
    details_by_classificacao: dict[str, pd.DataFrame] = field(default_factory=dict)
    non_classified: pd.DataFrame = field(default_factory=pd.DataFrame)


@dataclass(slots=True)
class ComparisonResult:
    base_label: str
    target_label: str
    summary: pd.DataFrame
    details_by_classificacao: dict[str, pd.DataFrame] = field(default_factory=dict)
