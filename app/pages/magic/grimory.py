# ------------------------------------------------------------------------------------------------ #
# IMPORTS

import streamlit as st
import pandas as pd

import warnings
from streamlit_option_menu import option_menu
warnings.simplefilter(action='ignore', category=UserWarning)

# RELATIVE IMPORTS
from app.utils import TIER_CONFIG, TIER_COLORS, TIER_ORDER, TIER_NAME_SETS
DEFAULT_TIER_SET = "habilidade"

from app.src.data_loader import read_excel_data
from app.components.filters import dynamic_filters, search_box, diff_text_granular

# ------------------------------------------------------------------------------------------------ #
# CONSTANTES

arcanum_dict = {

    "Arcano Fundamental": {
        "Arcanomancia": {
            "tipo": "Arcano",
            "cor":  "#2dd4bf",
            "is_proibida": "Não"
        }
    },

    "Cinêtico": {
        "Sonoromancia": {"tipo": "Som", "cor": "#f472b6", "is_proibida": "Não"},
        "Kinetomancia": {"tipo": "Movimento", "cor": "#10b981", "is_proibida": "Não"}
    },

    "Cognitivo": {
        "Psiquemancia": {"tipo": "Mente", "cor": "#06b6d4", "is_proibida": "Sim"},
        "Eidomancia": {"tipo": "Ilusão", "cor": "#c084fc", "is_proibida": "Sim"},
    },

    "Corporal": {
        "Somatomancia": {"tipo": "Corpo", "cor": "#f2d6c9", "is_proibida": "Não"},
        "Hemomancia": {"tipo": "Sangue", "cor": "#b91c1c", "is_proibida": "Sim"},
    },

    "Dimensional": {
        "Espaciomancia": {"tipo": "Espaço", "cor": "#6366f1", "is_proibida": "Sim"},
        "Cronomancia": {"tipo": "Tempo", "cor": "#f59e0b", "is_proibida": "Sim"}
    },

    "Elemental": {
        "Aeromancia": {"tipo": "Ar", "cor": "#22c55e", "is_proibida": "Não"},
        "Hidromancia": {"tipo": "Água", "cor": "#3b82f6", "is_proibida": "Não"},
        "Piromancia": {"tipo": "Fogo", "cor": "#ef4444", "is_proibida": "Não"},
        "Geomancia": {"tipo": "Terra", "cor": "#eab308", "is_proibida": "Não"},
        "Eletromancia": {"tipo": "Eletricidade", "cor": "#a855f7", "is_proibida": "Não"}
    },

    "Espiritual": {
        "Hagiomancia": {"tipo": "Sagrado", "cor": "#facc15", "is_proibida": "Não"},
        "Necromancia": {"tipo": "Necro", "cor": "#7c3aed", "is_proibida": "Sim"}
    },

    "Natural": {
        "Fitomancia": {"tipo": "Flora", "cor": "#16a34a", "is_proibida": "Não"},
        "Zoomancia": {"tipo": "Fauna", "cor": "#f97316", "is_proibida": "Não"},
    },

    "Vocacional": {
        "Melomancia": {"tipo": "Bardo", "cor": "#fb7185", "is_proibida": "Não"},
        "Imbuomancia": {"tipo": "Encantamento", "cor": "#a855f7", "is_proibida": "Não"},
        "Restauromancia": {"tipo": "Restauração", "cor": "#f472b6", "is_proibida": "Não"},
        "Umbromancia": {"tipo": "Sombra", "cor": "#1f2937", "is_proibida": "Não"},
    },


}

# ------------------------------------------------------------------------------------------------ #
# FUNÇÕES AUXILIARES

def render_arcano_card(
    nome: str,
    data: dict,
    expanded: bool = False,
    use_columns: bool = True
):
    """
    Renderiza um card padrão de arcano/escola com expander de detalhes.
    """

    base = data.get("cor", "#6366f1")

    def _render():
        st.html(f"""
        <div style="
            padding:14px;
            border-radius:14px;
            border:1px solid #37415130;
            margin-bottom:6px;
            transition: all 0.2s ease;

            color: #ffffff;

            background:
                linear-gradient(145deg, {base}55, #020617 60%),
                linear-gradient(145deg, #020617, #0f172a);

            box-shadow: 0 0 18px {base}55;
        "
        onmouseover="this.style.boxShadow='0 0 28px {base}aa'"
        onmouseout="this.style.boxShadow='0 0 18px {base}55'"
        >

            <div style="
                font-weight:700;
                font-size:18px;
                text-align:center;
            ">
                ✴ {nome}
            </div>

            <div style="
                margin-top:6px;
                font-size:13px;
                opacity:0.75;
                letter-spacing:1px;
                text-align:center;
            ">
                {data.get("tipo", "").upper()}
            </div>

        </div>
        """)

        with st.expander(f"Ver detalhes de {nome}", expanded=expanded):
            st.write(f"Descrição futura de {nome}...")

    if use_columns:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            _render()
    else:
        _render()

