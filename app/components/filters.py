"""
Script que contém os componentes de filtragem das páginas do projeto.
"""

# ------------------------------------------------------------------------------------------------ #
# IMPORT

import os
import re
import unicodedata
from difflib import SequenceMatcher
import streamlit as st
import pandas as pd
import streamlit as st

# ------------------------------------------------------------------------------------------------ #
# CONSTANTES

utils_directory = os.path.dirname(os.path.dirname(__file__)).rstrip('.')

# ------------------------------------------------------------------------------------------------ #
# FUNÇÕES

def format_rules(rules: str) -> str:
    """
    Formata o texto das regras para melhor exibição em markdown.
    """

    if not isinstance(rules, str):
        return ""

    # Remove aspas extras comuns de CSV/export
    rules = rules.strip().strip('"')

    # Garante quebra de linha correta
    lines = [line.strip() for line in rules.split("\n") if line.strip()]

    # Converte para markdown (lista)
    formatted = "\n".join(lines)

    return formatted

# ------------------------------------------------------------------------------------------------ #
# FUNÇÕES UTILITÁRIAS PARA O STREAMLIT

def dynamic_filters(df: pd.DataFrame, filter_config: dict):
    """
    Aplica filtros dinâmicos em um DataFrame usando componentes do Streamlit.
    Toda vez que um filtro é aplicado, os demais se ajustam de acordo com os
    valores restantes no subconjunto filtrado.

    Args:
        df : pd.DataFrame
            DataFrame original contendo os dados a serem filtrados.

        filter_config : dict
            Dicionário no formato:
            {
                "label_para_ui": {
                    "column": "nome_da_coluna",
                    "type": "multiselect" | "selectbox",
                    "default": []
                    "sort_order": []
                },
                ...
            }

    Return:
        filtered_df : pd.DataFrame
            DataFrame após aplicação de todos os filtros.

        filter_state : dict
            Dicionário contendo os valores selecionados para cada filtro.
    """

    filtered_df = df.copy()
    filter_state = {}

    # Itera sobre filtros na ordem definida
    for filter_label, cfg in filter_config.items():
        col_name = cfg["column"]
        filter_type = cfg.get("type", "multiselect")
        default = cfg.get("default", [])

        raw_values = list(filtered_df[col_name].dropna().unique())

        # Caso haja sort customizado
        custom_sort = cfg.get("sort_order")

        if custom_sort:
            # mantém apenas valores presentes — evita erro se algo não existir no DF
            valid_values = [v for v in custom_sort if v in raw_values]
        else:
            valid_values = sorted(raw_values)

        # Streamlit UI para o filtro
        if filter_type == "multiselect":
            selection = st.multiselect(
                filter_label,
                options=valid_values,
                default=[v for v in default if v in valid_values],
            )

            # aplica o filtro se tiver seleção
            if selection:
                filtered_df = filtered_df[filtered_df[col_name].isin(selection)]

        elif filter_type == "selectbox":
            selection = st.selectbox(
                filter_label,
                options=["(Todos)"] + valid_values,
                index=0
            )

            if selection != "(Todos)":
                filtered_df = filtered_df[filtered_df[col_name] == selection]

        else:
            raise ValueError(f"Unsupported filter type: {filter_type}")

        # Salva o estado do filtro
        filter_state[col_name] = selection

    return filtered_df, filter_state

def sort_ui(df, default_col=None):
    """
    UI para ordenação dinâmica de um DataFrame.

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame base a ser ordenado.
    default_col : str
        Coluna padrão para ordenação caso o usuário não selecione outra.

    Retorno
    -------
    pd.DataFrame
        DataFrame ordenado conforme seleção do usuário.
    """

    st.subheader("Ordenação")

    # Seleciona coluna
    sort_col = st.selectbox("Escolha a coluna para ordenar:", df.columns, index=df.columns.get_loc(default_col) if default_col else 0)

    # Crescente ou decrescente
    ascending = st.radio("Ordem:", ["Crescente", "Decrescente"]) == "Crescente"

    return df.sort_values(by=sort_col, ascending=ascending)

