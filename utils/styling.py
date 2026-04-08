from __future__ import annotations

import pandas as pd



def format_currency(value: object) -> str:
    if value is None or value == "":
        return "—"
    try:
        value_float = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"R$ {value_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")



def apply_table_theme(styler: pd.io.formats.style.Styler) -> pd.io.formats.style.Styler:
    return styler.set_properties(
        **{
            "border": "1px solid #111111",
            "font-size": "0.88rem",
        }
    ).set_table_styles(
        [
            {
                "selector": "th",
                "props": [
                    ("background-color", "#efefef"),
                    ("color", "#111111"),
                    ("border", "1px solid #111111"),
                    ("font-weight", "700"),
                ],
            }
        ]
    )



def _diff_style(value: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if number > 0:
        return "background-color: #fce8e8; color: #8a1c1c;"
    if number < 0:
        return "background-color: #e8f5ea; color: #14532d;"
    return "background-color: #f2f2f2; color: #333333;"



def colorize_differences(
    frame: pd.DataFrame,
    columns: list[str],
    styler: pd.io.formats.style.Styler,
) -> pd.io.formats.style.Styler:
    valid_columns = [column for column in columns if column in frame.columns]
    if not valid_columns:
        return styler
    return styler.applymap(_diff_style, subset=valid_columns)
