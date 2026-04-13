import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Dashboard FASICLIN v2", layout="wide", page_icon="📊")

# Estilo CSS Personalizado
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; color: #1ABC9C; font-weight: bold; }
    .main { background-color: #f0f2f6; }
    div.stButton > button:first-child { background-color: #1ABC9C; color: white; border-radius: 5px; }
    .stPlotlyChart { border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNÇÃO DE CARREGAMENTO OTIMIZADA
@st.cache_data(ttl=600)
def load_data():
    # URL da planilha publicada como CSV
    URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpHTm4l6jKCsZTLaSJjDZn-TYdaoxla54U9hhkJLdBe_HC5QNrWleCaLkq7_UglTMXP-muYt4hNKAI/pub?output=csv"
    
    # Adiciona refresh para evitar cache do Google
    df = pd.read_csv(f"{URL}&refresh={time.time()}")
    
    # Limpeza e Padronização
    df.columns = [str(col).strip().upper() for col in df.columns]
    
    # Tratamento de Strings para evitar duplicatas por erro de digitação
    for col in ['UNIDADE', 'CURSO', 'MÊS']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()

    # Identificação inteligente da coluna de valores
    target_col = "QUANTIDADE_PROCEDIMENTO"
    for col in df.columns:
        if "QUANTIDADE" in col:
            target_col = col
            break
            
    # Conversão numérica
    df[target_col] = pd.to_numeric(df[target_col], errors='coerce').fillna(0)
    
    return df, target_col

try:
    df, col_valor = load_data()

    # --- 3. SIDEBAR (FILTROS ORGANIZADOS) ---
    with st.sidebar:
        st.header("⚙️ Filtros de Gestão")
        
        if st.button("🔄 Atualizar Base de Dados"):
            st.cache_data.clear()
            st.toast('Dados atualizados!', icon='✅')
            time.sleep(1)
            st.rerun()

        st.divider()
        
        # Filtros Hierárquicos
        u_sel = st.multiselect("📍 Selecione a Unidade:", sorted(df["UNIDADE"].unique()), default=df["UNIDADE"].unique())
        
        # O filtro de curso se adapta às unidades selecionadas
        cursos_disponiveis = df[df["UNIDADE"].isin(u_sel)]["CURSO"].unique()
        c_sel = st.multiselect("🎓 Selecione o Curso:", sorted(cursos_disponiveis), default=cursos_disponiveis)
        
        semestres = df["SEMESTRE"].unique()
        s_sel = st.multiselect("📅 Semestre Acadêmico:", semestres, default=semestres)

    # Aplicação dos filtros
    mask = (df["UNIDADE"].isin(u_sel)) & (df["CURSO"].isin(c_sel)) & (df["SEMESTRE"].isin(s_sel))
    df_filtered = df[mask]

    # --- 4. CABEÇALHO ---
    st.title("📊 Gestão de Procedimentos - FASICLIN")
    st.caption(f"Sincronizado com Google Sheets às {time.strftime('%H:%M:%S')}")

    # --- 5. KPIs COM VALOR AGREGADO ---
    k1, k2, k3, k4 = st.columns(4)
    
    total_atend = int(df_filtered[col_valor].sum())
    # Média baseada nos meses que realmente tiveram dados
    meses_ativos = df_filtered[df_filtered[col_valor] > 0]["MÊS"].nunique()
    media_mensal = total_atend / meses_ativos if meses_ativos > 0 else 0
    
    with k1:
        st.metric("Total de Atendimentos", f"{total_atend:,}".replace(",", "."))
    with k2:
        st.metric("Média/Mês (Ativos)", f"{int(media_mensal):,}".replace(",", "."))
    with k3:
        if not df_filtered.empty:
            top_unidade = df_filtered.groupby("UNIDADE")[col_valor].sum().idxmax()
            st.metric("Unidade em Destaque", top_unidade)
    with k4:
        st.metric("Cursos Monitorados", len(c_sel))

    st.divider()

    # --- 6. GRÁFICOS (LAYOUT MELHORADO) ---
    c1, c2 = st.columns([6, 4]) # Gráfico de linha maior para melhor leitura

    with c1:
        st.subheader("📈 Evolução Temporal")
        # Agrupamento respeitando a ordem dos meses na planilha
        df_evol = df_filtered.groupby("MÊS", sort=False)[col_valor].sum().reset_index()
        fig_line = px.line(df_evol, x="MÊS", y=col_valor, 
                          markers=True, 
                          line_shape="spline",
                          color_discrete_sequence=["#1ABC9C"])
        fig_line.update_layout(hovermode="x unified", yaxis_title="Procedimentos")
        st.plotly_chart(fig_line, use_container_width=True)

    with c2:
        st.subheader("🍩 Distribuição por Curso")
        fig_pie = px.pie(df_filtered, values=col_valor, names="CURSO", 
                         hole=0.5, 
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    # Nova Seção: Comparativo entre Unidades
    st.subheader("🏢 Volume de Procedimentos por Unidade")
    df_unidade = df_filtered.groupby("UNIDADE")[col_valor].sum().reset_index().sort_values(col_valor, ascending=False)
    fig_bar = px.bar(df_unidade, x="UNIDADE", y=col_valor, 
                     color="UNIDADE", 
                     text_auto='.2s',
                     color_discrete_sequence=px.colors.sequential.Viridis)
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- 7. TABELA DETALHADA ---
    with st.expander("📄 Visualizar Tabela de Dados Brutos"):
        st.dataframe(df_filtered, use_container_width=True)

except Exception as e:
    st.error(f"Ocorreu um erro na renderização: {e}")
    st.info("💡 Verifique se o formato da planilha Google Sheets permanece o mesmo.")
