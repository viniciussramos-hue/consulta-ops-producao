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
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #004a8f; 
        margin-bottom: 15px;
    }
    .summary-box {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .metric-value {
        font-size: 1.1rem;
        font-weight: bold;
        color: #66b3ff;
    }
    .metric-label {
        font-size: 0.85rem;
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
        
        colunas_numericas = ['Quantidade operação', 'Quantidade básica', 'Qtd.boa total confirmada', 'Operação', 'Especificação 2']
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
st.title("🏭 Consulta de OPs e Eficiência")
st.markdown("---")

df_op = carregar_dados()

if df_op is None:
    st.error("⚠️ O arquivo **Coois_OP.xlsx** não foi encontrado.")
    st.stop()

# --- TABELA DE CONSULTA ESTÁTICA (EXPANSÍVEL) ---
with st.expander("📊 Tabela de Classificação de Estampagem"):
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
                <div>
                    <div class="metric-label">Cód Maxion (Material)</div>
                    <div class="metric-value">{cod_maxion}</div>
                </div>
                <div style="margin-top: 8px;">
                    <div class="metric-label">Descrição MP</div>
                    <div class="metric-value" style="font-size: 0.95rem;">{desc_material}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # --- TABELA SUSPENSA INTERATIVA (RESUMO DE OPs VINCULADAS) ---
        if tipo_busca == "Código Maxion (Material)":
            with st.expander("📂 Resumo das OPs vinculadas (Filtro BI)", expanded=True):
                st.markdown("💡 *Toque em uma OP abaixo para filtrar os detalhes:*")
                
                df_resumo_ops = df_filtrado.groupby('Ordem').agg({
                    'Quantidade operação': 'max',
                    'Qtd.boa total confirmada': 'max',
                    'Status do sistema': 'first' 
                }).reset_index()
                
                def definir_status_op(row):
                    status_sap = str(row['Status do sistema']).upper()
                    qtd_planejada = row['Quantidade operação']
                    qtd_produzida = row['Qtd.boa total confirmada']
                    
                    if 'ENC' in status_sap or 'TECO' in status_sap:
                        return '✅ Finalizada'
                    elif qtd_produzida >= qtd_planejada and qtd_planejada > 0:
                         return '✅ Finalizada (Qtd Atingida)'
                    else:
                        return '⏳ Aberta'
                        
                df_resumo_ops['Situação da OP'] = df_resumo_ops.apply(definir_status_op, axis=1)
                
                df_resumo_ops = df_resumo_ops.rename(columns={
                    'Ordem': 'Nº da OP',
                    'Quantidade operação': 'Qtd. Planejada',
                    'Qtd.boa total confirmada': 'Qtd. Produzida',
                    'Status do sistema': 'Status SAP'
                })
                
                evento_tabela = st.dataframe(
                    df_resumo_ops[['Nº da OP', 'Qtd. Planejada', 'Qtd. Produzida', 'Status SAP', 'Situação da OP']], 
                    use_container_width=True, 
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row"
                )
                
                linhas_selecionadas = evento_tabela.selection.rows
                if len(linhas_selecionadas) > 0:
                    op_clicada = df_resumo_ops.iloc[linhas_selecionadas[0]]['Nº da OP']
                    df_filtrado = df_filtrado[df_filtrado['Ordem'] == op_clicada]
                    st.success(f"Filtro ativo: OP **{op_clicada}**")
                else:
                    st.info("Exibindo todas as OPs vinculadas.")
        
        st.markdown("### 📋 Detalhes das Operações")
        
        # --- CÁLCULOS DE TEMPO E EFICIÊNCIA ---
        df_filtrado['Standard Ajustado'] = np.where(df_filtrado['Quantidade básica'] == 0, 1, df_filtrado['Quantidade básica'])
        df_filtrado['Tempo Previsto (h)'] = df_filtrado['Quantidade operação'] / df_filtrado['Standard Ajustado']
        df_filtrado['Tempo OP'] = df_filtrado['Tempo Previsto (h)'].apply(formatar_tempo)
        
        df_filtrado['Tempo Produzido (h)'] = df_filtrado['Qtd.boa total confirmada'] / df_filtrado['Standard Ajustado']
        df_filtrado['Tempo Produzido'] = df_filtrado['Tempo Produzido (h)'].apply(formatar_tempo)
        
        df_filtrado['Eficiencia_Num'] = np.where(
            df_filtrado['Tempo Previsto (h)'] > 0,
            (df_filtrado['Tempo Produzido (h)'] / df_filtrado['Tempo Previsto (h)']) * 100,
            0
        )
        
        df_filtrado['Eficiência'] = df_filtrado.apply(
            lambda row: f"{row['Eficiencia_Num']:.1f}%" if row['Tempo Produzido (h)'] > 0 else "-",
            axis=1
        )

        # Mapeamento exato com a ordem solicitada: CT, Descrição CT, Desc. Operação, Temp. Maq., Operação, Quantidade, Standard, Tempo OP
        colunas_para_exibir = {
            'Ordem': 'OP',
            'Centro de trabalho': 'CT',
            'Descrição do centro de trabalho': 'Descrição CT',
            'Txt.breve operação': 'Desc. Operação',
            'Especificação 2': 'Temp. Maq.',
            'Operação': 'Operação',
            'Quantidade operação': 'Quantidade',
            'Quantidade básica': 'Standard',
            'Tempo OP': 'Tempo OP',
            'Tempo Produzido': 'T. Produzido',
            'Eficiência': 'Efic.'
        }
        
        colunas_existentes = {k: v for k, v in colunas_para_exibir.items() if k in df_filtrado.columns}
        df_tabela = df_filtrado[list(colunas_existentes.keys())].rename(columns=colunas_existentes)
        
        if 'Operação' in df_tabela.columns:
            df_tabela['Operação'] = pd.to_numeric(df_tabela['Operação'], errors='coerce').fillna(0).astype(int)
            
        if 'OP' in df_tabela.columns and 'Operação' in df_tabela.columns:
            df_tabela = df_tabela.sort_values(by=['OP', 'Operação'])
            
        st.dataframe(df_tabela, use_container_width=True, hide_index=True)
        
        # --- RESUMO FINAL SIMPLIFICADO ---
        total_previsto_h = df_filtrado['Tempo Previsto (h)'].sum()
        total_produzido_h = df_filtrado['Tempo Produzido (h)'].sum()
        eficiencia_global = (total_produzido_h / total_previsto_h * 100) if total_previsto_h > 0 else 0
        
        st.markdown(f"""
            <div class="summary-box">
                <div style="font-weight: bold; margin-bottom: 8px; color: #fff;">📱 Resumo Consolidado (Foco Celular):</div>
                <div style="display: flex; justify-content: space-between; text-align: center;">
                    <div>
                        <div class="metric-label">Total Previsto</div>
                        <div class="metric-value">{formatar_tempo(total_previsto_h)}</div>
                    </div>
                    <div>
                        <div class="metric-label">Total Produzido</div>
                        <div class="metric-value">{formatar_tempo(total_produzido_h)}</div>
                    </div>
                    <div>
                        <div class="metric-label">Aderência Global</div>
                        <div class="metric-value">{eficiencia_global:.1f}%</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    else:
        st.warning("Nenhum dado encontrado para a busca informada.")
