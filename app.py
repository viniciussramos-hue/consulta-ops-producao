import streamlit as st
import pandas as pd
import numpy as np

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Consulta de OPs e Eficiência",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS CUSTOMIZADO ---
st.markdown("""
<style>
    .header-box {
        background-color: #1e1e1e; /* Ajustado para dark mode padrão */
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #004a8f; 
        margin-bottom: 20px;
    }
    .metric-value {
        font-size: 1.2rem;
        font-weight: bold;
        color: #66b3ff;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #ccc;
    }
</style>
""", unsafe_allow_html=True)

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_excel("Coois_OP.xlsx", sheet_name="Data")
        df['Ordem'] = df['Ordem'].fillna(0).astype(int).astype(str)
        df['Material'] = df['Material'].fillna('').astype(str)
        
        colunas_numericas = ['Quantidade operação', 'Quantidade básica', 'Qtd.boa total confirmada']
        for col in colunas_numericas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        return df
    except FileNotFoundError:
        return None
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

def formatar_tempo(horas_decimais):
    if pd.isna(horas_decimais) or horas_decimais == float('inf') or horas_decimais < 0:
        return "00:00:00"
    total_segundos = round(horas_decimais * 3600)
    h = total_segundos // 3600
    m = (total_segundos % 3600) // 60
    s = total_segundos % 60
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

# --- CABEÇALHO DO APP ---
st.title("🏭 Consulta de OPs e Eficiência de Produção")
st.markdown("---")

df_op = carregar_dados()

if df_op is None:
    st.error("⚠️ O arquivo **Coois_OP.xlsx** não foi encontrado.")
    st.stop()

# --- TABELA DE CONSULTA ESTÁTICA (EXPANSÍVEL) ---
with st.expander("📊 Consultar Tabela de Classificação de Operações de Estampagem"):
    tabela_estampagem = pd.DataFrame({
        "Classificação operações de estampagem": [
            "Simples", "LE + LD", "Dupla", "Conjugada (2 ferramentas)",
            "Conjugada (2 ferramentas) Dupla", "Conjugada (3 ferramentas)",
            "Conjugada (3 ferramentas) Dupla", "Conjugada (4 ferramentas)",
            "Conjugada (4 ferramentas) Dupla", "Dupla LE + LD",
            "Conjugada (2 ferramentas) LE + LD", "4 part numbers/batida"
        ],
        "Standard/part number": [150, 150, 300, 150, 300, 150, 300, 150, 300, 300, 150, 150],
        "Tempo máquina/part number": ["1", "0,5", "1", "0,5", "0,5", "0,33", "0,33", "0,25", "0,25", "0,5", "0,25", "0,25"]
    })
    
    st.markdown("### Exemplo 150 batidas/hora")
    st.table(tabela_estampagem)

# --- ÁREA DE BUSCA ---
col_busca1, col_busca2 = st.columns([1, 2])

with col_busca1:
    tipo_busca = st.radio("Buscar por:", ["Ordem de Produção (OP)", "Código Maxion (Material)"], horizontal=True)

with col_busca2:
    if tipo_busca == "Ordem de Produção (OP)":
        lista_opcoes = sorted([op for op in df_op['Ordem'].unique().tolist() if op != '0'])
        termo_busca = st.selectbox("Selecione ou digite o Nº da OP:", [""] + lista_opcoes)
    else:
        lista_opcoes = sorted([mat for mat in df_op['Material'].unique().tolist() if mat != ''])
        termo_busca = st.selectbox("Selecione ou digite o Cód Maxion:", [""] + lista_opcoes)

# --- REGRAS DE NEGÓCIO E EXIBIÇÃO ---
if termo_busca:
    if tipo_busca == "Ordem de Produção (OP)":
        df_filtrado = df_op[df_op['Ordem'] == termo_busca].copy()
    else:
        df_filtrado = df_op[df_op['Material'] == termo_busca].copy()
    
    if not df_filtrado.empty:
        # Cabeçalho de informações base
        primeira_linha = df_filtrado.iloc[0]
        cod_maxion = primeira_linha.get('Material', 'N/A')
        desc_material = primeira_linha.get('Texto breve material', 'N/A')
        
        st.markdown(f"""
            <div class="header-box">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <div class="metric-label">Cód Maxion (Material)</div>
                        <div class="metric-value">{cod_maxion}</div>
                    </div>
                    <div>
                        <div class="metric-label">Descrição MP</div>
                        <div class="metric-value">{desc_material}</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📋 Detalhes das Operações")
        
        # Cálculos de tempo e eficiência
        df_filtrado['Standard Ajustado'] = np.where(df_filtrado['Quantidade básica'] == 0, 1, df_filtrado['Quantidade básica'])
        df_filtrado['Tempo Previsto (h)'] = df_filtrado['Quantidade operação'] / df_filtrado['Standard Ajustado']
        df_filtrado['Tempo OP'] = df_filtrado['Tempo Previsto (h)'].apply(formatar_tempo)
        
        df_filtrado['Tempo Produzido (h)'] = df_filtrado['Qtd.boa total confirmada'] / df_filtrado['Standard Ajustado']
        df_filtrado['Tempo Produzido'] = df_filtrado['Tempo Produzido (h)'].apply(formatar_tempo)
        
        coluna_tempo_real = 'Duração real' # Altere conforme sua coluna do Excel
        
        if coluna_tempo_real in df_filtrado.columns:
            df_filtrado[coluna_tempo_real] = pd.to_numeric(df_filtrado[coluna_tempo_real], errors='coerce').fillna(0)
            df_filtrado['Eficiência'] = np.where(
                df_filtrado[coluna_tempo_real] > 0,
                (df_filtrado['Tempo Previsto (h)'] / df_filtrado[coluna_tempo_real]) * 100,
                0
            )
            df_filtrado['Eficiência'] = df_filtrado['Eficiência'].map('{:.1f}%'.format)
        else:
            df_filtrado['Eficiência'] = "Falta Coluna Tempo Real"

        # Organizando colunas para visualização
        colunas_para_exibir = {
            'Ordem': 'OP', # Adicionado para diferenciar quando buscar por material
            'Centro de trabalho': 'CT',
            'Descrição do centro de trabalho': 'Descrição CT',
            'Txt.breve operação': 'Desc. Operação',
            'Operação': 'Operação',
            'Quantidade operação': 'Quantidade',
            'Status do sistema': 'Status',
            'Quantidade básica': 'Standard',
            'Tempo OP': 'Tempo Previsto',
            'Tempo Produzido': 'Tempo Produzido',
            'Eficiência': 'Eficiência'
        }
        
        colunas_existentes = {k: v for k, v in colunas_para_exibir.items() if k in df_filtrado.columns}
        df_tabela = df_filtrado[list(colunas_existentes.keys())].rename(columns=colunas_existentes)
        
        if 'Operação' in df_tabela.columns:
            df_tabela['Operação'] = pd.to_numeric(df_tabela['Operação'], errors='coerce')
            
        # Ordena por OP e depois por Operação
        if 'OP' in df_tabela.columns and 'Operação' in df_tabela.columns:
            df_tabela = df_tabela.sort_values(by=['OP', 'Operação'])
            
        st.dataframe(df_tabela, use_container_width=True, hide_index=True)
        
    else:
        st.warning("Nenhum dado encontrado para a busca informada.")
