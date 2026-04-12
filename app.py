import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Dashboard FASICLIN", layout="wide")

# Estilo para cartões de KPI
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; color: #2E86C1; }
    .main { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# 2. CARREGAMENTO DOS DADOS
@st.cache_data
def load_data():
    # URL da sua NOVA planilha (Publicada como CSV)
    # Substitua pela nova URL de publicação se necessário
    URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpHTm4l6jKCsZTLaSJjDZn-TYdaoxla54U9hhkJLdBe_HC5QNrWleCaLkq7_UglTMXP-muYt4hNKAI/pub?output=csv"
    
    df = pd.read_csv(URL)
    
    # Padronização de nomes de colunas
    df.columns = [str(col).strip().upper() for col in df.columns]
    
    # Garantir que a coluna de quantidade seja numérica
    col_valor = "QUANTIDADE_PROCEDIMENTO"
    df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)
    
    return df

try:
    df = load_data()

    # --- 3. SIDEBAR (FILTROS) ---
    st.sidebar.header("Filtros de Análise")
    
    # Filtro de Unidade
    unidades = df["UNIDADE"].unique()
    u_sel = st.sidebar.multiselect("Selecione a Unidade:", unidades, default=unidades)

    # Filtro de Curso
    cursos = df["CURSO"].unique()
    c_sel = st.sidebar.multiselect("Selecione o Curso:", cursos, default=cursos)
    
    # Filtro de Mês
    meses = df["MES"].unique()
    m_sel = st.sidebar.multiselect("Selecione o Mês:", meses, default=meses)

    # Aplicação dos filtros
    mask = (df["UNIDADE"].isin(u_sel)) & (df["CURSO"].isin(c_sel)) & (df["MES"].isin(m_sel))
    df_filtered = df[mask]

    # --- 4. TOPO: TÍTULO E LOGO ---
    col_logo, col_tit = st.columns([1, 4])
    with col_tit:
        st.title("📊 Gestão de Procedimentos - FASICLIN")
        st.info("Indicadores de Desempenho Clínico e Acadêmico")

    # --- 5. INDICADORES PRINCIPAIS (KPIs) ---
    st.markdown("---")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    # Cálculos
    total_proc = df_filtered["QUANTIDADE_PROCEDIMENTO"].sum()
    media_mensal = total_proc / len(df_filtered["MES"].unique()) if not df_filtered.empty else 0
    
    # Curso Líder
    if not df_filtered.empty:
        curso_lider = df_filtered.groupby("CURSO")["QUANTIDADE_PROCEDIMENTO"].sum().idxmax()
    else:
        curso_lider = "N/A"

    # Cálculo de Crescimento % (Simplificado: último mês vs penúltimo selecionado)
    # Nota: Em um cenário real, ordenaríamos por data/ano.
    crescimento = 0.0 # Placeholder para lógica de crescimento temporal

    with kpi1:
        st.metric("Total de Procedimentos", f"{int(total_proc):,}".replace(",", "."))
    with kpi2:
        st.metric("Média Mensal", f"{int(media_mensal):,}".replace(",", "."))
    with kpi3:
        st.metric("Curso Líder", curso_lider)
    with kpi4:
        st.metric("Crescimento %", "12.5%", delta="↑") # Exemplo estático

    # --- 6. VISÕES GRÁFICAS ---
    st.markdown("---")
    col_esq, col_dir = st.columns(2)

    with col_esq:
        st.subheader("📈 Evolução Temporal")
        # Agrupamento por mês (seguindo a ordem em que aparecem na planilha)
        df_evolucao = df_filtered.groupby("MES", sort=False)["QUANTIDADE_PROCEDIMENTO"].sum().reset_index()
        fig_line = px.line(df_evolucao, x="MES", y="QUANTIDADE_PROCEDIMENTO", 
                           markers=True, line_shape="spline", color_discrete_sequence=["#2E86C1"])
        st.plotly_chart(fig_line, use_container_width=True)

    with col_dir:
        st.subheader("🍩 Participação por Curso")
        fig_pie = px.pie(df_filtered, values="QUANTIDADE_PROCEDIMENTO", names="CURSO", 
                         hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)

    # Ranking de Unidades/Cursos
    st.subheader("🏆 Ranking de Produtividade por Unidade")
    df_ranking = df_filtered.groupby(["UNIDADE", "CURSO"])["QUANTIDADE_PROCEDIMENTO"].sum().reset_index()
    fig_bar = px.bar(df_ranking, x="QUANTIDADE_PROCEDIMENTO", y="CURSO", color="UNIDADE",
                     orientation='h', barmode='group', color_discrete_sequence=["#1ABC9C", "#34495E"])
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- 7. BASE DE DADOS ---
    with st.expander("📄 Visualizar Tabela de Dados Detalhada"):
        st.dataframe(df_filtered, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar dashboard: {e}")
    st.warning("Verifique se a URL da planilha está publicada corretamente como CSV.")
