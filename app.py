import streamlit as st
import pandas as pd
import plotly.express as px
import time

# ==========================================
# 1. CONFIGURAÇÃO E ESTILIZAÇÃO
# ==========================================
st.set_page_config(
    page_title="Dashboard FASICLIN", 
    layout="wide", 
    page_icon="🏥"
)

# Paleta de Cores e CSS
COLOR_PRIMARY = "#1ABC9C" 
COLORS_UNIDADES = {"SINOP": "#3498DB", "SORRISO": "#F1C40F", "CUIABÁ": "#E74C3C"}

st.markdown(f"""
    <style>
    .stApp {{ background-color: #F4F7F6; }}
    [data-testid="stMetricValue"] {{ font-size: 32px; color: {COLOR_PRIMARY}; font-weight: 800; }}
    .plot-container {{
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #EAEAEA;
        margin-bottom: 25px;
    }}
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
    
    for col in ['UNIDADE', 'CURSO', 'MÊS']:
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
# 3. SIDEBAR E FILTROS
# ==========================================
with st.sidebar:
    st.markdown("## ⚙️ Filtros")
    if st.button("🔄 Sincronizar Dados"):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    u_sel = st.multiselect("📍 Unidades", sorted(df["UNIDADE"].unique()), default=df["UNIDADE"].unique())
    cursos_disponiveis = df[df["UNIDADE"].isin(u_sel)]["CURSO"].unique()
    c_sel = st.multiselect("🎓 Cursos", sorted(cursos_disponiveis), default=cursos_disponiveis)
    s_sel = st.multiselect("📅 Semestre", sorted(df["SEMESTRE"].unique()), default=df["SEMESTRE"].unique())

mask = (df["UNIDADE"].isin(u_sel)) & (df["CURSO"].isin(c_sel)) & (df["SEMESTRE"].isin(s_sel))
df_filtered = df[mask]

# ==========================================
# 4. CABEÇALHO (LOGO E KPIs)
# ==========================================
# 1- Logo no lugar do texto (ajuste o link se necessário)
c_logo, c_info = st.columns([8, 2])
with c_logo:
    st.image("https://www.fasiclin.com.br/wp-content/uploads/2021/08/logo-fasiclin.png", width=250)
with c_info:
    st.markdown(f"<div style='text-align:right; color:#7F8C8D;'>Sincronizado:<br><b>{time.strftime('%d/%m/%Y %H:%M')}</b></div>", unsafe_allow_html=True)

st.markdown("---")

# KPIs
k1, k2, k3, k4 = st.columns(4)
total_atend = int(df_filtered[col_valor].sum())
k1.metric("Total Procedimentos", f"{total_atend:,}".replace(",", "."))
k2.metric("Média Mensal", f"{int(total_atend/df_filtered['MÊS'].nunique()) if not df_filtered.empty else 0}")
k3.metric("Unidades Ativas", len(u_sel))
k4.metric("Cursos Ativos", len(c_sel))

# ==========================================
# 5. ESTRUTURA VERTICAL DE GRÁFICOS
# ==========================================

# Função auxiliar para limpar layout dos gráficos
def clean_chart(fig):
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, b=20))
    return fig

# 2- Gráfico de Tendência (Tela Cheia)
st.markdown('<div class="plot-container">', unsafe_allow_html=True)
st.subheader("📈 Tendência de Atendimentos no Tempo")
df_evol = df_filtered.groupby(["MÊS", "UNIDADE"], sort=False)[col_valor].sum().reset_index()
fig_line = px.line(df_evol, x="MÊS", y=col_valor, color="UNIDADE", markers=True, color_discrete_map=COLORS_UNIDADES)
st.plotly_chart(clean_chart(fig_line), use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# 3- Estatística de Procedimento (Abaixo da tendência)
st.markdown('<div class="plot-container">', unsafe_allow_html=True)
st.subheader("🍩 Estatística de Procedimento")
fig_pie = px.pie(df_filtered, values=col_valor, names="CURSO", hole=0.5, color_discrete_sequence=px.colors.qualitative.Safe)
st.plotly_chart(clean_chart(fig_pie), use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# Comparativo de Semestre
st.markdown('<div class="plot-container">', unsafe_allow_html=True)
st.subheader("📊 Comparativo de Volume Total por Unidade e Semestre")
df_un_sem = df_filtered.groupby(["UNIDADE", "SEMESTRE"])[col_valor].sum().reset_index()
fig_sem = px.bar(df_un_sem, x="UNIDADE", y=col_valor, color="SEMESTRE", barmode="group", text_auto='.2s')
st.plotly_chart(clean_chart(fig_sem), use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# 4- Ranking de Unidades (Barras Agrupadas)
st.markdown('<div class="plot-container">', unsafe_allow_html=True)
st.subheader("🏆 Ranking de Unidades por Procedimentos")
df_rank = df_filtered.groupby("UNIDADE")[col_valor].sum().reset_index().sort_values(col_valor, ascending=False)
fig_rank = px.bar(df_rank, x=col_valor, y="UNIDADE", orientation='h', 
                  text_auto='.2s', color="UNIDADE", color_discrete_map=COLORS_UNIDADES)
fig_rank.update_layout(yaxis={'categoryorder':'total ascending'})
st.plotly_chart(clean_chart(fig_rank), use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)
