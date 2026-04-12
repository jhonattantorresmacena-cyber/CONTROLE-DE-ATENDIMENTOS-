import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Dashboard FASICLIN", layout="wide")

# Estilo para melhorar a interface
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; color: #2E86C1; }
    .main { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# 2. CARREGAMENTO DOS DADOS
@st.cache_data
def load_data():
    # URL da planilha publicada como CSV
    URL = "https://docs.google.com/spreadsheets/d/1fR58iY_llCMQjrx2K7U3A2bFsUiHPhrtxc0fsT2vIuY/edit?gid=0#gid=0"
    
    df = pd.read_csv(URL)
    
    # Limpeza de nomes de colunas: remove espaços extras e garante o nome correto
    df.columns = [str(col).strip().upper() for col in df.columns]
    
    # IMPORTANTE: Garantir que a coluna de quantidade seja tratada como número
    # O nome deve ser exatamente como está na planilha (vimos que tem um espaço antes do underline na sua imagem)
    col_valor = "QUANTIDADE_PROCEDIMENTO" 
    
    if col_valor not in df.columns:
        # Tenta localizar a coluna caso haja variações de espaço ou escrita
        for c in df.columns:
            if "QUANTIDADE" in c:
                col_valor = c
                break

    df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)
    
    return df, col_valor

try:
    df, col_valor = load_data()

    # --- 3. SIDEBAR (FILTROS) ---
    st.sidebar.header("Filtros de Análise")
    
    # Filtro de Unidade
    u_list = df["UNIDADE"].unique()
    u_sel = st.sidebar.multiselect("Selecione a Unidade:", u_list, default=u_list)

    # Filtro de Curso
    c_list = df["CURSO"].unique()
    c_sel = st.sidebar.multiselect("Selecione o Curso:", c_list, default=c_list)
    
    # Filtro de Mês
    m_list = df["MÊS"].unique()
    m_sel = st.sidebar.multiselect("Selecione o Mês:", m_list, default=m_list)

    # Aplicação dos filtros (Ignorando anos e semestres na soma)
    mask = (df["UNIDADE"].isin(u_sel)) & (df["CURSO"].isin(c_sel)) & (df["MÊS"].isin(m_sel))
    df_filtered = df[mask]

    # --- 4. TÍTULO ---
    st.title("📊 Gestão de Procedimentos - FASICLIN")
    st.markdown("---")

    # --- 5. INDICADORES PRINCIPAIS (KPIs) ---
    kpi1, kpi2, kpi3 = st.columns(3)

    # Total Geral (Somente da coluna de procedimentos)
    total_atendimentos = int(df_filtered[col_valor].sum())
    
    # Média Mensal
    qtd_meses = len(df_filtered["MÊS"].unique())
    media = total_atendimentos / qtd_meses if qtd_meses > 0 else 0
    
    # Curso Líder
    if not df_filtered.empty:
        curso_lider = df_filtered.groupby("CURSO")[col_valor].sum().idxmax()
    else:
        curso_lider = "N/A"

    with kpi1:
        st.metric("Total de Procedimentos", f"{total_atendimentos:,}".replace(",", "."))
    with kpi2:
        st.metric("Média Mensal", f"{int(media):,}".replace(",", "."))
    with kpi3:
        st.metric("Curso Líder", curso_lider)

    st.markdown("---")

    # --- 6. VISÕES GRÁFICAS ---
    col_esq, col_dir = st.columns(2)

    with col_esq:
        st.subheader("📈 Evolução Temporal")
        # Agrupamento explícito pela coluna de valor correta
        df_evolucao = df_filtered.groupby("MÊS", sort=False)[col_valor].sum().reset_index()
        fig_line = px.line(df_evolucao, x="MÊS", y=col_valor, markers=True, color_discrete_sequence=["#2E86C1"])
        st.plotly_chart(fig_line, use_container_width=True)

    with col_dir:
        st.subheader("🍩 Participação por Curso")
        fig_pie = px.pie(df_filtered, values=col_valor, names="CURSO", hole=0.4, 
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)

    # Tabela detalhada
    with st.expander("📄 Visualizar Tabela de Dados Detalhada"):
        st.dataframe(df_filtered, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar dashboard: {e}")
