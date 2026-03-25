# ------------------------------------------------------------------------------------------------ #
# IMPORTS

import os
import streamlit as st
import pandas as pd
import warnings
from streamlit_option_menu import option_menu
warnings.simplefilter(action='ignore', category=UserWarning)

# RELATIVE IMPORTS
from app.src.data_loader import read_excel_data
from app.components.filters import dynamic_filters, search_box

# ------------------------------------------------------------------------------------------------ #
#   FUNÇÕES DE VISUALIZAÇÃO DO STREAMLIT

def skills_cost_in_points(df_skills: dict, df_magic_rules: dict) -> None:
    """
    Função simples que exibe um as regras de custo em pontos e aperfeiçoamento de perícias.
    """

    spell_levels = "spell_level"
    skills_mental = "mental"

    st.subheader("Aprendendo Feitiços", divider="grey")

    # ----------------------------------------------------------------------------------------- #
    # 1 - REGRAS E CUSTOS DOS NÍVEIS DE HABILIDADE QUANTO SUA CATEGORIA
    # ----------------------------------------------------------------------------------------- #

    with st.expander("Custo em pontos dos Feitiços"):

        df_mental = df_skills[skills_mental]
        df_mental.rename(columns={"skill_final_level": "Nível de Habilidade"}, inplace=True)

        st.dataframe(df_mental, width='stretch', hide_index=True)

    # ----------------------------------------------------------------------------------------- #
    # 1.1 SIGNIFICADO DO NÍVEL DE HABILIDADE COM AS PERÍCIAS
    # ----------------------------------------------------------------------------------------- #

    with st.expander("O que seu nível de habilidade em um feitiço significa?"):

        df_overview = df_magic_rules[spell_levels]

        # Cabeçalho (fora do loop)
        col1, col2, col3, col4 = st.columns(4)
        col1.markdown("**Nível de Habilidade (NH)**")
        col2.markdown("**Nomenclatura do NH**")
        col3.markdown("**Movimento permitido ao concentrar**")
        col4.markdown("**Forma de lançar o feitiço**")

        st.divider()

        # Linhas
        for _, row in df_overview.iterrows():
            col1, col2, col3, col4 = st.columns(4)
            col1.write(row["spell_skill_level_range"])
            col2.write(row["spell_skill_level"])
            col3.write(row["movement_allowed_while_concentrating"])
            col4.write(row["spell_cast_form"])

# ------------------------------------------------------------------------------------------------ #
#FUNÇÃO MAIN

def main():
    """
    Página principal que cria um menu lateral para seleção entre
    o grimório e a visão simples dos arquétipos.
    """

    df_skills = read_excel_data('skills.xlsx')
    df_magic_rules = read_excel_data('magic_rules.xlsx')

    options = ["Aprendizado", "Alcance e Forma"]

    with st.sidebar:
        selection = option_menu(
            menu_title=None,
            options=options,
            icons=["book", "list-ul"],
            default_index=0
        )

    # Roteamento das páginas
    if selection == options[0]:
        skills_cost_in_points(df_skills, df_magic_rules)
    elif selection == options[1]:
        pass

# ------------------------------------------------------------------------------------------------ #
main()