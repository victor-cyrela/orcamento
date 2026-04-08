from __future__ import annotations

from typing import List, Tuple

import pandas as pd
import streamlit as st

from assets.styles import TOP_BAR_CSS
from config import (
    APP_SUBTITLE,
    APP_TITLE,
    DEFAULT_LIBRARY_PATH,
    MAX_COMPARISONS,
    MIN_COMPARISONS,
    SUPPORTED_FORECAST_EXTENSIONS,
    SUPPORTED_LIBRARY_EXTENSIONS,
)
from services.comparator import compare_forecasts
from services.exporter import build_export_file
from services.forecast_loader import load_forecast
from services.library_loader import load_library
from services.models import ForecastResult
from services.standardizer import standardize_forecast
from utils.styling import apply_table_theme, colorize_differences, format_currency
from utils.validators import validate_extension, validate_upload_size


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📊",
    layout="wide",
)
st.markdown(TOP_BAR_CSS, unsafe_allow_html=True)

state = st.session_state
if "library_state" not in state:
    state.library_state = {"status": "idle", "message": "Biblioteca ainda não carregada.", "data": None}
if "num_comparisons" not in state:
    state.num_comparisons = MIN_COMPARISONS
if "default_library_checked" not in state:
    state.default_library_checked = False



def load_default_library() -> None:
    if not DEFAULT_LIBRARY_PATH.exists():
        state.library_state = {
            "status": "error",
            "message": "Biblioteca padrão não encontrada no repositório.",
            "data": None,
        }
        state.default_library_checked = True
        return

    try:
        library_data = load_library(DEFAULT_LIBRARY_PATH)
        state.library_state = {
            "status": "success",
            "message": f"Biblioteca padrão ativa ({DEFAULT_LIBRARY_PATH.name}).",
            "data": library_data,
        }
    except Exception as exc:  # noqa: BLE001
        state.library_state = {
            "status": "error",
            "message": f"Falha ao carregar a biblioteca padrão: {exc}",
            "data": None,
        }
    finally:
        state.default_library_checked = True