# CACHE: preprocessamento
@st.cache_data
def _preprocess_spells(df_spells: pd.DataFrame, tier_set: str):
    df = df_spells.copy().fillna("")

    tier_map = TIER_NAME_SETS[tier_set]
    name_to_level = {v: k for k, v in tier_map.items()}

    df["tier_level"] = (
        df["spell_tier"]
        .astype(str)
        .str.strip()
        .map(name_to_level)
    )

    df["tier_level"] = pd.Categorical(
        df["tier_level"],
        categories=TIER_ORDER,
        ordered=True
    )

    return df, tier_map, name_to_level

# CACHE: indexação completa
@st.cache_data
def _build_spell_index(df: pd.DataFrame):
    spell_index = {}

    for spell_type, df_type in df.groupby("spell_type"):

        spells_dict = {}

        for spell_name, df_spell in df_type.groupby("spell_box_name"):

            df_spell = df_spell.sort_values("tier_level").reset_index(drop=True)

            # tiers disponíveis
            tiers = sorted(
                int(t) for t in df_spell["tier_level"].dropna().unique()
            )

            # index por tier (ACESSO O(1))
            tier_rows = {
                int(row["tier_level"]): row
                for _, row in df_spell.iterrows()
            }

            spells_dict[spell_name] = {
                "df": df_spell,
                "tiers": tiers,
                "rows": tier_rows,
            }

        spell_index[spell_type] = spells_dict

    return spell_index

def _format_field(value, prev, color):
    if prev is None:
        if isinstance(value, (int, float)):
            return f"{float(value):.1f}"
        return str(value)

    if isinstance(value, str):
        return diff_text_granular(value, prev, color)

    if isinstance(value, (int, float)):
        value_fmt = f"{float(value):.1f}"
        prev_fmt = f"{float(prev):.1f}" if isinstance(prev, (int, float)) else prev

        if value_fmt != prev_fmt:
            return f"<span style='color:{color}; font-weight:600'>{value_fmt}</span>"

        return value_fmt

    if value != prev:
        return f"<span style='color:{color}; font-weight:600'>{value}</span>"

    return str(value)

def render_spells_grimory(
    school: str,
    df_spells: pd.DataFrame,
    tier_set: str = DEFAULT_TIER_SET):

    st.subheader(f"2️⃣ Feitiços de {school}", divider="grey")

    # 🔥 cache pesado
    df, tier_map, name_to_level = _preprocess_spells(df_spells, tier_set)
    spell_index = _build_spell_index(df)

    spell_types = sorted(spell_index.keys())

    for i, spell_type in enumerate(spell_types):

        if i > 0:
            st.divider()

        with st.expander(f"{spell_type}"):

            spells_dict = spell_index[spell_type]

            # ordenação por menor id (uma vez só)
            ordered_spells = sorted(
                spells_dict.keys(),
                key=lambda name: spells_dict[name]["df"]["spell_id"].min()
            )

            for spell_name in ordered_spells:

                data = spells_dict[spell_name]
                tiers_available = data["tiers"]

                if not tiers_available:
                    continue

                expanded_default = spell_name == "MOLDAR MANA | F"

                with st.expander(spell_name, expanded=expanded_default):

                    tier_labels = [tier_map[t] for t in tiers_available]

                    default_level = 1 if 1 in tiers_available else tiers_available[0]
                    default_label = tier_map[default_level]

                    # 🔥 sem try/except
                    selected_label = st.segmented_control(
                        "Tier",
                        options=tier_labels,
                        default=default_label,
                        key=f"tier_{spell_name}"
                    )

                    selected_level = name_to_level[selected_label]

                    row = data["rows"][selected_level]

                    idx = tiers_available.index(selected_level)
                    prev_row = None

                    if idx > 0:
                        prev_level = tiers_available[idx - 1]
                        prev_row = data["rows"].get(prev_level)

                    tier_color = TIER_COLORS.get(selected_level, "#374151")

                    def h(field):
                        prev_val = prev_row[field] if prev_row is not None else None
                        return _format_field(row[field], prev_val, tier_color)

                    # HEADER

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown(
                            f"**Tier:** <span style='color:{tier_color}; font-weight:700'>{tier_map[selected_level]}</span>",
                            unsafe_allow_html=True
                        )

                    with col2:
                        st.markdown(
                            f"**Dificuldade:** {h('spell_difficulty')}",
                            unsafe_allow_html=True
                        )

                    with col3:
                        try:
                            cost = int(float(row["spell_cost"]))
                        except:
                            cost = 0

                        st.markdown(f"**Custo de Mana:** {cost}")

                    # CAMPOS
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown(f"**Categoria:** {h('spell_type')}", unsafe_allow_html=True)

                    with col2:
                        st.markdown(f"**Tempo de Cast:** {h('spell_cast_time')}", unsafe_allow_html=True)

                    with col3:
                        st.markdown(f"**Duração:** {h('spell_duration')}", unsafe_allow_html=True)

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown(f"**Alcance:** {h('spell_range')}", unsafe_allow_html=True)

                    with col2:
                        st.markdown(f"**Tipo do Alvo:** {h('spell_target_type')}", unsafe_allow_html=True)

                    with col3:
                        st.markdown(f"**Área de Efeito:** {h('spell_effect_area')}", unsafe_allow_html=True)

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown(f"**Dimensionamento:** {h('spell_scaling')}", unsafe_allow_html=True)

                    with col2:
                        st.markdown(f"**Pré-Requisitos:** {h('spell_requirements')}", unsafe_allow_html=True)

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown(f"**Descrição:**\n\n{h('spell_description')}", unsafe_allow_html=True)

                    with col2:
                        st.markdown(f"**Observação:**\n\n{h('spell_observation')}", unsafe_allow_html=True)

