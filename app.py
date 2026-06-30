import streamlit as st
import pandas as pd
import plotly.express as px
import time
from streamlit_option_menu import option_menu

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILIZAÇÃO CSS
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
# 2. CARREGAMENTO E PADRONIZAÇÃO DOS DADOS (API)
# ==========================================
@st.cache_data(ttl=600)
def load_data():
    URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpHTm4l6jKCsZTLaSJjDZn-TYdaoxla54U9hhkJLdBe_HC5QNrWleCaLkq7_UglTMXP-muYt4hNKAI/pub?output=csv"
    df = pd.read_csv(f"{URL}&refresh={time.time()}")
    
    # 2.1 Padronização dos nomes das colunas (Sempre em Maiúsculo)
    df.columns = [str(col).strip().upper() for col in df.columns]
    
    # 2.2 Localização dinâmica da coluna de ANO para evitar quebras por variação de nome
    col_ano = None
    for col in df.columns:
        if "ANO" in col:
            col_ano = col
            break
            
    if not col_ano:
        col_ano = "ANO"
        df[col_ano] = "N/A"
    
    # 2.3 Tratamento de strings e preenchimento de vazios
    for col in df.columns:
        if col in ['UNIDADE', 'CURSO', 'MÊS', 'SEMESTRE', col_ano]:
            df[col] = df[col].astype(str).str.strip().str.upper()

    # 2.4 Ordenação lógica e categórica dos meses do ano
    ordem_meses = ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
                   "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
    if 'MÊS' in df.columns:
        df['MÊS'] = pd.Categorical(df['MÊS'], categories=ordem_meses, ordered=True)
            
    # 2.5 Identificação dinâmica e conversão da coluna de valores numéricos
    target_col = None
    for col in df.columns:
        if "QUANTIDADE" in col and "ANO" not in col:
            target_col = col
            break
    
    if not target_col:
        colunas_numericas = df.select_dtypes(include=['number']).columns
        colunas_filtradas = [c for c in colunas_numericas if "ANO" not in c]
        target_col = colunas_filtradas[-1] if colunas_filtradas else colunas_numericas[-1]

    df[target_col] = pd.to_numeric(df[target_col], errors='coerce').fillna(0)
    
    # Define por padrão que toda informação extraída diretamente da planilha é um dado de execução real
    df["TIPO"] = "REALIZADO"
    
    return df, target_col, col_ano


# ==========================================
# 3. MOTOR DE INTELIGÊNCIA: PROJEÇÃO DE METAS
# ==========================================
def injetar_metas_projetadas(df, col_valor, col_ano, taxa_crescimento=0.10):
    """
    Agrupa o histórico de atendimentos reais por Unidade, Curso e Mês e
    gera projeções automáticas de metas para os anos de 2025 e 2026.
    """
    df[col_ano] = df[col_ano].astype(str).str.strip()
    
    # Filtra e agrupa apenas com base nos registros que já aconteceram
    df_historico = df[df["TIPO"] == "REALIZADO"]
    
    base_metas = df_historico.groupby(["UNIDADE", "CURSO", "MÊS", "SEMESTRE"], observed=False)[col_valor].mean().reset_index()
    base_metas.rename(columns={col_valor: "MEDIA_HISTORICA"}, inplace=True)
    
    novas_linhas = []
    
    # Geração dos cenários futuros aplicando juros compostos de crescimento
    for ano_proj in ["2025", "2026"]:
        multiplicador = (1 + taxa_crescimento) if ano_proj == "2025" else (1 + taxa_crescimento) ** 2
        
        for _, row in base_metas.iterrows():
            meta_calculada = round(row["MEDIA_HISTORICA"] * multiplicador, 0)
            
            nova_linha = {
                "UNIDADE": row["UNIDADE"],
                "CURSO": row["CURSO"],
                "MÊS": row["MÊS"],
                "SEMESTRE": row["SEMESTRE"],
                col_ano: ano_proj,
                col_valor: meta_calculada,
                "TIPO": "META"
            }
            novas_linhas.append(nova_linha)
            
    if novas_linhas:
        df_metas = pd.DataFrame(novas_linhas)
        df = pd.concat([df, df_metas], ignore_index=True)
        
    return df


# Inicialização segura do pipeline de dados
try:
    df, col_valor, col_ano = load_data()
    # Adiciona as metas calculadas à base com o crescimento estabelecido
    df = injetar_metas_projetadas(df, col_valor, col_ano, taxa_crescimento=0.10)
except Exception as e:
    st.error(f"Erro de processamento no Pipeline de Dados: {e}")
    st.stop()


# ==========================================
# 4. DESIGN DO CABEÇALHO SINCRO
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
# 5. INTERFACE DO USUÁRIO: COMPONENTES E FILTROS
# ==========================================
def get_options(column_name, default_label, reverse=False):
    if column_name in df.columns:
        valores = df[column_name].astype(str).unique().tolist()
        return [default_label] + sorted(valores, reverse=reverse)
    return [default_label]

# --- Filtro 01: Procedimento / Curso ---
st.markdown('<p class="filter-label">🎯 PROCEDIMENTO / CURSO</p>', unsafe_allow_html=True)
lista_cursos = get_options("CURSO", "TODOS OS CURSOS")
c_sel_raw = st.selectbox("", lista_cursos, key="filtro_curso", label_visibility="collapsed")
c_sel = df["CURSO"].unique() if c_sel_raw == "TODOS OS CURSOS" else [c_sel_raw]