def render_forecast_panel(card_index: int, library_data: list, forecast_results: list, non_classified_frames: list, system_messages: list) -> None:
    logical_label = f"Previsão {card_index + 1}"
    st.markdown("<div class='forecast-card'>", unsafe_allow_html=True)
    st.markdown(f"<h3>Selecionar {logical_label}</h3>", unsafe_allow_html=True)

    forecast_file = st.file_uploader(
        f"Selecionar previsão {card_index + 1}",
        type=sorted(SUPPORTED_FORECAST_EXTENSIONS),
        key=f"forecast_file_{card_index}",
        label_visibility="collapsed",
    )

    if forecast_file is None:
        st.markdown("<div class='forecast-meta'></div>", unsafe_allow_html=True)
        st.caption("Aguardando upload desta previsão.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    try:
        validate_extension(forecast_file.name, SUPPORTED_FORECAST_EXTENSIONS)
        validate_upload_size(forecast_file)
    except Exception as exc:  # noqa: BLE001
        st.error(str(exc))
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if library_data is None:
        st.warning("Carregue uma biblioteca antes de processar as previsões.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    try:
        forecast_df, metadata, warning = load_forecast(forecast_file, logical_label)
        if warning:
            st.markdown(f"<div class='warning-banner'>{warning}</div>", unsafe_allow_html=True)
            system_messages.append(f"{logical_label}: {warning}")

        result = standardize_forecast(forecast_df, metadata, library_data)
        forecast_results.append((card_index, result))

        st.markdown(
            f"""
            <div class='forecast-meta'>
                <strong>Administradora:</strong> {metadata.administradora or 'Não identificada'}<br>
                <strong>Empreendimento:</strong> {metadata.empreendimento or 'Não identificado'}<br>
                <strong>Arquivo:</strong> {metadata.filename}
            </div>
            """,
            unsafe_allow_html=True,
        )

        summary_display = result.consolidated.rename(
            columns={
                "classificacao_exibicao": "Classificação de Gasto",
                "valor_90_dias": "90 dias",
                "valor_cota_plena": "Cota Plena",
            }
        )
        summary_style = summary_display.style.format(
            {"90 dias": format_currency, "Cota Plena": format_currency}
        )
        summary_style = apply_table_theme(summary_style)
        st.dataframe(summary_style, use_container_width=True, hide_index=True, height=430)

        detail_classes = summary_display["Classificação de Gasto"].tolist()
        if detail_classes:
            with st.expander("Ver detalhamento desta previsão"):
                for classification in detail_classes:
                    detail_df = result.details_by_classificacao.get(classification)
                    if detail_df is None or detail_df.empty:
                        continue
                    st.markdown(f"**{classification}**")
                    detail_display = detail_df.rename(
                        columns={
                            "descricao_original": "Descrição original",
                            "section_original": "Seção original",
                            "administradora": "Administradora",
                            "empreendimento": "Empreendimento",
                            "valor_90_dias": "90 dias",
                            "valor_cota_plena": "Cota Plena",
                            "classificacao_exibicao": "Classificação",
                        }
                    )
                    detail_style = detail_display.style.format(
                        {"90 dias": format_currency, "Cota Plena": format_currency}
                    )
                    detail_style = apply_table_theme(detail_style)
                    st.dataframe(detail_style, use_container_width=True, hide_index=True)

        if not result.non_classified.empty:
            st.markdown(
                "<div class='warning-banner'>Esta previsão possui itens não classificados.</div>",
                unsafe_allow_html=True,
            )
            temp = result.non_classified.copy()
            temp.insert(0, "Previsão", metadata.label)
            non_classified_frames.append(temp)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Erro ao processar a previsão: {exc}")
        system_messages.append(f"{logical_label}: {exc}")

    st.markdown("</div>", unsafe_allow_html=True)



def render_comparison_panel(ordered_results: List[Tuple[int, ForecastResult]]) -> None:
    st.markdown("<div class='forecast-card comparison-card'>", unsafe_allow_html=True)
    st.markdown("<div class='comparison-title-box'>DIFERENÇA ENTRE PREVISÕES</div>", unsafe_allow_html=True)

    if len(ordered_results) < MIN_COMPARISONS:
        st.info("Carregue ao menos duas previsões para habilitar a comparação.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    base_entry = next((item for item in ordered_results if item[0] == 0), ordered_results[0])
    base_idx, base_result = base_entry

    comparisons = []
    for idx, result in ordered_results:
        if idx == base_idx:
            continue
        comparisons.append(compare_forecasts(base_result, result))

    if not comparisons:
        st.info("Ainda não há previsões suficientes para comparar.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    option_map = {f"{item.base_label} × {item.target_label}": item for item in comparisons}
    selected_label = st.selectbox(
        "Escolha a comparação",
        options=list(option_map.keys()),
        key="comparison_selector",
    )
    selected_comparison = option_map[selected_label]

    stats_col1, stats_col2 = st.columns(2)
    stats_col1.metric("Classificações", len(selected_comparison.summary))
    stats_col2.metric(
        "Diferença absoluta total",
        format_currency(selected_comparison.summary["diff_cota_plena"].abs().sum()),
    )

    export_file_name, export_bytes = build_export_file(
        [result for _, result in ordered_results],
        selected_comparison,
    )
    st.download_button(
        "Exportar comparação",
        data=export_bytes,
        file_name=export_file_name,
        use_container_width=True,
    )

    display_summary = selected_comparison.summary.rename(
        columns={
            "classificacao_exibicao": "Classificação de Gasto",
            "valor_90_dias_base": f"{selected_comparison.base_label} - 90 dias",
            "valor_cota_plena_base": f"{selected_comparison.base_label} - Cota Plena",
            "valor_90_dias_target": f"{selected_comparison.target_label} - 90 dias",
            "valor_cota_plena_target": f"{selected_comparison.target_label} - Cota Plena",
            "diff_90_dias": "Diferença 90 dias",
            "diff_cota_plena": "Diferença Cota Plena",
        }
    )

    currency_columns = [column for column in display_summary.columns if column != "Classificação de Gasto"]
    diff_columns = [column for column in display_summary.columns if column.startswith("Diferença")]

    comparison_style = display_summary.style.format({column: format_currency for column in currency_columns})
    comparison_style = colorize_differences(display_summary, diff_columns, comparison_style)
    comparison_style = apply_table_theme(comparison_style)
    st.dataframe(comparison_style, use_container_width=True, hide_index=True, height=430)

    with st.expander("Ver detalhamento das diferenças"):
        for classification in display_summary["Classificação de Gasto"].tolist():
            detail = selected_comparison.details_by_classificacao.get(classification)
            if detail is None or detail.empty:
                continue
            st.markdown(f"**{classification}**")
            detail_display = detail.rename(
                columns={
                    "descricao_original": "Descrição original",
                    "section_original": "Seção original",
                    "administradora": "Administradora",
                    "empreendimento": "Empreendimento",
                    "valor_90_dias": "90 dias",
                    "valor_cota_plena": "Cota Plena",
                    "fonte": "Origem",
                    "classificacao_exibicao": "Classificação",
                }
            )
            detail_style = detail_display.style.format(
                {"90 dias": format_currency, "Cota Plena": format_currency}
            )
            detail_style = apply_table_theme(detail_style)
            st.dataframe(detail_style, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)


if not state.default_library_checked:
    load_default_library()

st.markdown("<div class='app-shell'>", unsafe_allow_html=True)
with st.container():
    st.markdown("<div class='top-bar'>", unsafe_allow_html=True)
    top_left, top_mid, top_right = st.columns([1.1, 2.6, 1.3], vertical_alignment="top")

    with top_left:
        st.markdown("<div class='label-box'>Número de Comparações</div>", unsafe_allow_html=True)
        num_comparisons = st.number_input(
            "Número de comparações",
            min_value=MIN_COMPARISONS,
            max_value=MAX_COMPARISONS,
            value=state.num_comparisons,
            step=1,
            label_visibility="collapsed",
        )
        state.num_comparisons = int(num_comparisons)

    with top_mid:
        st.markdown(f"<h1>{APP_TITLE}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p class='subtitle'>{APP_SUBTITLE}</p>", unsafe_allow_html=True)
        st.caption(
            "Layout adaptado para o modelo desenhado: previsões lado a lado e um painel exclusivo para diferenças."
        )

    with top_right:
        st.markdown("<div class='label-box'>Carregar Biblioteca</div>", unsafe_allow_html=True)
        library_file = st.file_uploader(
            "Carregar biblioteca (.xlsx, .xlsm ou .csv)",
            type=sorted(SUPPORTED_LIBRARY_EXTENSIONS),
            key="library_file",
            label_visibility="collapsed",
        )
        if st.button("Usar biblioteca padrão", use_container_width=True):
            load_default_library()

        if library_file is not None:
            try:
                validate_extension(library_file.name, SUPPORTED_LIBRARY_EXTENSIONS)
                validate_upload_size(library_file)
                library_data = load_library(library_file)
                state.library_state = {
                    "status": "success",
                    "message": f"Biblioteca carregada: {library_file.name}",
                    "data": library_data,
                }
            except Exception as exc:  # noqa: BLE001
                state.library_state = {
                    "status": "error",
                    "message": str(exc),
                    "data": None,
                }

        st.markdown(
            f"<div class='status-pill {state.library_state['status']}'>{state.library_state['message']}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

library_data = state.library_state.get("data")
forecast_results: List[Tuple[int, ForecastResult]] = []
non_classified_frames: List[pd.DataFrame] = []
system_messages: List[str] = []

if state.num_comparisons == 2:
    col_forecast_1, col_forecast_2, col_diff = st.columns(3, gap="large")
    with col_forecast_1:
        render_forecast_panel(0, library_data, forecast_results, non_classified_frames, system_messages)
    with col_forecast_2:
        render_forecast_panel(1, library_data, forecast_results, non_classified_frames, system_messages)
    ordered_results = sorted(forecast_results, key=lambda item: item[0])
    with col_diff:
        render_comparison_panel(ordered_results)
else:
    st.markdown("### Previsões carregadas")
    cards_per_row = 2
    for row_start in range(0, state.num_comparisons, cards_per_row):
        row_cols = st.columns(cards_per_row, gap="large")
        for offset, column in enumerate(row_cols):
            card_index = row_start + offset
            if card_index >= state.num_comparisons:
                continue
            with column:
                render_forecast_panel(card_index, library_data, forecast_results, non_classified_frames, system_messages)

    ordered_results = sorted(forecast_results, key=lambda item: item[0])
    render_comparison_panel(ordered_results)

st.markdown("---")
st.markdown("## Avisos e exceções")

if non_classified_frames:
    nao_classificados = pd.concat(non_classified_frames, ignore_index=True)
    nao_classificados_display = nao_classificados.rename(
        columns={
            "descricao_original": "Descrição original",
            "section_original": "Seção original",
            "administradora": "Administradora",
            "empreendimento": "Empreendimento",
            "valor_90_dias": "90 dias",
            "valor_cota_plena": "Cota Plena",
            "classificacao_exibicao": "Classificação",
        }
    )
    style = nao_classificados_display.style.format(
        {"90 dias": format_currency, "Cota Plena": format_currency}
    )
    style = apply_table_theme(style)
    st.dataframe(style, use_container_width=True, hide_index=True)
else:
    st.info("Nenhum item não classificado foi identificado nas previsões carregadas.")

if system_messages:
    with st.expander("Mensagens do sistema"):
        for message in system_messages:
            st.write(f"- {message}")
else:
    st.caption("Sem avisos adicionais.")

st.markdown("</div>", unsafe_allow_html=True)