# ------------------------------------------------------------------------------------------------ #
# FUNÇÕES DE VISUALIZAÇÃO DO STREAMLIT

def grimory(df_dict: dict):

    st.header("Grimório", divider="grey")

    @st.cache_data
    def build_escola_categoria_map(arcanum_dict):
        return {
            escola: categoria
            for categoria, archetypes in arcanum_dict.items()
            for escola in archetypes.keys()
        }

    escola_para_categoria = build_escola_categoria_map(arcanum_dict)

    # Filtrar apenas escolas presentes no df_dict
    categorias_disponiveis = {}

    for escola in df_dict.keys():

        categoria = escola_para_categoria.get(escola, "Outros")

        if categoria not in categorias_disponiveis:
            categorias_disponiveis[categoria] = []

        categorias_disponiveis[categoria].append(escola)

    if not categorias_disponiveis:
        st.warning("Nenhuma escola disponível no grimório.")
        return

    # ordenar
    categorias_disponiveis = {
        k: sorted(v) for k, v in sorted(categorias_disponiveis.items())
    }

    # SELECT: ARQUÉTIPO
    selected_categoria = st.selectbox(
        "Selecione um arquétipo:",
        list(categorias_disponiveis.keys())
    )

    # SELECT: ESCOLA
    escolas_categoria = categorias_disponiveis[selected_categoria]

    selected_escola = st.selectbox(
        "Selecione uma escola:",
        escolas_categoria
    )

    # DATAFRAME
    df = df_dict[selected_escola].fillna('')

    # Buscar dados da escola
    escola_data = arcanum_dict.get(selected_categoria, {}).get(
        selected_escola,
        {"cor": "#6366f1", "tipo": "Desconhecido"}
    )

    # HEADER CUSTOM
    render_arcano_card(
        selected_escola,
        escola_data,
        expanded=False,
        use_columns=False
    )

    st.markdown("***")

    # FILTROS
    st.subheader("1️⃣ Filtros de Feitiços", divider='grey')

    with st.expander("Expandir Filtros"):

        df = search_box(
            df=df,
            label="🔍 Busca de Feitiços",
            column="spell_name"
        )

        filter_config = {
            "Filtrar por Tipo:": {
                "column": "spell_type",
                "type": "multiselect",
                "default": []
            },
            "Filtrar por Dificuldade:": {
                "column": "spell_difficulty",
                "type": "multiselect",
                "default": [],
                "sort_order": ["F", "M", "D", "MD"]
            }
        }

        df, selected_filters = dynamic_filters(df, filter_config)

        if df.empty:
            st.warning("Nenhum feitiço encontrado com os filtros aplicados.")
            return

    # RENDER SPELLS
    render_spells_grimory(selected_escola, df)

def archetype_overview():

    # ITERAR POR ARQUÉTIPOS
    st.subheader("📂 Arquétipos", divider='grey')

    for categoria, archetypes in arcanum_dict.items():

        with st.expander(f"{categoria}"):

            st.markdown("🔮 Escolas:")

            archetypes_list = list(archetypes.items())
            blocks_per_row = 2

            for i in range(0, len(archetypes_list), blocks_per_row):

                row = archetypes_list[i:i + blocks_per_row]
                cols = st.columns(blocks_per_row)

                for idx in range(len(row)):

                    nome, data = row[idx]

                    with cols[idx]:
                        render_arcano_card(
                            nome,
                            data,
                            expanded=False,
                            use_columns=False  # 🔥 importante: evita colunas internas
                        )

# ------------------------------------------------------------------------------------------------ #
# FUNÇÃO MAIN

def main():
    """
    Página principal que cria um menu lateral para seleção entre
    o grimório e a visão simples dos arquétipos.
    """

    df_dict = read_excel_data('grimory.xlsx')

    options = ["Arquétipos", "Grimório"]

    with st.sidebar:
        selection = option_menu(
            menu_title=None,
            options=options,
            icons=["book", "list-ul"],
            default_index=0,
        )

    # Roteamento das páginas
    if selection == options[0]:
        archetype_overview()
    elif selection == options[1]:
        grimory(df_dict)

# ------------------------------------------------------------------------------------------------ #
main()
