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

# ------------------------------------------------------------------------------------------------ #
# FUNÇÕES AUXILIARES DAS REGRAS

# Helpers
def round_half_up(x: float) -> int:
    return int(math.floor(x + 0.5))

def tier_limit_for_nh(nh: int, tier: str) -> int:
    cfg = TIER_CONFIG[tier]

    if nh < cfg["min_nh"]:
        return 0

    return round_half_up(nh / cfg["divisor"])

def limits_for_nh(nh: int) -> dict:
    return {t: tier_limit_for_nh(nh, t) for t in TIER_ORDER}

# Tabela
def tb_tier_limits(nh_min=None, nh_max=30):

    if nh_min is None:
        nh_min = min(cfg["min_nh"] for cfg in TIER_CONFIG.values())

    rows = []

    for nh in range(nh_min, nh_max + 1):

        row = {"NH": nh}
        row.update(limits_for_nh(nh))

        rows.append(row)

    return pd.DataFrame(rows)

# ------------------------------------------------------------------------------------------------ #
# FUNÇÕES DE VISUALIZAÇÃO DAS REGRAS

def render_tier_limits_panel():

    st.subheader("Fabricação por NH do Alquimista", divider="grey")

    # -------------------------------------------------
    # tabela completa

    df = tb_tier_limits()

    # -------------------------------------------------
    # usar nomenclatura fixa: qualidade

    name_set = TIER_NAME_SETS["qualidade"]

    # 👉 aplica nomes na tabela completa também
    df = df.rename(columns=name_set)

    # -------------------------------------------------
    # NH selecionado

    nh_min = min(cfg["min_nh"] for cfg in TIER_CONFIG.values())

    nh = st.number_input(
        "NH do alquimista",
        min_value=nh_min,
        max_value=30,
        value=12,
        step=1
    )

    # -------------------------------------------------
    # limites calculados

    limits = limits_for_nh(nh)

    # somente tiers permitidos
    allowed_tiers = [
        t for t in TIER_ORDER
        if nh >= TIER_CONFIG[t]["min_nh"]
    ]

    st.markdown("### **Limite para este NH**")

    # dataframe com nomes corretos no header
    df_limits = pd.DataFrame([
        {t: limits[t] for t in allowed_tiers}
    ])

    df_limits.rename(columns=name_set, inplace=True)

    st.dataframe(
        df_limits,
        width='stretch',
        hide_index=True
    )

    # -------------------------------------------------
    # tabela completa

    with st.expander("Tabela completa", expanded=False):
        st.dataframe(df, width='stretch', hide_index=True)

def render_fabrication_rules() -> None:
    """
    Renderiza as regras de fabricação de poções.
    """

    st.subheader("Resultados na Fabricação de Consumíveis Alquímicos", divider="grey")

    # ✅ SUCESSO
    with st.expander("✅ Sucesso", expanded=False):
        st.markdown("""
- O consumível é produzido exatamente na qualidade escolhida, conforme a **NH** do alquimista.
        """)

    # ✨ ACERTO CRÍTICO
    with st.expander("✨ Acerto Crítico", expanded=False):
        st.markdown("""

A produção é realizada com precisão excepcional, superando as capacidades normais do alquimista.

- **50% de chance** (3 números à escolha do Mestre e/ou jogador):
  ➝ O consumível é criado com qualidade **1 tier acima** da NH.

- **50% de chance** (3 números):
  ➝ São produzidas **maiores quantidades** do consumível (dobro, triplo etc.), conforme decisão do Mestre.

📌 **Caso o alquimista possua NH para qualidade Obra-Prima**

- Mestre e jogador podem decidir o resultado automaticamente, sem necessidade de rolagem.

- Se houver subida de tier a partir de **Obra-Prima**, o consumível se torna de qualidade **Única**, recebendo:
  - Seu efeito normal de Obra-Prima;
  - +1 efeito benéfico adicional coerente com sua categoria.

**Exemplo:**
Uma poção de vida não pode conceder invisibilidade, mas pode fornecer resistência a dano ou venenos.
A decisão final sobre o efeito bônus cabe ao Mestre.

        """)

    # ❌ FALHA
    with st.expander("❌ Falha", expanded=False):
        st.markdown("""

Caso o alquimista falhe no teste de criação do consumível, role **1d6** para determinar o resultado:

📌 **Resultado Padrão**

- **50% de chance** (3 números à escolha do Mestre e/ou jogador):
  ➝ O consumível falha e os ingredientes são perdidos.

- **50% de chance** (3 números):
  ➝ O consumível decai **1 tier** em qualidade.

📌 **Caso o alquimista só possa produzir qualidade **Comum****

A redução de tier **não se aplica**.

- **70% de chance** (4 números):
  ➝ O consumível falha e os ingredientes são perdidos.

- **30% de chance** (2 números):
  ➝ Ocorre uma consequência desastrosa (ver *Erro Crítico*).

        """)

    # 💥 ERRO CRÍTICO
    with st.expander("💥 Erro Crítico", expanded=False):
        st.markdown("""

O consumível se torna instável durante a fabricação, gerando um resultado geralmente desastroso.

- **70% de chance** (4 números à escolha do Mestre e/ou jogador):
  ➝ Consequência catastrófica (explosão, nuvem nociva com efeito negativo do consumível ou outro efeito decidido pelo Mestre).

- **30% de chance** (2 números):
  ➝ O consumível falha e os ingredientes são perdidos.

        """)

