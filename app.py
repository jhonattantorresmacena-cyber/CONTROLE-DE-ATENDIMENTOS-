import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Dashboard Fasiclin", layout="wide")

# Título e Logo
st.title("📊 Gestão de Procedimentos - FASICLIN")
st.markdown("---")

# Carregamento dos dados
@st.cache_data
def load_data():
    # Substitua pelo caminho do seu arquivo
    df = pd.read_excel("data/procedimentos.xlsx") 
    # Transformar de formato "largo" para "longo" (tidy data) para facilitar os gráficos
    df_melted = df.melt(id_vars=["CURSO", "UNIDADE"], 
                        var_name="MES", 
                        value_name="ATENDIMENTOS")
    return df_melted

df = load_data()

# --- SIDEBAR (Filtros) ---
st.sidebar.header("Filtros")
unidade = st.sidebar.multiselect("Selecione a Unidade:", 
                                 options=df["UNIDADE"].unique(),
                                 default=df["UNIDADE"].unique())

curso = st.sidebar.multiselect("Selecione o Curso:", 
                               options=df["CURSO"].unique(),
                               default=df["CURSO"].unique())

df_selection = df.query("UNIDADE == @unidade & CURSO == @curso")

# --- KPIs PRINCIPAIS ---
total_atendimentos = df_selection["ATENDIMENTOS"].sum()
curso_pico = df_selection.groupby("CURSO")["ATENDIMENTOS"].sum().idxmax()

col1, col2 = st.columns(2)
with col1:
    st.metric("Total de Atendimentos", f"{total_atendimentos:,}".replace(",", "."))
with col2:
    st.metric("Curso com Maior Volume", curso_pico)

st.markdown("---")

# --- GRÁFICOS ---
col3, col4 = st.columns(2)

with col3:
    st.subheader("Evolução Mensal")
    fig_mensal = px.line(df_selection.groupby("MES", sort=False)["ATENDIMENTOS"].sum().reset_index(), 
                         x="MES", y="ATENDIMENTOS", markers=True,
                         color_discrete_sequence=["#00CC96"])
    st.plotly_chart(fig_mensal, use_container_width=True)

with col4:
    st.subheader("Atendimentos por Curso")
    fig_curso = px.bar(df_selection.groupby("CURSO")["ATENDIMENTOS"].sum().reset_index().sort_values("ATENDIMENTOS"), 
                       x="ATENDIMENTOS", y="CURSO", orientation='h',
                       color="ATENDIMENTOS", color_continuous_scale="Viridis")
    st.plotly_chart(fig_curso, use_container_width=True)

# Tabela detalhada
with st.expander("Ver Dados Completos"):
    st.write(df_selection)
