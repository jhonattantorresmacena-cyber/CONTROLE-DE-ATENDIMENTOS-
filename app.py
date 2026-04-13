import streamlit as st
import pandas as pd
import plotly.express as px
import time

# ==========================================
# 1. CONFIGURAÇÃO E ESTILIZAÇÃO CUSTOMIZADA
# ==========================================
st.set_page_config(page_title="Dashboard FASICLIN", layout="wide", page_icon="🏥")

# CSS para criar os botões arredondados e filtros profissionais
st.markdown("""
    <style>
    /* Fundo e Container */
    .stApp { background-color: #FFFFFF; }
    
    /* Estilização dos Filtros tipo "Pílula" (Meses e Unidades) */
    div.stSelectbox > div { border-radius: 20px !important; }
    
    /* Títulos de seção */
    .filter-label {
        font-weight: bold;
        color: #2C3E50;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Estilização dos Cards de KPI */
    [data-testid="stMetricDiv"] {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #EEE;
    }
    
    /* Esconder o menu lateral padrão para focar nos filtros da tela principal */
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
    
    # Limpeza de texto
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
    # 4- CORREÇÃO DA LOGO: Usando o link direto da imagem pública da FASICLIN
    st.image("https://www.fasiclin.com.br/wp-content/uploads/2021/08/logo-fasiclin.png", width=220)
with col_sync:
    st.markdown(f"""
        <div style='text-align: right; color: #7F8C8D; font-size: 0.85rem;'>
        Sincronizado em:<br>
        <b>{time.strftime('%d/%m/%Y às %H:%M')}</b>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 4. FILTROS PROFISSIONAIS (PADRÃO IMAGEM)
# ==========================================

# 1- FILTRO DE CURSOS (Padrão: Seleção Horizontal/Dropdown largo)
st.markdown('<p class="filter-label">🎯 Procedimento / Curso:</p>', unsafe_allow_html=True)
lista_cursos = ["-- TODOS OS CURSOS --"] + sorted(df["CURSO"].unique().tolist())
c_sel_raw = st.selectbox("", lista_cursos, label_visibility="collapsed")
c_sel = df["CURSO"].unique() if c_sel_raw == "-- TODOS OS CURSOS --" else [c_sel_raw]

st.markdown("<br>", unsafe_allow_html=True)

# 2- FILTRO DE UNIDADES (Padrão: Botões Lado a Lado / Pílulas)
st.markdown('<p class="filter-label">📍 Unidades:</p>', unsafe_allow_html=True)
lista_unidades = ["TODAS AS UNIDADES"] + sorted(df["UNIDADE"].unique().tolist())
u_sel_raw = st.radio("", lista_unidades, horizontal=True, label_visibility="collapsed")
u_sel = df["UNIDADE"].unique() if u_sel_raw == "TODAS AS UNIDADES" else [u_sel_raw]

# 3- FILTRO DE SEMESTRE (Abaixo das unidades, mesmo padrão de botões)
st.markdown('<p class="filter-label">📅 Semestre:</p>', unsafe_allow_html=True)
lista_semestres = ["TODOS OS SEMESTRES"] + sorted(df["SEMESTRE"].unique().tolist())
s_sel_raw = st.radio("", lista_semestres, horizontal=True, label_visibility="collapsed")
s_sel = df["SEMESTRE"].unique() if s_sel_raw == "TODOS OS SEMESTRES" else [s_sel_raw]

# Filtro de Meses (Padrão: Botões Lado a Lado)
st.markdown('<p class="filter-label">🗓️ Período:</p>', unsafe_allow_html=True)
lista_meses = ["TODOS OS MESES"] + sorted(df["MÊS"].unique().tolist())
m_sel_raw = st.radio("", lista_meses, horizontal=True, label_visibility="collapsed")
m_sel = df["MÊS"].unique() if m_sel_raw == "TODOS OS MESES" else [m_sel_raw]

# Aplicar Máscara de Filtros
mask = (df["UNIDADE"].isin(u_sel)) & (df["CURSO"].isin(c_sel)) & (df["SEMESTRE"].isin(s_sel)) & (df["MÊS"].isin(m_sel))
df_filtered = df[mask]

st.markdown("---")

# ==========================================
# 5. KPIs E GRÁFICOS (ESTRUTURA VERTICAL)
# ==========================================
k1, k2, k3 = st.columns(3)
total_atend = int(df_filtered[col_valor].sum())
# Simulação de faturamento e eficiência baseado no seu print
with k1:
    st.metric("Total Atendimentos", f"{total_atend:,}".replace(",", "."))
with k2:
    # Exemplo de cálculo: R$ 20,00 por procedimento (ajuste conforme necessário)
    st.metric("Faturamento Estimado", f"R$ {total_atend * 20:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
with k3:
    st.metric("Cursos Ativos", len(df_filtered["CURSO"].unique()))

# Gráfico de Tendência (Tela Cheia conforme solicitado antes)
st.subheader("📈 Tendência de Atendimentos")
df_evol = df_filtered.groupby(["MÊS", "UNIDADE"], sort=False)[col_valor].sum().reset_index()
fig_line = px.line(df_evol, x="MÊS", y=col_valor, color="UNIDADE", markers=True, color_discrete_sequence=px.colors.qualitative.Safe)
fig_line.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig_line, use_container_width=True)

# Ranking de Unidades
st.subheader("🏆 Ranking de Unidades")
df_rank = df_filtered.groupby("UNIDADE")[col_valor].sum().reset_index().sort_values(col_valor, ascending=False)
fig_rank = px.bar(df_rank, x=col_valor, y="UNIDADE", orientation='h', text_auto='.2s', color="UNIDADE")
st.plotly_chart(fig_rank, use_container_width=True)