def alchemy_rules() -> None:

    render_tier_limits_panel()

    st.markdown("***")

    render_fabrication_rules()

def toxicity_rules() -> None:
    """
    Renderiza as regras de Toxicidade.
    """

    st.subheader("Regras de Toxicidade", divider="grey")

    # 📊 CONCEITO E CÁLCULO
    st.markdown(r"""

        A **Toxicidade** representa o limite fisiológico do personagem para consumir substâncias alquímicas sem sofrer efeitos adversos.

        Ela é calculada pela fórmula:

        $$
        \text{Toxicidade} = \frac{HT \times 4 + IQ \times 3 + ST \times 3}{3}
        $$

        Sendo:

        - $HT$ = Vitalidade
        - $IQ$ = Inteligência
        - $ST$ = Força

    """)

    with st.expander("Exemplo"):
        st.markdown(r"""
            Se um personagem possui:

            $$
            HT = 12
            $$

            $$
            IQ = 11
            $$

            $$
            ST = 10
            $$

            Então:

            $$
            \text{Toxicidade} = \frac{(12 \times 4) + (11 \times 3) + (10 \times 3)}{3}
            $$

            $$
            \text{Toxicidade} = \frac{48 + 33 + 30}{3}
            $$

            $$
            \text{Toxicidade} = \frac{90}{3} = 30
            $$
        """)

    # ♻️ RECUPERAÇÃO
    with st.expander("♻️ Recuperação de Toxicidade", expanded=False):
        st.markdown("""
- A recuperação natural é de **1 ponto a cada 30 minutos**.
- A toxicidade **só começa a decair após todos os efeitos de poções e elixires terminarem**.
- Existem consumíveis específicos capazes de **eliminar toxicidade** diretamente.
        """)

    # ⚠️ EFEITOS POR PERCENTUAL
    with st.expander("⚠️ Efeitos por Percentual de Toxicidade", expanded=False):
        st.markdown("""
Os efeitos negativos variam conforme o percentual atual de toxicidade em relação ao limite máximo do personagem:

- **100% a 50%**
  ➝ Nenhuma consequência.

- **49% a 25%**
  ➝ Perda de **1 ponto de vida por hora**, até que a toxicidade seja eliminada.

- **24% a 1%**
  ➝ Perda de **2 pontos de vida por hora**, até que a toxicidade seja eliminada.

- **0%**
  ➝ Quando todos os efeitos que causam toxicidade cessarem:
    - O personagem fica **inconsciente**;
    - Perde **4 pontos de vida a cada 2 horas**, até que a toxicidade seja eliminada.
        """)

# ------------------------------------------------------------------------------------------------ #
#FUNÇÃO MAIN

def main():

    options = ["Regras", "Toxicidade"]

    selection = option_menu(
        menu_title=None,
        options=options,
        default_index=0,
        orientation='horizontal'
    )

    # Roteamento das páginas
    if selection == options[0]:
        alchemy_rules()
    elif selection == options[1]:
        toxicity_rules()

# ------------------------------------------------------------------------------------------------ #
main()