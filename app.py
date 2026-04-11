imporimport streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Dashboard Fasiclin", layout="wide")

# Estilo CSS para melhorar a aparência
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# Título e Logo
st.title("📊 Gestão de Procedimentos - FASICLIN")
st.markdown("---")

# Carregamento dos dados
@st.cache_data
def load_data():
    # Link CSV da sua planilha (Publicada na Web)
    GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpHTm4l6jKCsZTLaSJjDZn-TYdaoxla54U9hhkJLdBe_HC5QNrWleCaLkq7_UglTMXP-muYt4hNKAI/pub?output=csv"
    
    # Lê o CSV
    df = pd.read_csv(GOOGLE_SHEET_URL)
    
    # TRATAMENTO DE ERROS DE NOME:
    # Remove espaços e coloca tudo em MAIÚSCULO para evitar KeyError
    df.columns = [str(col).strip().upper() for col in df.columns]
    
    # Identifica as colunas de ID (geralmente as duas primeiras: CURSO e UNIDADE)
    # Isso evita erro se a planilha estiver como "curso" (minúsculo)
    col_curso = df.columns[0]
    col_unidade = df.columns[1]
    
    # Transforma a tabela para o formato longo (Tidy Data)
    df_melted = df.melt(id_vars=[col_curso, col_unidade], 
                        var_name="MES", 
                        value_name="ATENDIMENTOS")
    
    # Garante que os valores de atendimentos sejam numéricos
    df_melted["ATENDIMENTOS"] = pd.to_numeric(df_melted["ATENDIMENTOS"], errors='coerce').fillna(0)
    
    return df_melted, col_curso, col_unidade

# Executa o carregamento
try:
    df, col_curso, col_unidade = load_data()

    # --- SIDEBAR (Filtros) ---
    st.sidebar.header("Filtros de Visualização")
    
    unidade_list = df[col_unidade].unique()
    unidade_selecionada = st.sidebar.multiselect("Selecione a Unidade:", 
                                                 options=unidade_list,
                                                 default=unidade_list)

    curso_list = df[col_curso].unique()
    curso_selecionado = st.sidebar.multiselect("Selecione o Curso:", 
                                               options=curso_list,
                                               default=curso_list)

    # Filtragem dos dados
    df_selection = df[df[col_unidade].isin(unidade_selecionada) & df[col_curso].isin(curso_selecionado)]

    # --- KPIs PRINCIPAIS ---
    total_atendimentos = int(df_selection["ATENDIMENTOS"].sum())
    
    # Lógica para evitar erro caso o filtro esteja vazio
    if not df_selection.empty and total_atendimentos > 0:
        curso_pico = df_selection.groupby(col_curso)["ATENDIMENTOS"].sum().idxmax()
    else:
        curso_pico = "N/A"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Procedimentos", f"{total_atendimentos:,}".replace(",", "."))
    with col2:
        st.metric("Curso em Destaque", curso_pico)
    with col3:
        # KPI de média mensal
        media_mensal = total_atendimentos / df_selection["MES"].nunique() if not df_selection.empty else 0
        st.metric("Média Mensal", f"{media_mensal:.0f}")

    st.markdown("---")

    # --- GRÁFICOS ---
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        st.subheader("📈 Evolução dos Atendimentos")
        # Agrupamento para o gráfico de linha (mantendo a ordem dos meses da planilha)
        df_mensal = df_selection.groupby("MES", sort=False)["ATENDIMENTOS"].sum().reset_index()
        fig_mensal = px.line(df_mensal, x="MES", y="ATENDIMENTOS", 
                             markers=True, line_shape="spline",
                             color_discrete_sequence=["#2E86C1"])
        st.plotly_chart(fig_mensal, use_container_width=True)

    with col_graf2:
        st.subheader("🏆 Atendimentos por Área")
        df_curso = df_selection.groupby(col_curso)["ATENDIMENTOS"].sum().reset_index().sort_values("ATENDIMENTOS")
        fig_curso = px.bar(df_curso, x="ATENDIMENTOS", y=col_curso, 
                           orientation='h',
                           color="ATENDIMENTOS", 
                           color_continuous_scale="Blues")
        st.plotly_chart(fig_curso, use_container_width=True)

    # Expansor com os dados brutos filtrados
    with st.expander("🔍 Detalhes da Base de Dados"):
        st.dataframe(df_selection, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.info("Verifique se a planilha está publicada corretamente como CSV e se as colunas estão na ordem correta.")
