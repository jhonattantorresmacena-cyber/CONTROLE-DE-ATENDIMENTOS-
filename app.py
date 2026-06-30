import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

# 1. Configuração da Página
st.set_page_config(page_title="FASICLIN - Dashboard Premium", layout="wide")

# Estilização para os cards de detalhamento
st.markdown("""
    <style>
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #eee;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
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

@st.cache_data(ttl=10)  # Cache curto para atualização rápida
def load_all_data():
    lista_dfs = []
    cache_buster = int(time.time() // 10) 
    
    for nome_aba, gid in ABAS_CONFIG.items():
        try:
            url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}&cb={cache_buster}"
            df_temp = pd.read_csv(url)
            
            # Limpeza rigorosa de cabeçalhos (tudo para maiúsculo e sem quebras de linha)
            df_temp.columns = [
                str(c).replace('\n', ' ').replace('\r', ' ').strip().upper() 
                for c in df_temp.columns
            ]
            df_temp.columns = [" ".join(c.split()) for c in df_temp.columns]
            
            df_temp['UNIDADE_NOME'] = nome_aba
            lista_dfs.append(df_temp)
        except Exception as e:
            st.sidebar.warning(f"Aba {nome_aba} não pôde ser carregada. Verifique o link/permissão.")
            
    return pd.concat(lista_dfs, ignore_index=True) if lista_dfs else pd.DataFrame()

df_raw = load_all_data()

if not df_raw.empty:
    # --- MAPEAMENTO EXATO DAS COLUNAS ---
    COL_CLINICA = "CLINICA"
    COL_ANO = "ANO LETIVO"
    COL_META = "QUANTIDADE DE PROCEDIMENTO POR SEMESTRE"
    MESES = ["FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", "JULHO"]

    # Validação de segurança para garantir que a coluna exata de metas existe
    if COL_META not in df_raw.columns:
        # Busca por aproximação caso haja divergência mínima de acentuação/espaço
        fallback_meta = None
        for c in df_raw.columns:
            if "PROCEDIMENTO" in c and "SEMESTRE" in c:
                fallback_meta = c
                break
        if fallback_meta:
            COL_META = fallback_meta
        else:
            st.error(f"Coluna de metas '{COL_META}' não encontrada. Colunas disponíveis: {list(df_raw.columns)}")
            st.stop()

    # Garantir formato numérico puro nas colunas de valores
    colunas_numericas = [COL_META] + [m for m in MESES if m in df_raw.columns]
    for c in colunas_numericas:
        if c in df_raw.columns:
            df_raw[c] = pd.to_numeric(df_raw[c], errors='coerce').fillna(0)

    # --- INTERFACE ---
    st.title("🏥 FASICLIN - Dashboard de Produtividade")

    # Filtros superiores
    col_u, col_a, col_c = st.columns(3)
    
    with col_u:
        unidades_disponiveis = sorted(df_raw['UNIDADE_NOME'].unique().tolist())
        unidade_sel = st.selectbox("Selecione a Unidade", unidades_disponiveis)
    
    df_filtrado = df_raw.copy()
    df_filtrado = df_filtrado[df_filtrado['UNIDADE_NOME'] == unidade_sel]

    with col_a:
        if COL_ANO in df_filtrado.columns:
            anos_disponiveis = sorted(df_filtrado[COL_ANO].dropna().unique().tolist(), reverse=True)
            ano_sel = st.selectbox("Ano Letivo", anos_disponiveis)
            df_filtrado = df_filtrado[df_filtrado[COL_ANO] == ano_sel]
        else:
            ano_sel = "Geral"
            st.selectbox("Ano Letivo", ["Padrão"], disabled=True)

    with col_c:
        clinicas_disponiveis = ["TODAS"] + sorted(df_filtrado[COL_CLINICA].dropna().unique().tolist())
        clinica_sel = st.selectbox("Filtrar Clínica", clinicas_disponiveis)

    if clinica_sel != "TODAS":
        df_filtrado = df_filtrado[df_filtrado[COL_CLINICA] == clinica_sel]

    # --- CÁLCULOS DINÂMICOS ---
    total_meta = df_filtrado[COL_META].sum()
    meses_reais = [m for m in MESES if m in df_filtrado.columns]
    total_realizado = df_filtrado[meses_reais].sum().sum() if meses_reais else 0
    falta = max(0, total_meta - total_realizado)
    perc_total = (total_realizado / total_meta * 100) if total_meta > 0 else 0

    # Descobrir meses ativos com dados inseridos
    soma_por_mes = df_filtrado[meses_reais].sum() if meses_reais else pd.Series()
    meses_com_dados = sum(soma_por_mes > 0)
    total_meses_periodo = len(meses_reais) if meses_reais else 1
    meses_restantes = max(1, total_meses_periodo - meses_com_dados)

    media_necessaria_mes = int(falta / meses_restantes) if falta > 0 else 0

    # Banner informativo
    if falta > 0:
        st.info(f"**Acompanhamento de Metas ({ano_sel}):** Faltam **{falta:.0f}** procedimentos para atingir a meta total. "
                f"Média necessária: **{media_necessaria_mes}** procedimentos/mês nos meses restantes ({meses_restantes}).")
    else:
        st.success(f"🎉 **Parabéns!** A meta de {total_meta:.0f} atendimentos para {ano_sel} foi atingida! (Realizado: {total_realizado:.0f})")

    # Gráficos
    c_donut, c_bar = st.columns([1, 2])

    with c_donut:
        fig_donut = go.Figure(data=[go.Pie(
            labels=['Realizado', 'Pendente'],
            values=[total_realizado, falta],
            hole=.8,
            marker_colors=['#299947' if perc_total >= 100 else '#004a87', '#f2f2f2'],
            textinfo='none'
        )])
        fig_donut.update_layout(
            annotations=[dict(text=f'Eficiência<br><b>{perc_total:.0f}%</b>', x=0.5, y=0.5, font_size=20, showarrow=False)],
            showlegend=False, height=350, margin=dict(t=0, b=0, l=0, r=0)
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with c_bar:
        resumo = df_filtrado.groupby(COL_CLINICA).agg({COL_META: 'sum'}).reset_index()
        resumo['REALIZADO'] = df_filtrado.groupby(COL_CLINICA)[meses_reais].sum().sum(axis=1).values if meses_reais else 0
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name='Realizado', x=resumo[COL_CLINICA], y=resumo['REALIZADO'], marker_color='#299947'))
        fig_bar.add_trace(go.Bar(name='Meta', x=resumo[COL_CLINICA], y=resumo[COL_META], marker_color='#004a87'))
        fig_bar.update_layout(barmode='group', height=350, margin=dict(t=20, b=20), legend=dict(orientation="h", y=11))
        st.plotly_chart(fig_bar, use_container_width=True)

    # Detalhamento
    st.subheader("Detalhamento por Clínica")
    cols = st.columns(3)
    for i, (_, row) in enumerate(resumo.iterrows()):
        p_ind = (row['REALIZADO'] / row[COL_META] * 100) if row[COL_META] > 0 else 0
        with cols[i % 3]:
            with st.container():
                st.markdown(f"**{row[COL_CLINICA]}**")
                st.metric(label="Realizado", value=int(row['REALIZADO']), delta=f"{p_ind:.1f}% da meta")
                st.progress(min(p_ind/100, 1.0))
                st.caption(f"Meta: {int(row[COL_META])}")
                st.markdown("---")
else:
    st.warning("Nenhum dado pôde ser carregado. Certifique-se de que a planilha está aberta para 'Qualquer pessoa com o link'.")
