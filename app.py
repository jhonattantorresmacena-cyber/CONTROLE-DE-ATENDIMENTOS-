import streamlit as st
import pandas as pd
import plotly.express as px
import time

# ==========================================
# 1. CONFIGURAÇÃO E ESTILIZAÇÃO PREMIUM
# ==========================================
st.set_page_config(
    page_title="FASICLIN | Analytics Hub", 
    layout="wide", 
    page_icon="🏥"
)

# Paleta de Cores FASICLIN (Definição de Identidade Visual)
COLOR_PRIMARY = "#1ABC9C"  # Turquesa
COLOR_BG = "#F4F7F6"       # Cinza muito claro
COLORS_UNIDADES = {
    "SINOP": "#3498DB",    # Azul
    "SORRISO": "#F1C40F",   # Amarelo
    "CUIABÁ": "#E74C3C"     # Vermelho
}

# Injeção de CSS para customização avançada
st.markdown(f"""
    <style>
    /* Fundo da aplicação */
    .stApp {{ background-color: {COLOR_BG}; }}
    
    /* Customização da Sidebar */
    [data-testid="stSidebar"] {{ background-color: white; border-right: 1px solid #E0E0E0; }}
    
    /* Títulos e Subtítulos */
    h1 {{ color: #2C3E50; font-weight: 800; padding-bottom: 0px; }}
    h2 {{ color: #34495E; font-weight: 600; padding-top: 10px; border-bottom: 2px solid {COLOR_PRIMARY}; padding-bottom: 5px; }}
    h3 {{ color: #7F8C8D; font-size: 1.1rem; font-weight: 400; margin-top: -15px; margin-bottom: 25px; }}

    /* Estilização dos Cards de Métrica */
    [data-testid="stMetricValue"] {{ font-size: 32px; color: {COLOR_PRIMARY}; font-weight: 800; }}
    [data-testid="stMetricLabel"] {{ font-size: 14px; color: #7F8C8D; font-weight: 600; text-transform: uppercase; }}
    [data-testid="stMetricDiv"] {{ 
        background-color: white; 
        padding: 20px; 
        border-radius: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
        border: 1px solid #EAEAEA;
    }}

    /* Estilização dos Contêineres de Gráficos (Cards) */
    .plot-container {{
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #EAEAEA;
        margin-bottom: 20px;
    }}
    
    /* Botão Customizado */
    div.stButton > button:first-child {{
        background-color: {COLOR_PRIMARY};
        color: white;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        width: 100%;
    }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. FUNÇÃO DE DADOS (CACHE E TRATAMENTO)
# ==========================================
@st.cache_data(ttl=600)
def load_data():
    # URL da planilha publicada como CSV
    URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpHTm4l6jKCsZTLaSJjDZn-TYdaoxla54U9hhkJLdBe_HC5QNrWleCaLkq7_UglTMXP-muYt4hNKAI/pub?output=csv"
    
    try:
        # Adiciona refresh para evitar cache do Google
        df = pd.read_csv(f"{URL}&refresh={time.time()}")
        
        # 2.1 Limpeza e Padronização
        df.columns = [str(col).strip().upper() for col in df.columns]
        
        for col in ['UNIDADE', 'CURSO', 'MÊS']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.upper()

        # 2.2 Identificação inteligente da coluna de valores
        target_col = "QUANTIDADE_PROCEDIMENTO"
        for col in df.columns:
            if "QUANTIDADE" in col:
                target_col = col
                break
                
        # 2.3 Conversão numérica
        df[target_col] = pd.to_numeric(df[target_col], errors='coerce').fillna(0)
        
        return df, target_col
    except Exception as e:
        st.error(f"Erro ao carregar dados da planilha: {e}")
        return pd.DataFrame(), ""

# Carregamento inicial
df, col_valor = load_data()

if df.empty:
    st.stop() # Interrompe se não houver dados

# ==========================================
# 3. SIDEBAR (FILTROS DESIGN-FORWARD)
# ==========================================
with st.sidebar:
    st.image("https://www.fasiclin.com.br/wp-content/uploads/2021/08/logo-fasiclin.png", width=150) # Tente colocar logo oficial aqui
    st.markdown("## Painel de Controle")
    
    if st.button("🔄 Sincronizar Dados Atualizados"):
        st.cache_data.clear()
        st.toast('Sincronizando com Google Sheets...', icon='⏳')
        time.sleep(1)
        st.rerun()

    st.divider()
    
    st.markdown("### Seleção de Escopo")
    u_sel = st.multiselect("📍 Unidades", sorted(df["UNIDADE"].unique()), default=df["UNIDADE"].unique())
    
    # Filtro dinâmico de curso
    cursos_disponiveis = df[df["UNIDADE"].isin(u_sel)]["CURSO"].unique()
    c_sel = st.multiselect("🎓 Cursos", sorted(cursos_disponiveis), default=cursos_disponiveis)
    
    semestres = sorted(df["SEMESTRE"].unique())
    s_sel = st.multiselect("📅 Semestre Acadêmico", semestres, default=semestres)

    st.divider()
    st.caption("FASICLIN Analytics v2.1 | Desenvolvido internamente")

# Aplicação dos filtros
mask = (df["UNIDADE"].isin(u_sel)) & (df["CURSO"].isin(c_sel)) & (df["SEMESTRE"].isin(s_sel))
df_filtered = df[mask]

# ==========================================
# 4. CABEÇALHO E KPIs (CARD STYLE)
# ==========================================
# Layout do título com hora da atualização
c_title, c_time = st.columns([8, 2])
with c_title:
    st.title("Hub de Procedimentos Clínicos")
    st.markdown("### Monitoramento em tempo real da produtividade acadêmica")
with c_time:
    st.markdown(f"""
        <div style='text-align: right; color: #7F8C8D; padding-top: 20px;'>
        Sincronizado às:<br>
        <b style='color: {COLOR_PRIMARY}; font-size: 1.2rem;'>{time.strftime('%H:%M')}</b>
        </div>
    """, unsafe_allow_html=True)

# Seção de KPIs
st.markdown("## Indicadores Chave (KPIs)")
k1, k2, k3, k4 = st.columns(4)

total_atend = int(df_filtered[col_valor].sum())
meses_ativos = df_filtered[df_filtered[col_valor] > 0]["MÊS"].nunique()
media_mensal = total_atend / meses_ativos if meses_ativos > 0 else 0

k1.metric("Total de Atendimentos", f"{total_atend:,}".replace(",", "."))
k2.metric("Média Mensal (Ativos)", f"{int(media_mensal):,}".replace(",", "."))

if not df_filtered.empty:
    top_unidade = df_filtered.groupby("UNIDADE")[col_valor].sum().idxmax()
    k3.metric("Unidade Líder", top_unidade)
else:
    k3.metric("Unidade Líder", "N/A")

k4.metric("Cursos em Análise", len(c_sel))

st.markdown("<br>", unsafe_allow_html=True) # Espaçador

# ==========================================
# 5. ÁREA DE ANÁLISE VISUAL (GRÁFICOS)
# ==========================================
st.markdown("## Análise Detalhada")

# Configuração Padrão do Layout Plotly (limpo)
def update_plot_layout(fig):
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_xaxes(showgrid=False, color="#7F8C8D")
    fig.update_yaxes(showgrid=True, gridcolor="#EAEAEA", color="#7F8C8D")
    return fig

# --- LINHA 1 ---
c_line, c_pie = st.columns([6, 4])

with c_line:
    st.markdown('<div class="plot-container">', unsafe_allow_html=True)
    st.markdown("### Tendência de Atendimentos no Tempo")
    # Agrupamento respeitando a ordem dos meses na planilha
    df_evol = df_filtered.groupby(["MÊS", "UNIDADE"], sort=False)[col_valor].sum().reset_index()
    
    fig_line = px.line(df_evol, x="MÊS", y=col_valor, 
                      color="UNIDADE",
                      markers=True, 
                      line_shape="spline",
                      color_discrete_map=COLORS_UNIDADES) # Cores fixas
    
    fig_line.update_traces(line=dict(width=3), marker=dict(size=8))
    st.plotly_chart(update_plot_layout(fig_line), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c_pie:
    st.markdown('<div class="plot-container">', unsafe_allow_html=True)
    st.markdown("### Mix de Produção por Curso")
    fig_pie = px.pie(df_filtered, values=col_valor, names="CURSO", 
                     hole=0.5, 
                     color_discrete_sequence=px.colors.qualitative.Safe)
    fig_pie.update_traces(textposition='inside', textinfo='percent')
    fig_pie.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_pie, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- LINHA 2 (Comparativo) ---
st.markdown('<div class="plot-container">', unsafe_allow_html=True)
st.markdown("### Comparativo de Volume Total por Unidade e Semestre")

# Tabela dinâmica para barras empilhadas
df_un_sem = df_filtered.groupby(["UNIDADE", "SEMESTRE"])[col_valor].sum().reset_index()

fig_bar = px.bar(df_un_sem, x="UNIDADE", y=col_valor, 
                 color="SEMESTRE", 
                 barmode="group", # Barras lado a lado para comparar semestre
                 text_auto='.2s',
                 color_discrete_sequence=px.colors.sequential.Teal)

# Aplica cores fixas nas bordas para identidade
fig_bar.update_traces(marker_line_color='white', marker_line_width=1.5, opacity=0.9)
st.plotly_chart(update_plot_layout(fig_bar), use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# 6. RODAPÉ E DADOS BRUTOS
# ==========================================
st.markdown("<br><hr>", unsafe_allow_html=True)
with st.expander("📄 Acessar Base de Dados Filtrada (Auditoria)"):
    st.dataframe(df_filtered, use_container_width=True)
