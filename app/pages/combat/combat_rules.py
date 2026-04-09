# ------------------------------------------------------------------------------------------------ #
# IMPORTS

import os
import math
import streamlit as st
import pandas as pd

import warnings
from streamlit_option_menu import option_menu
warnings.simplefilter(action='ignore', category=UserWarning)

# RELATIVE IMPORTS
from utils import get_project_folder
from app.src.data_loader import read_excel_data
from app.components.filters import format_rules

assets_folder = get_project_folder('assets')

# ------------------------------------------------------------------------------------------------ #
# FUNÇÕES AUXILIARES

def render_impact_points(df: pd.DataFrame):
    """
    Renderiza pontos de impacto organizados por região do corpo,
    usando apenas expanders.
    """

    def classify_target(target: str) -> str:
        t = target.lower()

        if any(x in t for x in ["cérebro", "olho", "face"]):
            return "Cabeça"
        elif "garganta" in t:
            return "Pescoço"
        elif "tronco" in t:
            return "Tronco"
        elif any(x in t for x in ["coração", "pulmões", "rins"]):
            return "Órgãos Vitais"
        elif any(x in t for x in ["braço", "mão"]):
            return "Membros Superiores"
        elif "virilha" in t:
            return "Virilha"
        elif any(x in t for x in ["perna", "pé"]):
            return "Membros Inferiores"
        elif "frestas" in t:
            return "Especial"
        else:
            return "Outros"

    df["categoria"] = df["target"].apply(classify_target)

    body_order = [
        "Cabeça",
        "Pescoço",
        "Tronco",
        "Órgãos Vitais",
        "Membros Superiores",
        "Virilha",
        "Membros Inferiores",
        "Outros",
        "Especial",
    ]

    df["ordem"] = df["categoria"].apply(lambda x: body_order.index(x))
    df = df.sort_values(by=["ordem", "target_reductor"])

    st.subheader("Detalhamento dos Pontos de Impacto")

    for categoria in body_order:
        df_cat = df[df["categoria"] == categoria]

        if df_cat.empty:
            continue

        with st.expander(f"{categoria}", expanded=False):

            for _, row in df_cat.iterrows():
                target = row["target"]
                reductor = row["target_reductor"]
                obs = format_rules(row["target_observations"])

                with st.expander(f"{target} ({reductor})", expanded=False):
                    st.markdown(obs)

def get_distance_multiplier(df_distance, peso):
    """
    Retorna o multiplicador de distância baseado no peso.
    """

    peso_floor = math.floor(peso)

    # garante ordenação
    df_distance = df_distance.sort_values(by="object_weigth")

    # pega o maior peso <= peso_floor
    df_valid = df_distance[df_distance["object_weigth"] <= peso_floor]

    if df_valid.empty:
        return None

    return df_valid.iloc[-1]["object_throw_distance"]

def get_damage(df_damage, st, peso):
    """
    Retorna o dano baseado na ST e peso.
    """

    row = df_damage[df_damage["ST"] == st]

    if row.empty:
        return "-"

    row = row.iloc[0]

    if peso <= 5:
        return row["0.25_to_5"]
    elif peso <= 25:
        return row["5_to_25"]
    elif peso <= 50:
        return row["25_to_50"]
    else:
        return row["50_plus"]

def throw_simulator(df_distance, df_damage):

    st.subheader("Simulador de Arremesso")

 # ----------- Inputs -----------
    st_value = st.slider("ST", 5, 20, 10)

    peso = st.number_input(
        "Peso do objeto (kg)",
        min_value=0.25,
        value=1.0,
        step=0.25
    )

    has_skill = st.checkbox("Possui perícia Arremesso?")

    skill = st.number_input(
        "Nível da perícia",
        min_value=1,
        value=12,
        disabled=not has_skill
    )

    st.markdown("> ⚠️ A perícia Arremesso aumenta a distância, mas não o dano diretamente.")

    # ----------- Cálculo -----------
    st_effective = st_value + (skill / 6 if has_skill else 0)

    base_distance = get_distance_multiplier(df_distance, peso)

    if base_distance is None:
        st.warning("Peso fora da tabela")
        return

    distancia_final = base_distance * st_effective
    dano = get_damage(df_damage, st_value, peso)

    # ----------- Resultado -----------
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Distância Máxima (m)", f"{distancia_final:.2f}")

    with col2:
        st.metric("Dano", dano)

    # ----------- Debug opcional (ajuda muito) -----------
    with st.expander("Detalhes do cálculo"):
        st.write(f"Peso arredondado: {math.floor(peso)} kg")
        st.write(f"Multiplicador base: {base_distance}")
        st.write(f"ST efetiva: {st_effective:.2f}")