# --- Filtro 02: Menu de Unidades ---
st.markdown('<p class="filter-label">📍 UNIDADES</p>', unsafe_allow_html=True)
lista_unidades = get_options("UNIDADE", "TODAS")
u_sel_raw = option_menu(None, lista_unidades, 
    icons=['house'] + ['geo-alt']*(len(lista_unidades)-1), 
    menu_icon="cast", default_index=0, orientation="horizontal",
    styles={"nav-link-selected": {"background-color": "#1ABC9C"}}, 
    key="filtro_unidade"
)
u_sel = df["UNIDADE"].unique() if u_sel_raw == "TODAS" else [u_sel_raw]

# --- Filtro 03: Menu de Anos ---
st.markdown('<p class="filter-label">📅 ANO DE REFERÊNCIA</p>', unsafe_allow_html=True)
if df[col_ano].iloc[0] == "N/A":
    st.warning("⚠️ Nenhuma coluna de 'ANO' localizada nos dados originais.")
    a_sel = df[col_ano].unique()
else:
    lista_anos = get_options(col_ano, "TODOS OS ANOS", reverse=False)
    a_sel_raw = option_menu(None, lista_anos, 
        icons=['calendar4-range'] + ['calendar3']*(len(lista_anos)-1), 
        menu_icon="cast", default_index=0, orientation="horizontal",
        styles={"nav-link-selected": {"background-color": "#2C3E50"}}, 
        key="filtro_ano"
    )
    a_sel = df[col_ano].unique() if a_sel_raw == "TODOS OS ANOS" else [a_sel_raw]

# --- Filtro 04: Menu de Semestres ---
st.markdown('<p class="filter-label">📅 SEMESTRE</p>', unsafe_allow_html=True)
lista_semestres = get_options("SEMESTRE", "TODOS")
s_sel_raw = option_menu(None, lista_semestres, 
    icons=['calendar'] + ['calendar-check']*(len(lista_semestres)-1), 
    menu_icon="cast", default_index=0, orientation="horizontal",
    styles={"nav-link-selected": {"background-color": "#3498DB"}}, 
    key="filtro_semestre"
)
s_sel = df["SEMESTRE"].unique() if s_sel_raw == "TODOS" else [s_sel_raw]

# Aplicação da máscara de filtros unificada
mask = (df["UNIDADE"].isin(u_sel)) & (df["CURSO"].isin(c_sel)) & (df["SEMESTRE"].isin(s_sel)) & (df[col_ano].isin(a_sel))
df_filtered = df[mask]


# ==========================================
# 6. CENTRAL DE MÉTRICAS (KPIs) & GRÁFICOS
# ==========================================
st.markdown("<br>", unsafe_allow_html=True)
k1, k2, k3 = st.columns(3)

# Filtro interno para exibir apenas dados reais consolidados nos indicadores analíticos
total_realizado = int(df_filtered[df_filtered["TIPO"] == "REALIZADO"][col_valor].sum())

with k1: 
    st.metric("Total Realizado", f"{total_realizado:,}".replace(",", "."))
with k2: 
    st.metric("Cursos Ativos", len(df_filtered["CURSO"].unique()))
with k3: 
    st.metric("Média por Unidade (Real)", f"{int(total_realizado/len(u_sel)) if len(u_sel)>0 else 0}")


def style_fig(fig):
    """Aplica o tema visual transparente e limpo nos gráficos do Plotly."""
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", 
        paper_bgcolor="rgba(0,0,0,0)", 
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="#EEE")
    )
    return fig


# 6.1 Painel Principal: Comparativo Realizado vs Meta por Mês
st.markdown('<p class="filter-label">📊 COMPARATIVO ANUAL: REALIZADO VS META EM ATENDIMENTOS</p>', unsafe_allow_html=True)
df_comp = df_filtered.groupby(["MÊS", "TIPO"], observed=False)[col_valor].sum().reset_index()

fig_bar_comp = px.bar(
    df_comp, x="MÊS", y=col_valor, color="TIPO", barmode="group",
    color_discrete_map={"REALIZADO": "#1ABC9C", "META": "#34495E"},
    text_auto='.2s'
)
st.plotly_chart(style_fig(fig_bar_comp), use_container_width=True)


# Painel Secundário dividido em colunas balanceadas
c1, c2 = st.columns(2)

with c1:
    st.markdown('<p class="filter-label">🍩 DISTRIBUIÇÃO VOLUMÉTRICA POR CURSO (REALIZADO)</p>', unsafe_allow_html=True)
    df_pie_data = df_filtered[df_filtered["TIPO"] == "REALIZADO"]
    fig_pie = px.pie(
        df_pie_data, values=col_valor, names="CURSO", hole=0.5,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    st.plotly_chart(style_fig(fig_pie), use_container_width=True)

with c2:
    st.markdown('<p class="filter-label">🏆 RANKING PERFORMANCE: UNIDADES (REALIZADO)</p>', unsafe_allow_html=True)
    df_rank_data = df_filtered[df_filtered["TIPO"] == "REALIZADO"]
    df_rank = df_rank_data.groupby("UNIDADE")[col_valor].sum().reset_index().sort_values(col_valor, ascending=True)
    
    fig_rank = px.bar(
        df_rank, x=col_valor, y="UNIDADE", orientation='h', 
        text_auto='.2s', color_discrete_sequence=["#1ABC9C"]
    )
    st.plotly_chart(style_fig(fig_rank), use_container_width=True)
