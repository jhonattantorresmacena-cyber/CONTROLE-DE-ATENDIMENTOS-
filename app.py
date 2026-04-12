import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Dashboard FASICLIN", layout="wide")

# Estilo CSS para melhorar o visual
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; color: #1ABC9C; }
    .main { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNÇÃO DE CARREGAMENTO (Com atualização automática a cada 10 min)
@st.cache_data(ttl=600)
def load_data():
    # URL da planilha publicada como CSV
    URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpHTm4l6jKCsZTLaSJjDZn-TYdaoxla54U9hhkJLdBe_HC5QNrWleCaLkq7_UglTMXP-muYt4hNKAI/pub?output=csv"
    
    # Adiciona um marcador de tempo na URL para forçar o Google a entregar dados novos
    df = pd.read_csv(f"{URL}&refresh={time.time()}")
    
    # Padroniza nomes de colunas (Maiúsculo e sem espaços)
    df.columns = [str(col).strip().upper() for col in df.columns]
    
    # Define a coluna correta de valor (Verificando se há espaço no nome vindo da planilha)
    # Na sua imagem a coluna parece ser "QUANTIDADE _PROCEDIMENTO"
    target_col = "QUANTIDADE_PROCEDIMENTO"
    for col in df.columns:
        if "QUANTIDADE" in col:
            target_col = col
            break
            
    # Converte para número e limpa a coluna
    df[target_col] = pd.to_numeric(df[target_col], errors='coerce').fillna(0)
    
    return df, target_col

try:
    df, col_valor = load_data()

    # --- 3. SIDEBAR (FILTROS E ATUALIZAÇÃO) ---
    st.sidebar.header("⚙️ Painel de Controle")
    
    if st.sidebar.button("🔄 Forçar Atualização"):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.markdown("---")
    
    # Filtros Dinâmicos
    unidades = df["UNIDADE"].unique()
    u_sel = st.sidebar.multiselect("Unidade:", unidades, default=unidades)

    cursos = df["CURSO"].unique()
    c_sel = st.sidebar.multiselect("Curso:", cursos, default=cursos)
    
    meses = df["MÊS"].unique()
    m_sel = st.sidebar.multiselect("Mês:", meses, default=meses)

    # Aplicação dos filtros
    mask = (df["UNIDADE"].isin(u_sel)) & (df["CURSO"].isin(c_sel)) & (df["MÊS"].isin(m_sel))
    df_filtered = df[mask]

    # --- 4. CABEÇALHO ---
    st.title("📊 Gestão de Procedimentos - FASICLIN")
    st.info(f"Dados atualizados em: {time.strftime('%H:%M:%S')}")

    # --- 5. INDICADORES (KPIs) ---
    k1, k2, k3 = st.columns(3)
    
    # Cálculo correto: Soma apenas a coluna de quantidade (ignora ano e semestre)
    total_atend = int(df_filtered[col_valor].sum())
    media_mensal = total_atend / len(df_filtered["MÊS"].unique()) if not df_filtered.empty else 0
    
    with k1:
        st.metric("Total de Procedimentos", f"{total_atend:,}".replace(",", "."))
    with k2:
        st.metric("Média Mensal", f"{int(media_mensal):,}".replace(",", "."))
    with k3:
        if not df_filtered.empty:
            lider = df_filtered.groupby("CURSO")[col_valor].sum().idxmax()
            st.metric("Curso Líder", lider)
        else:
            st.metric("Curso Líder", "N/A")

    st.markdown("---")

    # --- 6. GRÁFICOS ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📈 Evolução por Mês")
        # Agrupamento correto para não somar colunas de ano
        df_evol = df_filtered.groupby("MÊS", sort=False)[col_valor].sum().reset_index()
        fig_line = px.line(df_evol, x="MÊS", y=col_valor, markers=True, color_discrete_sequence=["#2E86C1"])
        st.plotly_chart(fig_line, use_container_width=True)

    with c2:
        st.subheader("🍩 Distribuição por Curso")
        fig_pie = px.pie(df_filtered, values=col_valor, names="CURSO", hole=0.4, 
                         color_discrete_sequence=px.colors.qualitative.Safe)
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- 7. TABELA DETALHADA ---
    with st.expander("📄 Ver dados completos"):
        st.write(df_filtered)

except Exception as e:
    st.error(f"Erro ao carregar dashboard: {e}")
    st.warning("Dica: Verifique se a coluna na planilha se chama exatamente 'QUANTIDADE_PROCEDIMENTO'.")
