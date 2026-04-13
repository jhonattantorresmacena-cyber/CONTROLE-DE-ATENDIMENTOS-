import streamlit as st
import pandas as pd
import plotly.express as px
import time
from streamlit_option_menu import option_menu # Importando o componente

# ==========================================
# 1. CONFIGURAÇÃO E ESTILIZAÇÃO CUSTOMIZADA
# ==========================================
st.set_page_config(page_title="Dashboard FASICLIN", layout="wide", page_icon="🏥")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    /* Estilização para o seletor de Cursos (Selectbox) */
    div.stSelectbox > div { border-radius: 10px !important; background-color: #F0F2F6; border: none; }
    
    .filter-label {
        font-weight: bold;
        color: #2C3E50;
        margin-bottom: 5px;
        margin-top: 15px;
        font-size: 0.9rem;
    }
    
    [data-testid="stMetricDiv"] {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #EEE;
    }
    /* Esconder o menu lateral */
    [data-testid="stSidebar"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. CARREGAMENTO DE DADOS
# ==========================================
@st.cache_data(ttl=600)
def load_data():
    URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpHTm4l6jKCsZTLaSJjDZn-TYdaoxla54U9hhkJLdBe_HC5QNrWleCaLkq7_UglTMXP-muYt4hNKAI/pub?output=csv"
    df = pd.read_csv(f"{URL}&refresh={time.time()}")
    df.columns = [str(col).strip().upper() for col in df.columns]
    for col in ['UNIDADE', 'CURSO', 'MÊS', 'SEMESTRE']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
    target_col = "QUANTIDADE_PROCEDIMENTO"
    for col in df.columns:
        if "QUANTIDADE" in col:
            target_col = col
            break
    df[target_col] = pd.to_numeric(df[target_col], errors='coerce').fillna(0)
    return df, target_col

df, col_valor = load_data()

# ==========================================
# 3. CABEÇALHO (LOGO E SINCRONISMO)
# ==========================================
col_logo, col_sync = st.columns([8, 2])
with col_logo:
    # Correção da Logo: Link direto oficial
   st.image("image_1.png", width=220)
with col_sync:
    st.markdown(f"<div style='text-align: right; color: #7F8C8D;'><b>{time.strftime('%d/%m/%Y %H:%M')}</b></div>", unsafe_allow_html=True)

# ==========================================
# 4. FILTROS PROFISSIONAIS (COMPONENTES CUSTOM)
# ==========================================

# 1. Filtro de Cursos (Selectbox largo)
st.markdown('<p class="filter-label">🎯 PROCEDIMENTO / CURSO</p>', unsafe_allow_html=True)
lista_cursos = ["TODOS OS CURSOS"] + sorted(df["CURSO"].unique().tolist())
c_sel_raw = st.selectbox("", lista_cursos, label_visibility="collapsed")
c_sel = df["CURSO"].unique() if c_sel_raw == "TODOS OS CURSOS" else [c_sel_raw]

# 2. Filtro de Unidades (Estilo Pílula/Botões)
st.markdown('<p class="filter-label">📍 UNIDADES</p>', unsafe_allow_html=True)
lista_unidades = ["TODAS"] + sorted(df["UNIDADE"].unique().tolist())
u_sel_raw = option_menu(None, lista_unidades, 
    icons=['house', 'geo-alt', 'geo-alt', 'geo-alt'], 
    menu_icon="cast", default_index=0, orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#fafafa"},
        "nav-link": {"font-size": "14px", "text-align": "center", "margin":"0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "#1ABC9C"}, # Verde FASICLIN
    }
)
u_sel = df["UNIDADE"].unique() if u_sel_raw == "TODAS" else [u_sel_raw]

# 3. Filtro de Semestre (Estilo Pílula)
st.markdown('<p class="filter-label">📅 SEMESTRE</p>', unsafe_allow_html=True)
lista_semestres = ["TODOS"] + sorted(df["SEMESTRE"].unique().tolist())
s_sel_raw = option_menu(None, lista_semestres, 
    icons=['calendar-range', 'calendar-check', 'calendar-check'], 
    menu_icon="cast", default_index=0, orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#fafafa"},
        "nav-link": {"font-size": "14px", "text-align": "center", "margin":"0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "#3498DB"},
    }
)
s_sel = df["SEMESTRE"].unique() if s_sel_raw == "TODOS" else [s_sel_raw]

# Aplicação dos Filtros
mask = (df["UNIDADE"].isin(u_sel)) & (df["CURSO"].isin(c_sel)) & (df["SEMESTRE"].isin(s_sel))
df_filtered = df[mask]

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 5. KPIs E GRÁFICOS (FLUXO VERTICAL)
# ==========================================
k1, k2, k3 = st.columns(3)
total_atend = int(df_filtered[col_valor].sum())
with k1: st.metric("Total de Atendimentos", f"{total_atend:,}".replace(",", "."))
with k2: st.metric("Cursos Ativos", len(df_filtered["CURSO"].unique()))
with k3: st.metric("Média por Unidade", f"{int(total_atend/len(u_sel)) if len(u_sel)>0 else 0}")

# Tendência
st.markdown('<p class="filter-label">📈 TENDÊNCIA DE ATENDIMENTOS</p>', unsafe_allow_html=True)
df_evol = df_filtered.groupby(["MÊS", "UNIDADE"], sort=False)[col_valor].sum().reset_index()
fig_line = px.line(df_evol, x="MÊS", y=col_valor, color="UNIDADE", markers=True, 
                  color_discrete_map={"SINOP": "#3498DB", "SORRISO": "#F1C40F", "CUIABÁ": "#E74C3C"})
st.plotly_chart(fig_line, use_container_width=True)

# Estatística de Procedimento (Donut)
st.markdown('<p class="filter-label">🍩 ESTATÍSTICA DE PROCEDIMENTO</p>', unsafe_allow_html=True)
fig_pie = px.pie(df_filtered, values=col_valor, names="CURSO", hole=0.5)
st.plotly_chart(fig_pie, use_container_width=True)

# Ranking
st.markdown('<p class="filter-label">🏆 RANKING DE UNIDADES</p>', unsafe_allow_html=True)
df_rank = df_filtered.groupby("UNIDADE")[col_valor].sum().reset_index().sort_values(col_valor, ascending=False)
fig_rank = px.bar(df_rank, x=col_valor, y="UNIDADE", orientation='h', text_auto='.2s', color="UNIDADE")
st.plotly_chart(fig_rank, use_container_width=True)
