import streamlit as st
import pandas as pd
import plotly.express as px
import time
from streamlit_option_menu import option_menu

# ==========================================
# 1. CONFIGURAÇÃO E ESTILIZAÇÃO
# ==========================================
st.set_page_config(page_title="Dashboard FASICLIN", layout="wide", page_icon="🏥")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    div.stSelectbox > div { border-radius: 10px !important; background-color: #F0F2F6; border: none; }
    .filter-label { font-weight: bold; color: #2C3E50; margin-bottom: 5px; margin-top: 15px; font-size: 0.9rem; }
    [data-testid="stMetricDiv"] { background-color: #f8f9fa; padding: 20px; border-radius: 15px; border: 1px solid #EEE; }
    [data-testid="stSidebar"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. CARREGAMENTO E TRATAMENTO DE DADOS
# ==========================================
@st.cache_data(ttl=600)
def load_data():
    URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpHTm4l6jKCsZTLaSJjDZn-TYdaoxla54U9hhkJLdBe_HC5QNrWleCaLkq7_UglTMXP-muYt4hNKAI/pub?output=csv"
    df = pd.read_csv(f"{URL}&refresh={time.time()}")
    
    # Padronização de colunas
    df.columns = [str(col).strip().upper() for col in df.columns]
    
    # Identificar dinamicamente a coluna de ANO para evitar KeyError
    col_ano = None
    for col in df.columns:
        if "ANO" in col:
            col_ano = col
            break
            
    if not col_ano:
        col_ano = "ANO"
        df[col_ano] = "N/A"
    
    # Padronização das colunas de texto/categorias
    for col in df.columns:
        if col in ['UNIDADE', 'CURSO', 'MÊS', 'SEMESTRE', col_ano]:
            df[col] = df[col].astype(str).str.strip().str.upper()

    # Ordem cronológica dos meses
    ordem_meses = ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
                   "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
    if 'MÊS' in df.columns:
        df['MÊS'] = pd.Categorical(df['MÊS'], categories=ordem_meses, ordered=True)
            
    # Localiza a coluna de valor (Quantidade de Procedimentos)
    target_col = None
    for col in df.columns:
        if "QUANTIDADE" in col and "ANO" not in col:
            target_col = col
            break
    
    if not target_col:
        colunas_numericas = df.select_dtypes(include=['number']).columns
        colunas_filtradas = [c for c in colunas_numericas if "ANO" not in c]
        target_col = colunas_filtradas[-1] if colunas_filtradas else colunas_numericas[-1]

    df[target_col] = pd.to_numeric(df[target_col], errors='coerce').fillna(0)
    
    # Adiciona a coluna TIPO como REALIZADO para os dados vindos da planilha
    df["TIPO"] = "REALIZADO"
    
    return df, target_col, col_ano


# ==========================================
# 3. CÁLCULO E INJEÇÃO AUTOMÁTICA DE METAS (2025/2026)
# ==========================================
def injetar_metas_projetadas(df, col_valor, col_ano, taxa_crescimento=0.10):
    """
    Calcula a média histórica e projeta as linhas de METAS para 2025 e 2026
    """
    df[col_ano] = df[col_ano].astype(str).str.strip()
    
    # Filtra apenas o histórico real para servir de base
    df_historico = df[df["TIPO"] == "REALIZADO"]
    
    base_metas = df_historico.groupby(["UNIDADE", "CURSO", "MÊS", "SEMESTRE"], observed=False)[col_valor].mean().reset_index()
    base_metas.rename(columns={col_valor: "MEDIA_HISTORICA"}, inplace=True)
    
    novas_linhas = []
    
    for ano_proj in ["2025", "2026"]:
        multiplicador = (1 + taxa_crescimento) if ano_proj == "2025" else (1 + taxa_crescimento) ** 2
        
        for _, row in base_metas.iterrows():
            meta_calculada = round(row["MEDIA_HISTORICA"] * multiplicador, 0)
            
            nova_linha = {
                "UNIDADE": row["UNIDADE"],
                "CURSO": row["CURSO"],
                "MÊS": row["MÊS"],
                "SEMESTRE": row["SEMESTRE"],
                col_ano: ano_proj,
                col_valor: meta_calculada,
                "TIPO": "META"  # Definido explicitamente como META
            }
            novas_linhas.append(nova_linha)
            
    if novas_linhas:
        df_metas = pd.DataFrame(novas_linhas)
        df = pd.concat([df, df_metas], ignore_index=True)
        
    return df


# Execução do carregamento e projeção de metas
try:
    df, col_valor, col_ano = load_data()
    df = injetar_metas_projetadas(df, col_valor, col_ano, taxa_crescimento=0.10)
except Exception as e:
    st.error(f"Erro crítico ao carregar e projetar dados: {e}")
    st.stop()

# ==========================================
# 4. CABEÇALHO
# ==========================================
col_logo, col_sync = st.columns([8, 2])
with col_logo:
    try:
        st.image("image_1.png", width=220)
    except:
        st.subheader("🏥 Dashboard FASICLIN")

with col_sync:
    st.markdown(f"<div style='text-align: right; color: #7F8C8D; padding-top:10px;'><b>{time.strftime('%d/%m/%Y %H:%M')}</b></div>", unsafe_allow_html=True)

# ==========================================
# 5. FILTROS
# ==========================================
def get_options(column_name, default_label, reverse=False):
    if column_name in df.columns:
        valores = df[column_name].astype(str).unique().tolist()
        return [default_label] + sorted(valores, reverse=reverse)
    return [default_label]

# --- FILTRO: CURSO ---
st.markdown('<p class="filter-label">🎯 PROCEDIMENTO / CURSO</p>', unsafe_allow_html=True)
lista_cursos = get_options("CURSO", "TODOS OS CURSOS")
c_sel_raw = st.selectbox("", lista_cursos, key="filtro_curso", label_visibility="collapsed")
c_sel = df["CURSO"].unique() if c_sel_raw == "TODOS OS CURSOS" else [c_sel_raw]

# --- FILTRO: UNIDADES ---
st.markdown('<p class="filter-label">📍 UNIDADES</p>', unsafe_allow_html=True)
lista_unidades = get_options("UNIDADE", "TODAS")
u_sel_raw = option_menu(None, lista_unidades, 
    icons=['house'] + ['geo-alt']*(len(lista_unidades)-1), 
    menu_icon="cast", default_index=0, orientation="horizontal",
    styles={"nav-link-selected": {"background-color": "#1ABC9C"}}, 
    key="filtro_unidade"
)
u_sel = df["UNIDADE"].unique() if u_sel_raw == "TODAS" else [u_sel_raw]

# --- FILTRO: ANO ---
st.markdown('<p class="filter-label">📅 ANO DE REFERÊNCIA</p>', unsafe_allow_html=True)
if df[col_ano].iloc[0] == "N/A":
    st.warning("⚠️ Atenção: Nenhuma coluna de 'ANO' foi identificada.")
    a_sel = df[col_ano].unique()
else:
    lista_anos = get_options(col_ano, "TODOS OS ANOS", reverse=False)
    a_sel_raw = option_menu(None, lista_anos, 
        icons=['calendar4-range'] + ['calendar3']*(len(lista_anos)-1), 
        menu_icon="cast", default_index=0, orientation="horizontal",
        styles={"nav-link-selected": {"background-color": "#2C3E50"}}, 
        key="filtro_ano"
    )
    a_sel = df[col_ano].unique() if a_sel_raw == "TODOS OS ANOS" else [a_sel_raw]

# --- FILTRO: SEMESTRE ---
st.markdown('<p class="filter-label">📅 SEMESTRE</p>', unsafe_allow_html=True)
lista_semestres = get_options("SEMESTRE", "TODOS")
s_sel_raw = option_menu(None, lista_semestres, 
    icons=['calendar'] + ['calendar-check']*(len(lista_semestres)-1), 
    menu_icon="cast", default_index=0, orientation="horizontal",
    styles={"nav-link-selected": {"background-color": "#3498DB"}}, 
    key="filtro_semestre"
)
s_sel = df["SEMESTRE"].unique() if s_sel_raw == "TODOS" else [s_sel_raw]

# Filtro final aplicado ao DataFrame
mask = (df["UNIDADE"].isin(u_sel)) & (df["CURSO"].isin(c_sel)) & (df["SEMESTRE"].isin(s_sel)) & (df[col_ano].isin(a_sel))
df_filtered = df[mask]
