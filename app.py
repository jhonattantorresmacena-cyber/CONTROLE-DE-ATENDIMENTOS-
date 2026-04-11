import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Dashboard Fasiclin", layout="wide")

# Estilo para melhorar a interface
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    </style>
    """, unsafe_allow_html=True)

# Título
st.title("📊 Gestão de Procedimentos - FASICLIN")
st.markdown("---")

# Carregamento dos dados
@st.cache_data
def load_data():
    # Link da sua planilha (Publicada na Web como CSV)
    GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpHTm4l6jKCsZTLaSJjDZn-TYdaoxla54U9hhkJLdBe_HC5QNrWleCaLkq7_UglTMXP-muYt4hNKAI/pub?output=csv"
    
    # Lê os dados
    df = pd.read_csv(GOOGLE_SHEET_URL)
    
    # Limpa nomes de colunas (remove espaços e padroniza para maiúsculo)
    df.columns = [str(col).strip().upper() for col in df.columns]
    
    # Identifica as colunas de ID (Curso e Unidade)
    col_curso = df.columns[0]
    col_unidade = df.columns[1]
    
    # Transformação de formato largo para longo
    df_melted = df.melt(id_vars=[col_curso, col_unidade], 
                        var_name="MES", 
                        value_name="ATENDIMENTOS")
    
    # Garante que Atendimentos seja número
    df_melted["ATENDIMENTOS"] = pd.to_numeric(df_melted["ATENDIMENTOS"], errors='coerce').fillna(0)
    
    return df_melted, col_curso, col_unidade

try:
    df, col_curso, col_unidade = load_data()

    # --- SIDEBAR (Filtros) ---
    st.sidebar.header("Filtros")
    
    u_list = df[col_unidade].unique()
    u_sel = st.sidebar.multiselect("Unidade:", options=u_list, default=u_list)

    c_list = df[col_curso].unique()
    c_sel = st.sidebar.multiselect("Curso:", options=c_list, default=c_list)

    # Aplica Filtros
    df_selection = df[df[col_unidade].isin(u_sel) & df[col_curso].isin(c_sel)]

    # --- KPIs ---
    total = int(df_selection["ATENDIMENTOS"].sum())
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total de Procedimentos", f"{total:,}".replace(",", "."))
    with col2:
        if not df_selection.empty and total > 0:
            top_curso = df_selection.groupby(col_curso)["ATENDIMENTOS"].sum().idxmax()
            st.metric("Líder de Atendimentos", top_curso)
        else:
            st.metric("Líder de Atendimentos", "N/A")

    st.markdown("---")

    # --- GRÁFICOS ---
    c_graf1, c_graf2 = st.columns(2)

    with c_graf1:
        st.subheader("Evolução Mensal")
        # Agrupa por mês sem reordenar alfabeticamente
        df_m = df_selection.groupby("MES", sort=False)["ATENDIMENTOS"].sum().reset_index()
        fig_m = px.line(df_m, x="MES", y="ATENDIMENTOS", markers=True, color_discrete_sequence=["#2E86C1"])
        st.plotly_chart(fig_m, use_container_width=True)

    with c_graf2:
        st.subheader("Atendimentos por Curso")
        df_c = df_selection.groupby(col_curso)["ATENDIMENTOS"].sum().reset_index().sort_values("ATENDIMENTOS")
        fig_c = px.bar(df_c, x="ATENDIMENTOS", y=col_curso, orientation='h', color_discrete_sequence=["#1ABC9C"])
        st.plotly_chart(fig_c, use_container_width=True)

    with st.expander("Visualizar Base de Dados"):
        st.dataframe(df_selection)

except Exception as e:
    st.error(f"Ocorreu um problema: {e}")
