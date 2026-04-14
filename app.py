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
    
    for col in df.columns:
        if col in ['UNIDADE', 'CURSO', 'MÊS', 'SEMESTRE']:
            df[col] = df[col].astype(str).str.strip().str.upper()

    # Ordem cronológica dos meses
    ordem_meses = ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
                   "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
    if 'MÊS' in df.columns:
        df['MÊS'] = pd.Categorical(df['MÊS'], categories=ordem_meses, ordered=True)
            
    # Localiza a coluna de valor (Quantidade)
    target_col = None
    for col in df.columns:
        if "QUANTIDADE" in col:
            target_col = col
            break
    
    if not target_col:
        target_col = df.select_dtypes(include=['number']).columns[-1]

    df[target_col] = pd.to_numeric(df[target_col], errors='coerce').fillna(0)
    return df, target_col

try:
    df, col_valor = load_data()
except Exception as e:
    st.error(f"Erro crítico: {e}")
    st.stop()

# ==========================================
# 3. CABEÇALHO
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
# 4. FILTROS
# ==========================================
def get_options(column_name, default_label):
    if column_name in df.columns:
        return [default_label] + sorted(df[column_name].unique().tolist())
    return [default_label]

st.markdown('<p class="filter-label">🎯 PROCEDIMENTO / CURSO</p>', unsafe_allow_html=True)
lista_cursos = get_options("CURSO", "TODOS OS CURSOS")
c_sel_raw = st.selectbox("", lista_cursos, label_visibility="collapsed")
c_sel = df["CURSO"].unique() if c_sel_raw == "TODOS OS CURSOS" else [c_sel_raw]

st.markdown('<p class="filter-label">📍 UNIDADES</p>', unsafe_allow_html=True)
lista_unidades = get_options("UNIDADE", "TODAS")
u_sel_raw = option_menu(None, lista_unidades, 
    icons=['house'] + ['geo-alt']*(len(lista_unidades)-1), 
    menu_icon="cast", default_index=0, orientation="horizontal",
    styles={"nav-link-selected": {"background-color": "#1ABC9C"}} # Verde FASICLIN
)
u_sel = df["UNIDADE"].unique() if u_sel_raw == "TODAS" else [u_sel_raw]

st.markdown('<p class="filter-label">📅 SEMESTRE</p>', unsafe_allow_html=True)
lista_semestres = get_options("SEMESTRE", "TODOS")
s_sel_raw = option_menu(None, lista_semestres, 
    icons=['calendar'] + ['calendar-check']*(len(lista_semestres)-1), 
    menu_icon="cast", default_index=0, orientation="horizontal",
    styles={"nav-link-selected": {"background-color": "#3498DB"}} # Azul Semestre
)
s_sel = df["SEMESTRE"].unique() if s_sel_raw == "TODOS" else [s_sel_raw]

# Filtro final
mask = (df["UNIDADE"].isin(u_sel)) & (df["CURSO"].isin(c_sel)) & (df["SEMESTRE"].isin(s_sel))
df_filtered = df[mask]

# ==========================================
# 5. KPIs E GRÁFICOS
# ==========================================
st.markdown("<br>", unsafe_allow_html=True)
k1, k2, k3 = st.columns(3)
total_atend = int(df_filtered[col_valor].sum())
with k1: st.metric("Total de Atendimentos", f"{total_atend:,}".replace(",", "."))
with k2: st.metric("Cursos Ativos", len(df_filtered["CURSO"].unique()))
with k3: st.metric("Média por Unidade", f"{int(total_atend/len(u_sel)) if len(u_sel)>0 else 0}")

def style_fig(fig):
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", 
        paper_bgcolor="rgba(0,0,0,0)", 
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="#EEE")
    )
    return fig

# Tendência com cores coordenadas
st.markdown('<p class="filter-label">📈 TENDÊNCIA DE ATENDIMENTOS</p>', unsafe_allow_html=True)
df_evol = df_filtered.groupby(["MÊS", "UNIDADE"], sort=True, observed=False)[col_valor].sum().reset_index()
fig_line = px.line(df_evol, x="MÊS", y=col_valor, color="UNIDADE", markers=True,
                  color_discrete_sequence=["#1ABC9C", "#3498DB", "#F1C40F", "#E74C3C"])
st.plotly_chart(style_fig(fig_line), use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    st.markdown('<p class="filter-label">🍩 DISTRIBUIÇÃO POR CURSO</p>', unsafe_allow_html=True)
    fig_pie = px.pie(df_filtered, values=col_valor, names="CURSO", hole=0.5,
                    color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(style_fig(fig_pie), use_container_width=True)

with c2:
    st.markdown('<p class="filter-label">🏆 RANKING DE UNIDADES</p>', unsafe_allow_html=True)
    df_rank = df_filtered.groupby("UNIDADE")[col_valor].sum().reset_index().sort_values(col_valor, ascending=True)
    fig_rank = px.bar(df_rank, x=col_valor, y="UNIDADE", orientation='h', 
                     text_auto='.2s', color_discrete_sequence=["#1ABC9C"])
    st.plotly_chart(style_fig(fig_rank), use_container_width=True)
    
