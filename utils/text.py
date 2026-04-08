from __future__ import annotations

import math
import re
import unicodedata
from typing import Any

import pandas as pd


TEXT_NULLS = {"", "nan", "none", "null", "nat", "-", "--"}


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value).strip()
    if text.lower() in TEXT_NULLS:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()



def clean_display_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value).replace("\n", " ").replace("\r", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text



def parse_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not pd.isna(value):
        return float(value)

    text = clean_display_text(value)
    if not text:
        return None

    text_lower = text.lower()
    if any(token in text_lower for token in ["rateio", "conforme conta real"]):
        return None

    text = text.replace("R$", "").replace(" ", "")

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(".", "").replace(",", ".")

    try:
        return float(text)
    except ValueError:
        return None



def looks_like_code(value: str) -> bool:
    text = clean_display_text(value)
    if not text:
        return False
    return bool(re.match(r"^(\d+(?:\.\d+)*|[A-Z]\)|[A-Z]\.)$", text, re.IGNORECASE))



def is_blank_row(values: list[Any]) -> bool:
    return all(not clean_display_text(value) for value in values)



def safe_sheet_name(value: str, fallback: str) -> str:
    text = clean_display_text(value) or fallback
    text = re.sub(r"[\\/*?:\[\]]", "-", text)
    return text[:31]
