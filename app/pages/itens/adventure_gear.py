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
from utils import get_project_folder
from app.src.data_loader import read_excel_data
from app.components.filters import format_rules

# ------------------------------------------------------------------------------------------------ #
# FUNÇÕES DE VISUALIZAÇÃO DO STREAMLIT

def adventure_gear(df_dict: dict):
    """
    Renderiza equipamentos de aventura organizados por tipo,
    com expanders aninhados.
    """

    df = df_dict["adventure_gear"]

    st.header("Sobrevivência", divider="grey")

    # Ordenação
    df = df.sort_values(by=["adventure_gear_type", "adventure_gear_id"])

    # ----------- Agrupamento por tipo -----------
    for gear_type in df["adventure_gear_type"].unique():
        df_type = df[df["adventure_gear_type"] == gear_type]

        with st.expander(f"{gear_type} ({len(df_type)})", expanded=False):

            for _, row in df_type.iterrows():
                name = row["adventure_gear_name"]
                price = row["adventure_gear_price"]
                weight = row["adventure_gear_weight"]
                obs = format_rules(row["adventure_gear_observation"])

                with st.expander(name, expanded=False):

                    # ----------- Info principal -----------
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown(f"**💰 Preço:** {int(price)} moedas")

                    with col2:
                        st.markdown(f"**⚖️ Peso:** {weight} kg")

                    # ----------- Observações -----------
                    if obs:
                        st.markdown(obs)

# ------------------------------------------------------------------------------------------------ #
# FUNÇÃO MAIN

def main():

    df_dict = read_excel_data('gear.xlsx')

    options = ["Sobrevivência"]

    selection = option_menu(
        menu_title=None,
        options=options,
        default_index=0,
        orientation='horizontal'
    )

    if selection == options[0]:
        adventure_gear(df_dict)

# ------------------------------------------------------------------------------------------------ #
main()