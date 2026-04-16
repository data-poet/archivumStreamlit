
# ------------------------------------------------------------------------------------------------ #
# IMPORT
import os
import re
import logging
import pandas as pd
import streamlit as st
from r4ven_utils.log4me import r4venLogManager

# RELATIVE IMPORTS
from utils import get_project_folder

# ------------------------------------------------------------------------------------------------ #
# CONSTANTES

logs_folder = get_project_folder('app')
data_folder = get_project_folder('data')

# ------------------------------------------------------------------------------------------------ #
# FUNÇÕES UTILITÁRIAS PARA MANIPULAÇÃO DE TABELAS

def filter_sheet_names(sheet_list: list, exclude_list: list) -> list:
    """
    Filtra da lista todas as sheet_names contidas na exclude_list.
    Retorna a lista limpa de abas que o usuário poderá selecionar.
    """
    return [s for s in sheet_list if s not in exclude_list]

def _normalize_string(value):
        if not isinstance(value, str):
            return value

        # remove múltiplas quebras no início → mantém só 1
        value = re.sub(r'^\n+', '\n', value)

        return value

def clean_dataframe(df):
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str)
    return df

# ------------------------------------------------------------------------------------------------ #
# CLASSE PARA LEITURA DE EXCEL

class ExcelReader:
    def __init__(self, log_dir: str, file_path: str):
        """
        Inicializa o ExcelReader com o caminho para o arquivo Excel.
        """
        self.file_path = file_path
        # Inicializa o gerenciador de log
        self.log_manager = r4venLogManager(log_dir)

    def get_logger(self):
        """ Retorna dinamicamente o logger para este arquivo. """
        return self.log_manager.function_logger(
            __file__,
            console_level=logging.WARNING,
        )

    def get_sheet_names(self) -> list:
        """
        Retorna uma lista com os nomes de todas as abas do arquivo Excel.
        """
        log4me = self.get_logger()

        try:
            xls = pd.ExcelFile(self.file_path)
            sheet_names = xls.sheet_names
            log4me.info(f"Nomes de abas encontrados: {sheet_names}")
            return sheet_names
        except Exception as e:
            log4me.error(f"Erro ao ler os nomes das abas: {e}")
            return []

    def load_sheets(self, ignore_sheets: list = None) -> dict:
        log4me = self.get_logger()
        ignore_sheets = set(ignore_sheets or [])
        sheets_dict = {}

        try:
            xls = pd.ExcelFile(self.file_path)
        except Exception as e:
            log4me.error(f"Erro ao abrir o arquivo Excel '{self.file_path}': {e}")
            return sheets_dict

        for sheet in xls.sheet_names:
            if sheet in ignore_sheets:
                log4me.info(f"Aba ignorada: {sheet}")
                continue

            try:
                df = pd.read_excel(self.file_path, sheet_name=sheet)

                # 🔥 1. fillna global
                df = df.fillna('')

                # 🔥 2. normalizar apenas colunas string (muito mais eficiente)
                str_cols = df.select_dtypes(include=["object"]).columns

                for col in str_cols:
                    df[col] = df[col].apply(_normalize_string)

                df = clean_dataframe(df)

                sheets_dict[sheet] = df

                log4me.info(f"Aba carregada com sucesso: {sheet}")

            except Exception as e:
                log4me.error(f"Erro ao carregar a aba '{sheet}': {e}")

        return sheets_dict


@st.cache_data(show_spinner="Carregando dados...", ttl=3600)
def read_excel_data(file_name: str) -> dict:
    """
    Página principal do Streamlit responsável por:
    - Ler o arquivo skills.xlsx usando a classe ExcelReader
    - Filtrar abas indesejadas
    - Permitir selecionar uma aba válida
    - Validar colunas obrigatórias
    - Aplicar filtros dinâmicos + campo de busca + ordenação
    - Permitir modo de visualização (Ficha Completa / Lista Compacta)
    - Renderizar o conteúdo final
    """

    # Caminho fixo do arquivo
    file_path = os.path.join(data_folder, file_name)

    # Inicializa o leitor
    excel_reader = ExcelReader(log_dir=logs_folder, file_path=file_path)
    log4me = excel_reader.get_logger()

    # ----------------------------------------------------------------------------------------- #
    # LÊ OS NOMES DAS ABAS
    # ----------------------------------------------------------------------------------------- #
    try:
        sheet_names = excel_reader.get_sheet_names()
        sheet_names = sorted(sheet_names)
        invalid_sheet_names = [s for s in sheet_names if s and s[0].isdigit()]
    except Exception as e:
        log4me.error("Falha ao ler os nomes das abas.")
        return

    if not sheet_names:
        log4me.error(f"Nenhuma aba encontrada no arquivo: {file_path}")
        return

    default_exclude = ["data_validation"]
    default_exclude.extend(invalid_sheet_names)
    cleaned_sheet_names = filter_sheet_names(sheet_names, default_exclude)

    if not cleaned_sheet_names:
        log4me.error("Nenhuma aba válida após a filtragem.")
        return

    # ----------------------------------------------------------------------------------------- #
    # CARREGA AS ABAS EM SEUS RESPECTIVOS DATAFRAMES
    # ----------------------------------------------------------------------------------------- #
    try:
        df_dict = excel_reader.load_sheets(ignore_sheets=default_exclude)
    except Exception as e:
        log4me.error("Falha ao carregar as abas selecionada.")
        return

    return df_dict
