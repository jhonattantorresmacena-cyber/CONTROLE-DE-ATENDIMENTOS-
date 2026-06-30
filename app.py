import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

# 1. Configuração da Página
st.set_page_config(page_title="FASICLIN - Dashboard Premium", layout="wide")

# Estilização CSS para visual Moderno e Clean
st.markdown("""
    <style>
    .kpi-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #004a87;
        margin-bottom: 15px;
    }
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        margin-bottom: 15px;
    }
    .main-title {
        color: #004a87;
        font-weight: 700;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Identificação da Planilha Atualizada e GIDs Fornecidos
SHEET_ID = "1slAr_6YDKRKBqsZK4G6JguD47FD8dz3Oa-9OD8hCYyE"
ABAS_CONFIG = {
    "SINOP": "1049389082",
    "SORRISO": "608902302",       
    "CUIABA": "1444156369",        
    "RONDONOPOLIS": "1726640375",   
    "PRIMAVERA": "470975982"      
}

@st.cache_data(ttl=10)
def load_all_data():
    lista_dfs = []
    cache_buster = int(time.time() // 10) 
    
    for nome_aba, gid in ABAS_CONFIG.items():
        try:
            url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}&cb={cache_buster}"
            df_temp = pd.read_csv(url)
            
            df_temp.columns = [
                str(c).replace('\n', ' ').replace('\r', ' ').strip().upper() 
                for c in df_temp.columns
            ]
            df_temp.columns = [" ".join(c.split()) for c in df_temp.columns]
            
            df_temp['UNIDADE_NOME'] = nome_aba
            lista_dfs.append(df_temp)
        except Exception as e:
            st.sidebar.warning(f"Aba {nome_aba} não pôde ser carregada.")
            
    return pd.concat(lista_dfs, ignore_index=True) if lista_dfs else pd.DataFrame()

df_raw = load_all_data()

if not df_raw.empty:
    COL_CLINICA = "CLINICA"
    COL_ANO = "ANO LETIVO"
    COL_META = "QUANTIDADE DE PROCEDIMENTO POR SEMESTRE"
    MESES = ["FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", "JULHO"]

    if COL_META not in df_raw.columns:
        for c in df_raw.columns:
            if "PROCEDIMENTO" in c and "SEMESTRE" in c:
                COL_META = c
                break

    colunas_numericas = [COL_META] + [m for m in MESES if m in df_raw.columns]
    for c in colunas_numericas:
        if c in df_raw.columns:
            df_raw[c] = pd.to_numeric(df_raw[c], errors='coerce').fillna(0)

    # --- INTERFACE ---
    st.markdown('<h1 class="main-title">🏥 FASICLIN - Gestão de Metas e Produtividade</h1>', unsafe_allow_html=True)

    # Filtros dispostos de forma compacta
    col_u, col_a, col_c = st.columns(3)
    
    with col_u:
        unidades_disponiveis = sorted(df_raw['UNIDADE_NOME'].unique().tolist())
        unidade_sel = st.selectbox("Unidade:", unidades_disponiveis)
    
    df_filtrado = df_raw.copy()
    df_filtrado = df_filtrado[df_filtrado['UNIDADE_NOME'] == unidade_sel]

    with col_a:
        if COL_ANO in df_filtrado.columns:
            anos_disponiveis = sorted(df_filtrado[COL_ANO].dropna().unique().tolist(), reverse=True)
            ano_sel = st.selectbox("Ano Letivo:", anos_disponiveis)
            df_filtrado = df_filtrado[df_filtrado[COL_ANO] == ano_sel]
        else:
            ano_sel = "Geral"

    with col_c:
        clinicas_disponiveis = ["TODAS"] + sorted(df_filtrado[COL_CLINICA].dropna().unique().tolist())
        clinica_sel = st.selectbox("Filtrar por Clínica:", clinicas_disponiveis)

    if clinica_sel != "TODAS":
        df_filtrado = df_filtrado[df_filtrado[COL_CLINICA] == clinica_sel]

    # --- CÁLCULOS EXECUTIVOS ---
    total_meta = df_filtrado[COL_META].sum()
    meses_reais = [m for m in MESES if m in df_filtrado.columns]
    total_realizado = df_filtrado[meses_reais].sum().sum() if meses_reais else 0
    falta = max(0, total_meta - total_realizado)
    perc_total = (total_realizado / total_meta * 100) if total_meta > 0 else 0

    soma_por_mes = df_filtrado[meses_reais].sum() if meses_reais else pd.Series()
    meses_com_dados = sum(soma_por_mes > 0)
    total_meses_periodo = len(meses_reais) if meses_reais else 1
    meses_restantes = max(1, total_meses_periodo - meses_com_dados)
    media_necessaria_mes = int(falta / meses_restantes) if falta > 0 else 0

    st.markdown("---")

    # --- MELHORIA 1: BLOCO DE METRICAS / KPIS PROFISSIONAIS ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f'<div class="kpi-container"><b>🎯 META SEMESTRAL</b><h2>{total_meta:,.0f}</h2><span style="color:gray;">Procedimentos</span></div>', unsafe_allow_html=True)
    with kpi2:
        st.markdown(f'<div class="kpi-container" style="border-left-color: #299947;"><b>✅ REALIZADO ACUMULADO</b><h2>{total_realizado:,.0f}</h2><span style="color:gray;">Atendimentos</span></div>', unsafe_allow_html=True)
    with kpi3:
        cor_status = "#299947" if perc_total >= 100 else "#004a87"
        st.markdown(f'<div class="kpi-container" style="border-left-color: {cor_status};"><b>📈 EFICIÊNCIA DO PERÍODO</b><h2>{perc_total:.1f}%</h2><span style="color:gray;">Geral da Unidade</span></div>', unsafe_allow_html=True)
    with kpi4:
        st.markdown(f'<div class="kpi-container" style="border-left-color: #ff9800;"><b>📅 MÉDIA MENSAL REQUERIDA</b><h2>{media_necessaria_mes:,.0f}</h2><span style="color:gray;">Nos próximos {meses_restantes} meses</span></div>', unsafe_allow_html=True)

    # Mensagem de Sucesso dinâmica simplificada
    if falta == 0:
        st.success(f"🎉 **Excelente!** A meta planejada para {ano_sel} foi totalmente superada!")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- GRÁFICOS APERFEIÇOADOS ---
    c_donut, c_bar = st.columns([1, 2])

    with c_donut:
        fig_donut = go.Figure(data=[go.Pie(
            labels=['Realizado', 'Restante'],
            values=[total_realizado, falta],
            hole=.75,
            marker_colors=['#299947' if perc_total >= 100 else '#004a87', '#f1f3f5'],
            textinfo='none'
        )])
        fig_donut.update_layout(
            annotations=[dict(text=f'Alcançado<br><b>{perc_total:.0f}%</b>', x=0.5, y=0.5, font_size=18, showarrow=False, font_color="#333")],
            showlegend=True, legend=dict(orientation="h", x=0.2, y=-0.1), height=350, margin=dict(t=10, b=10, l=10, r=10)
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with c_bar:
        resumo = df_filtrado.groupby(COL_CLINICA).agg({COL_META: 'sum'}).reset_index()
        resumo['REALIZADO'] = df_filtrado.groupby(COL_CLINICA)[meses_reais].sum().sum(axis=1).values if meses_reais else 0
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name='Realizado', x=resumo[COL_CLINICA], y=resumo['REALIZADO'], marker_color='#299947', text=resumo['REALIZADO'], textposition='auto'))
        fig_bar.add_trace(go.Bar(name='Meta', x=resumo[COL_CLINICA], y=resumo[COL_META], marker_color='#004a87', text=resumo[COL_META], textposition='auto'))
        fig_bar.update_layout(barmode='group', height=350, margin=dict(t=20, b=20), legend=dict(orientation="h", y=1.1, x=0))
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- MELHORIA 2: DETALHAMENTO EM CARDS ELEGANTES ---
    st.markdown('<h3 style="color:#004a87; margin-top:30px;">📋 Detalhamento Estratégico por Clínica</h3>', unsafe_allow_html=True)
    cols = st.columns(3)
    
    for i, (_, row) in enumerate(resumo.iterrows()):
        p_ind = (row['REALIZADO'] / row[COL_META] * 100) if row[COL_META] > 0 else 0
        with cols[i % 3]:
            # Divisão contida no card em HTML para design corporativo
            st.markdown(f"""
            <div class="metric-card">
                <span style="font-size: 16px; font-weight: bold; color: #333;">{row[COL_CLINICA]}</span>
                <hr style="margin: 8px 0; border: 0; border-top: 1px solid #eee;">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: gray;">Realizado: <b>{int(row['REALIZADO'])}</b></span>
                    <span style="color: gray;">Meta: <b>{int(row[COL_META])}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            # Barra de progresso logo abaixo do Card para unificar o design
            st.progress(min(p_ind/100, 1.0))
            st.caption(f"Aproveitamento: {p_ind:.1f}% da meta")
else:
    st.warning("Nenhum dado pôde ser carregado. Certifique-se de que a planilha está aberta para 'Qualquer pessoa com o link'.")
