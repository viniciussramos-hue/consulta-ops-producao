import streamlit as st
import pandas as pd
import numpy as np

# Configuração inicial da página Streamlit
st.set_page_config(page_title="Consulta de OPs", layout="wide")

@st.cache_data
def carregar_dados():
    # Carrega a aba 'Data' do arquivo Excel
    df = pd.read_excel("Coois_OP.xlsx", sheet_name="Data")
    
    # Tratamento básico dos tipos para evitar erros de busca
    df['Material'] = df['Material'].astype(str)
    df['Ordem'] = df['Ordem'].astype(str)
    
    return df

def formatar_tempo(horas):
    """Converte horas decimais para o formato HH:MM:SS com arredondamento."""
    if pd.isna(horas) or horas == float('inf'):
        return "00:00:00"
    
    total_segundos = round(horas * 3600)
    h = total_segundos // 3600
    m = (total_segundos % 3600) // 60
    s = total_segundos % 60
    
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

# --- Interface Frontend ---
st.title("🏭 Consulta de OPs e Eficiência de Produção")
st.markdown("---")

# 1. Carregamento e leitura
try:
    df_op = carregar_dados()
except FileNotFoundError:
    st.error("O arquivo 'Coois_OP.xlsx' não foi encontrado. Verifique se ele está na mesma pasta deste script.")
    st.stop()

# 2. Interface de Busca e Cabeçalho
col1, col2 = st.columns([1, 3])

with col1:
    lista_ops = df_op['Ordem'].unique().tolist()
    op_selecionada = st.selectbox("Selecione ou digite o Nº da OP:", [""] + lista_ops)

# 3. Tabela e Cálculos (Regra de Negócio)
if op_selecionada:
    df_filtrado = df_op[df_op['Ordem'] == op_selecionada].copy()
    
    if not df_filtrado.empty:
        cod_maxion = df_filtrado.iloc[0]['Material']
        desc_material = df_filtrado.iloc[0]['Texto breve material']
        
        with col2:
            st.info(f"**Cód Maxion (Material):** {cod_maxion} \n\n **Descrição MP:** {desc_material}")
            
        st.markdown("### Detalhes das Operações")
        
        # --- Cálculos Base ---
        # Tempo Previsto (Tempo OP) = Quantidade Operação / Standard (Quantidade básica)
        df_filtrado['Tempo Previsto (h)'] = df_filtrado['Quantidade operação'] / df_filtrado['Quantidade básica']
        df_filtrado['Tempo OP Formatado'] = df_filtrado['Tempo Previsto (h)'].apply(formatar_tempo)
        
        # Tempo Produzido = Quantidade Boa Produzida / Standard
        df_filtrado['Tempo Produzido (h)'] = df_filtrado['Qtd.boa total confirmada'] / df_filtrado['Quantidade básica']
        df_filtrado['Tempo Produzido Formatado'] = df_filtrado['Tempo Produzido (h)'].apply(formatar_tempo)
        
        # --- Cálculo de Eficiência ---
        # Variável para você ajustar caso o nome da coluna no seu Excel seja diferente
        coluna_tempo_real = 'Tempo Real' 
        
        if coluna_tempo_real in df_filtrado.columns:
            # Calcula Eficiência evitando divisão por zero
            df_filtrado['Eficiência'] = np.where(
                df_filtrado[coluna_tempo_real] > 0,
                (df_filtrado['Tempo Previsto (h)'] / df_filtrado[coluna_tempo_real]) * 100,
                0
            )
            df_filtrado['Eficiência'] = df_filtrado['Eficiência'].map('{:.2f}%'.format)
        else:
            # Caso a coluna não exista no arquivo lido, exibe um aviso na tabela
            df_filtrado['Eficiência'] = "Falta Coluna Tempo Real"

        # Prepara a tabela para exibição
        colunas_exibicao = [
            'Centro de trabalho',
            'Descrição do centro de trabalho',
            'Txt.breve operação',
            'Operação',
            'Quantidade operação',
            'Status do sistema',
            'Quantidade básica',
            'Tempo OP Formatado',
            'Tempo Produzido Formatado',
            'Eficiência'
        ]
        
        df_tabela = df_filtrado[colunas_exibicao].rename(columns={
            'Centro de trabalho': 'CT',
            'Descrição do centro de trabalho': 'Descrição CT',
            'Txt.breve operação': 'Desc. Operação',
            'Quantidade operação': 'Quantidade',
            'Status do sistema': 'Status',
            'Quantidade básica': 'Standard',
            'Tempo OP Formatado': 'Tempo Previsto',
            'Tempo Produzido Formatado': 'Tempo Produzido'
        })
        
        # Exibe a tabela interativa
        st.dataframe(df_tabela, use_container_width=True, hide_index=True)
        
    else:
        st.warning("Nenhum dado encontrado para a OP informada.")
else:
    st.info("Aguardando seleção da Ordem de Produção (OP)...")