def tag_filter(df, filter_columns):
    """
    Filtro dinâmico baseado em múltiplas colunas do DataFrame.
    Conforme o usuário faz seleções, as demais opções são atualizadas.

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame base a ser filtrado.
    filter_columns : list
        Lista de colunas que serão usadas como filtros.

    Retorno
    -------
    pd.DataFrame
        DataFrame filtrado conforme as escolhas do usuário.
    dict
        Dicionário contendo os valores selecionados para cada filtro.
    """

    st.subheader("Filtros")

    # Armazena seleções do usuário
    selections = {}

    # DataFrame auxiliar que será filtrado a cada passo
    filtered_df = df.copy()

    for col in filter_columns:

        # Ajusta dinamicamente as opções disponíveis
        available_options = sorted(filtered_df[col].dropna().unique())

        # Caixa de seleção dinâmica
        selection = st.multiselect(
            f"Filtrar por {col}:",
            available_options,
            default=None
        )

        selections[col] = selection

        # Aplica filtragem parcial para atualizar opções das próximas colunas
        if selection:
            filtered_df = filtered_df[filtered_df[col].isin(selection)]

    return filtered_df, selections

# ------------------------------------------------------------------------------------------------ #
# FUNÇÕES PARA o SEARCH BOX

def _normalize_text(x: str) -> str:
    if x is None:
        return ""

    x = str(x)

    x = unicodedata.normalize("NFKD", x)
    x = "".join(c for c in x if not unicodedata.combining(c))
    x = re.sub(r"\s+", " ", x).strip().lower()

    return x

def _ensure_search_column(df, column, norm_column):
    if norm_column not in df.columns:
        df = df.copy()
        df[norm_column] = df[column].astype(str).apply(_normalize_text)
    return df

def _fuzzy_score(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def search_box(
    df,
    label="🔍 Buscar",
    column="nome",
    norm_column="_search_norm",
    fuzzy_threshold=0.6,
    max_suggestions=20,
):
    """
    Busca híbrida robusta:
    - substring
    - fuzzy
    - ignora acentos
    - ignora espaços
    - NÃO quebra se esquecer de preparar df
    """

    df = _ensure_search_column(df, column, norm_column)

    termo = st.text_input(label)

    if termo:
        termo_norm = _normalize_text(termo)

        mask_sub = df[norm_column].str.contains(termo_norm, na=False)

        fuzzy_scores = df[norm_column].apply(lambda x: _fuzzy_score(termo_norm, x))
        mask_fuzzy = fuzzy_scores >= fuzzy_threshold

        mask = mask_sub | mask_fuzzy
        filtered = df[mask]

        suggestions = (
            filtered.assign(_score=fuzzy_scores)
            .sort_values("_score", ascending=False)[column]
            .dropna()
            .unique()
            .tolist()
        )

        if suggestions:
            st.caption("Sugestões:")
            st.write(", ".join(suggestions[:max_suggestions]))
        else:
            st.caption("Nenhuma sugestão encontrada.")

        return filtered

    return df

# ------------------------------------------------------------------------------------------------ #
# FUNÇÕES DE HIGHLIGHT DE TEXTO.

def diff_text_granular(current, previous, color):
    """
    Highlight palavra a palavra preservando quebras de linha.
    """

    if previous is None:
        return str(current)

    current_lines = str(current).splitlines()
    prev_lines = str(previous).splitlines()

    result_lines = []

    for i, line in enumerate(current_lines):

        prev_line = prev_lines[i] if i < len(prev_lines) else ""

        if line == prev_line:
            result_lines.append(line)
            continue

        # diff palavra a palavra
        words_current = line.split(" ")
        words_prev = prev_line.split(" ")

        matcher = SequenceMatcher(None, words_prev, words_current)

        new_line_parts = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():

            segment = " ".join(words_current[j1:j2])

            if tag in ("replace", "insert"):
                if segment:
                    segment = f"<span style='color:{color}; font-weight:600'>{segment}</span>"

            new_line_parts.append(segment)

        result_lines.append(" ".join(new_line_parts))

    return "\n".join(result_lines)