# ------------------------------------------------------------------------------------------------ #
#   FUNÇÕES DE VISUALIZAÇÃO DO STREAMLIT

def manuvers(df_dict: dict, n_cols: int = 2):
    """
    Renderiza as manobras disponíveis a partir de um dict de dataframes.

    Args:
    - df_dict: dict onde a chave é o nome do conjunto e o valor é o dataframe de manobras
    """

    df = df_dict['maneuvers']

    # Ordenação opcional
    df = df.sort_values(by="manuver_id").reset_index(drop=True)

    # Exibição
    st.header("Manobras", divider='grey')

    for i in range(0, len(df), n_cols):
        cols = st.columns(n_cols)

        for j in range(n_cols):
            if i + j < len(df):
                row = df.iloc[i + j]
                with cols[j]:
                    with st.expander(row["manuver_name"]):
                        st.markdown(format_rules(row["manuver_rules"]))

def impact_points(df_dict: dict):
    """
    Página completa:
    - imagem + redutores lado a lado
    - lista detalhada (expanders)
    """

    df = df_dict['impact_points']
    image_path = os.path.join(assets_folder, "impact_points.png")

    # ----------- Topo: imagem + redutores -----------
    col1, col2 = st.columns([1, 1])

    with col1:
        st.image(image_path, caption="Referência de redutores por parte do corpo")

    with col2:
        st.subheader("Redutores por Local")

        df_sorted = df.sort_values(by="target_reductor")

        for _, row in df_sorted.iterrows():
            target = row["target"]
            reductor = row["target_reductor"]

            if reductor <= -7:
                color = "#8B0000"
            elif reductor <= -5:
                color = "#B22222"
            elif reductor <= -3:
                color = "#CD5C5C"
            else:
                color = "#444"

            st.markdown(
                f"""
                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                    padding:6px 10px;
                    border-bottom:1px solid #333;
                ">
                    <span>{target}</span>
                    <span style="
                        background:{color};
                        color:white;
                        padding:2px 8px;
                        border-radius:6px;
                        font-size:12px;
                    ">
                        {reductor}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.divider()

    # ----------- Lista detalhada -----------
    render_impact_points(df)

def combat_info(df_dict: dict):
    """
    Renderiza informações gerais de combate em expanders.
    """

    df = df_dict['combat']

    # Ordenação opcional (caso tenha coluna futura tipo ID)
    df = df.reset_index(drop=True)

    st.header("Informações de Combate", divider='grey')

    for _, row in df.iterrows():
        title = row["combat_info"]
        description = format_rules(row["combat_info_description"])

        with st.expander(title):
            st.markdown(description)

def throw_rules(df_dict: dict):

    st.header("Arremesso", divider="grey")

    df_distance = df_dict["throw_distance"]
    df_damage = df_dict["throw_damage"]

    col1, col2 = st.columns(2)

    with col1:
        with st.expander("Tabela de Distância"):
            st.dataframe(df_distance, width='stretch', hide_index=True)

    with col2:
        with st.expander("Tabela de Dano"):
            st.dataframe(df_damage, width='stretch', hide_index=True)

    st.divider()

    throw_simulator(df_distance, df_damage)

# ------------------------------------------------------------------------------------------------ #
#FUNÇÃO MAIN

def main():
    df_dict = read_excel_data('combat_rules.xlsx')

    options = ["Informações", "Manobras", "Locais de Acerto", "Arremesso"]

    selection = option_menu(
        menu_title=None,
        options=options,
        default_index=0,
        orientation="horizontal"
    )

    # Roteamento das páginas
    if selection == options[0]:
        combat_info(df_dict)
    elif selection == options[1]:
        manuvers(df_dict)
    elif selection == options[2]:
        impact_points(df_dict)
    elif selection == options[3]:
        throw_rules(df_dict)

# ------------------------------------------------------------------------------------------------ #
main()