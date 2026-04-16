# ------------------------------------------------------------------------------------------------ #
# IMPORTS

import os
import streamlit as st
from itertools import product
import math
import pandas as pd

import warnings
from streamlit_option_menu import option_menu
warnings.simplefilter(action='ignore', category=UserWarning)

# RELATIVE IMPORTS
from app.utils import TIER_CONFIG, TIER_COLORS, TIER_ORDER, TIER_NAME_SETS
DEFAULT_TIER_SET = "qualidade"

from app.src.data_loader import read_excel_data
from app.components.filters import dynamic_filters, search_box, diff_text_granular

# ------------------------------------------------------------------------------------------------ #
# FUNÇÕES AUXILIARES DOS CONSUMÍVEIS

def get_row_by_tier(df: pd.DataFrame, tier: str):
    filtered = df[df["consumable_tier"].astype(str) == str(tier)]
    if filtered.empty:
        return None
    return filtered.iloc[0]

def render_consumable_sub_page(
    df_consumables: pd.DataFrame,
    consumable_type: str,
    tier_set: str = DEFAULT_TIER_SET):

    df = df_consumables.copy()

    tier_map = TIER_NAME_SETS[tier_set]

    # -----------------------------
    # Converter nome do tier -> nível numérico
    # -----------------------------
    name_to_level = {v: k for k, v in tier_map.items()}

    df["tier_level"] = (
        df["consumable_tier"]
        .astype(str)
        .str.strip()
        .map(name_to_level)
    )

    df["tier_level"] = pd.Categorical(
        df["tier_level"],
        categories=TIER_ORDER,
        ordered=True
    )

    # -----------------------------
    # ordenar por menor id
    # -----------------------------
    order = (
        df.groupby("consumable_name")["consumable_id"]
        .min()
        .sort_values()
        .index
    )

    for consumable_name in order:

        df_consumable = (
            df[df["consumable_name"] == consumable_name]
            .sort_values("tier_level")
            .reset_index(drop=True)
        )

        with st.expander(consumable_name):

            tiers_available = [
                int(t)
                for t in df_consumable["tier_level"]
                .dropna()
                .unique()
            ]

            tiers_available = sorted(tiers_available)

            if not tiers_available:
                st.warning("Sem tiers disponíveis")
                continue

            tier_labels = [tier_map[t] for t in tiers_available]

            default_level = 1 if 1 in tiers_available else tiers_available[0]
            default_label = tier_map[default_level]

            # -----------------------------
            # Controle de seleção
            # -----------------------------
            try:
                selected_label = st.segmented_control(
                    "Tier",
                    options=tier_labels,
                    default=default_label,
                    key=f"tier_segment_{consumable_name}"
                )
            except Exception:
                selected_label = st.radio(
                    "Tier",
                    options=tier_labels,
                    index=tier_labels.index(default_label),
                    horizontal=True,
                    key=f"tier_radio_{consumable_name}"
                )

            selected_level = name_to_level[selected_label]

            # -----------------------------
            # Buscar linha selecionada
            # -----------------------------
            row = df_consumable[df_consumable["tier_level"] == selected_level]

            if row.empty:
                continue

            row = row.iloc[0]

            # -----------------------------
            # tier anterior
            # -----------------------------
            prev_row = None
            idx = tiers_available.index(selected_level)

            if idx > 0:
                prev_level = tiers_available[idx - 1]
                prev = df_consumable[df_consumable["tier_level"] == prev_level]
                if not prev.empty:
                    prev_row = prev.iloc[0]

            tier_color = TIER_COLORS.get(selected_level, "#374151")

            # -----------------------------
            # Highlight helper
            # -----------------------------
            def h(field):

                if prev_row is None:
                    value = row[field]

                    if isinstance(value, (int, float)):
                        return f"{float(value):.1f}"

                    return str(value)

                value = row[field]
                prev = prev_row[field]

                # textos longos → diff granular
                if isinstance(value, str):
                    return diff_text_granular(value, prev, tier_color)

                # números → round + highlight
                if isinstance(value, (int, float)):
                    value_fmt = f"{float(value):.1f}"
                    prev_fmt = f"{float(prev):.1f}" if isinstance(prev, (int, float)) else prev

                    if value_fmt != prev_fmt:
                        return f"<span style='color:{tier_color}; font-weight:600'>{value_fmt}</span>"

                    return value_fmt

                # fallback
                if value != prev:
                    return f"<span style='color:{tier_color}; font-weight:600'>{value}</span>"

                return str(value)

            # -----------------------------
            # HEADER
            # -----------------------------
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(
                    f"**Tier:** <span style='color:{tier_color}; font-weight:700'>{tier_map[selected_level]}</span>",
                    unsafe_allow_html=True
                )

            # -----------------------------
            # CAMPOS
            # -----------------------------
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Categoria:** {h('consumable_category')}", unsafe_allow_html=True)

            with col2:
                st.markdown(f"**Duração:** {h('consumable_duration')}", unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Efeito:** {h('consumable_effect')}", unsafe_allow_html=True)

            with col2:

                if consumable_type in ("Poções", "Elixires"):
                    st.markdown(f"**Toxicidade:** {h('consumable_toxicity')}", unsafe_allow_html=True)

                elif consumable_type in ("Venenos"):
                    st.markdown(f"**Métodos de Aplicação:** {h('consumable_method')}", unsafe_allow_html=True)

                elif consumable_type in ("Bombas"):
                    st.markdown(f"**Área de Efeito:** {h('consumable_effect_area')}", unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Preço:** {h('consumable_price')} moedas", unsafe_allow_html=True)

            with col2:
                st.markdown(f"**Peso:** {h('consumable_weight')} kg", unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Descrição:**\n\n{h('consumable_description')}", unsafe_allow_html=True)

            with col2:
                st.markdown(f"**Observação:**\n\n{h('consumable_observation')}", unsafe_allow_html=True)

# ------------------------------------------------------------------------------------------------ #
# FUNÇÕES DE VISUALIZAÇÃO DOS CONSUMÍVEIS

def potions(df_dict: dict) -> None:
    """Poções"""

    df = df_dict["db_potions"]

    # Filtros
    with st.expander(f"🎯 Filtros de Poções"):


        df = search_box(
            df=df,
            label=f"🔍 Busca de Poções",
            column="consumable_name"
        )

        filter_config = {
            "Filtrar por Tipo:": {
                "column": "consumable_category",
                "type": "multiselect",
                "default": []
            }
        }

        df, selected_filters = dynamic_filters(df, filter_config)

        if df.empty:
            st.warning(f"Nenhuma poção encontrado com os filtros aplicados.")
            return

    st.markdown("***")

    # Função de visualização
    render_consumable_sub_page(df, "Poções")

def poisons(df_dict: dict) -> None:
    """Venenos"""

    df = df_dict["db_poisons"]

    # Filtros
    with st.expander(f"🎯 Filtros de Venenos"):


        df = search_box(
            df=df,
            label=f"🔍 Busca de Venenos",
            column="consumable_name"
        )

        filter_config = {
            "Filtrar por Tipo:": {
                "column": "consumable_category",
                "type": "multiselect",
                "default": []
            }
        }

        df, selected_filters = dynamic_filters(df, filter_config)

        if df.empty:
            st.warning(f"Nenhuma poção encontrado com os filtros aplicados.")
            return

    st.markdown("***")

    # Função de visualização
    render_consumable_sub_page(df, "Venenos")

def elixirs(df_dict: dict) -> None:
    """Elixires"""

    df = df_dict["db_elixirs"]

    # Filtros
    with st.expander(f"🎯 Filtros de Elixires"):


        df = search_box(
            df=df,
            label=f"🔍 Busca de Elixires",
            column="consumable_name"
        )

        filter_config = {
            "Filtrar por Tipo:": {
                "column": "consumable_category",
                "type": "multiselect",
                "default": []
            }
        }

        df, selected_filters = dynamic_filters(df, filter_config)

        if df.empty:
            st.warning(f"Nenhuma poção encontrado com os filtros aplicados.")
            return

    st.markdown("***")

    # Função de visualização
    render_consumable_sub_page(df, "Elixires")

def bombs(df_dict: dict) -> None:
    """Bombas"""

    df = df_dict["db_bombs"]

    # Filtros
    with st.expander(f"🎯 Filtros de Bombas"):


        df = search_box(
            df=df,
            label=f"🔍 Busca de Bombas",
            column="consumable_name"
        )

        filter_config = {
            "Filtrar por Tipo:": {
                "column": "consumable_category",
                "type": "multiselect",
                "default": []
            }
        }

        df, selected_filters = dynamic_filters(df, filter_config)

        if df.empty:
            st.warning(f"Nenhuma poção encontrado com os filtros aplicados.")
            return

    st.markdown("***")

    # Função de visualização
    render_consumable_sub_page(df, "Bombas")

def consumables() -> None:
    """Itens de alquimia"""

    df_dict = read_excel_data('db_alchemy_consumables.xlsx')

    options = ["Poções", "Venenos", "Elixires", "Bombas"]

    selection = option_menu(
        menu_title=None,
        options=options,
        icons=["1-square-fill", "2-square-fill", "3-square-fill", "4-square-fill"],
        default_index=0,
        orientation="horizontal"
    )

    # Roteamento das páginas
    if selection == options[0]:
        potions(df_dict)
    elif selection == options[1]:
        poisons(df_dict)
    elif selection == options[2]:
        elixirs(df_dict)
    elif selection == options[3]:
        bombs(df_dict)

# ------------------------------------------------------------------------------------------------ #
#FUNÇÃO MAIN

def main():
    consumables()


# ------------------------------------------------------------------------------------------------ #
main()