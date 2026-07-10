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
    .growth-indicator {
        font-size: 14px;
        font-weight: bold;
        margin-top: 5px;
        display: block;
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

# --- SUBSTITUIÇÃO DA LÓGICA DINÂMICA DE MESES ---
if not df_raw.empty:
    COL_CLINICA = "CLINICA"
    COL_ANO = "ANO LETIVO"
    COL_META = "QUANTIDADE DE PROCEDIMENTO POR SEMESTRE"
    COL_ALUNOS = "QUANTIDADE DE ALUNOS"
    
    # Lista global com todos os meses possíveis do ano para garantir a extração futura
    TODOS_OS_MESES_ANO = [
        "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
        "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"
    ]
    
    # Identifica dinamicamente quais desses meses existem como colunas na planilha atual
    MESES_DETECTADOS = [m for m in TODOS_OS_MESES_ANO if m in df_raw.columns]

    if COL_META not in df_raw.columns:
        for c in df_raw.columns:
            if "PROCEDIMENTO" in c and "SEMESTRE" in c:
                COL_META = c
                break

    # Configura as colunas numéricas com base nos meses reais encontrados na planilha
    colunas_numericas = [COL_META] + MESES_DETECTADOS
    if COL_ALUNOS in df_raw.columns:
        colunas_numericas.append(COL_ALUNOS)

    for c in colunas_numericas:
        if c in df_raw.columns:
            df_raw[c] = pd.to_numeric(df_raw[c], errors='coerce').fillna(0)

    # Cria a coluna com o Total Realizado somando apenas os meses existentes de forma dinâmica
    df_raw['TOTAL_REALIZADO_LINHA'] = df_raw[MESES_DETECTADOS].sum(axis=1)
    # ------------------------------------------------

    # --- INTERFACE ---
    st.markdown('<h1 class="main-title">🏥 FASICLIN - Gestão de Metas e Produtividade</h1>', unsafe_allow_html=True)

    # Filtros dispostos de forma compacta
    col_u, col_a, col_c = st.columns(3)
    
    with col_u:
        ordem_unidades = ["SINOP", "SORRISO", "CUIABA", "RONDONOPOLIS", "PRIMAVERA"]
        unidades_disponiveis = [u for u in ordem_unidades if u in df_raw['UNIDADE_NOME'].unique().tolist()]
        for u in df_raw['UNIDADE_NOME'].unique():
            if u not in unidades_disponiveis:
                unidades_disponiveis.append(u)
                
        unidade_sel = st.selectbox("Unidade:", unidades_disponiveis)
    
    df_unidade = df_raw[df_raw['UNIDADE_NOME'] == unidade_sel].copy()

    with col_a:
        if COL_ANO in df_unidade.columns:
            anos_disponiveis = ["TODOS"] + sorted(df_unidade[COL_ANO].dropna().unique().tolist(), reverse=True)
            ano_sel = st.selectbox("Ano Letivo Principal (para os KPIs):", anos_disponiveis)
        else:
            ano_sel = "Geral"

    if ano_sel == "TODOS" or ano_sel == "Geral":
        df_filtrado = df_unidade.copy()
    else:
        df_filtrado = df_unidade[df_unidade[COL_ANO] == ano_sel]

    with col_c:
        clinicas_disponiveis = ["TODAS"] + sorted(df_filtrado[COL_CLINICA].dropna().unique().tolist())
        clinica_sel = st.selectbox("Filtrar por Clínica:", clinicas_disponiveis)

    df_kpi_atual = df_filtrado.copy()
    if clinica_sel != "TODAS":
        df_kpi_atual = df_kpi_atual[df_kpi_atual[COL_CLINICA] == clinica_sel]

    # --- CÁLCULOS EXECUTIVOS ---
    total_meta = df_kpi_atual[COL_META].sum()
    total_realizado = df_kpi_atual['TOTAL_REALIZADO_LINHA'].sum()
    falta = max(0, total_meta - total_realizado)
    perc_total = (total_realizado / total_meta * 100) if total_meta > 0 else 0
    total_alunos = df_kpi_atual[COL_ALUNOS].sum() if COL_ALUNOS in df_kpi_atual.columns else 0

    # --- LÓGICA DO INDICATIVO DE CRESCIMENTO ---
    texto_crescimento = '<span style="color:gray; font-size:12px;">Primeiro período registrado</span>'
    
    if COL_ANO in df_unidade.columns and ano_sel != "TODOS" and ano_sel != "Geral":
        anos_validos = sorted(df_unidade[COL_ANO].dropna().unique().tolist(), reverse=True)
        try:
            idx_ano_atual = anos_validos.index(ano_sel)
            if idx_ano_atual < len(anos_validos) - 1:
                ano_anterior = anos_validos[idx_ano_atual + 1]
                
                df_ano_ant = df_unidade[df_unidade[COL_ANO] == ano_anterior]
                if clinica_sel != "TODAS":
                    df_ano_ant = df_ano_ant[df_ano_ant[COL_CLINICA] == clinica_sel]
                
                total_realizado_anterior = df_ano_ant['TOTAL_REALIZADO_LINHA'].sum()
                
                if total_realizado_anterior > 0:
                    variacao = ((total_realizado - total_realizado_anterior) / total_realizado_anterior) * 100
                    if variacao >= 0:
                        texto_crescimento = f'<span class="growth-indicator" style="color:#299947;">▲ +{variacao:.1f}%</span> <span style="color:gray; font-size:12px;">vs {ano_anterior}</span>'
                    else:
                        texto_crescimento = f'<span class="growth-indicator" style="color:#d32f2f;">▼ {variacao:.1f}%</span> <span style="color:gray; font-size:12px;">vs {ano_anterior}</span>'
                else:
                    texto_crescimento = '<span style="color:gray; font-size:12px;">Sem dados em período anterior</span>'
        except:
            pass
    elif ano_sel == "TODOS":
        texto_crescimento = '<span style="color:gray; font-size:12px;">Visualizando histórico consolidado</span>'

    st.markdown("---")

    # --- BLOCO DE METRICAS / KPIS ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f"""
            <div class="kpi-container">
                <b>🎯 META SEMESTRAL ({ano_sel})</b>
                <h2>{total_meta:,.0f}</h2>
                <span style="color:gray; font-size:12px;">Procedimentos planejados</span>
            </div>
        """, unsafe_allow_html=True)
        
    with kpi2:
        st.markdown(f"""
            <div class="kpi-container" style="border-left-color: #299947;">
                <b>✅ REALIZADO ({ano_sel})</b>
                <h2>{total_realizado:,.0f}</h2>
                {texto_crescimento}
            </div>
        """, unsafe_allow_html=True)
        
    with kpi3:
        cor_status = "#299947" if perc_total >= 100 else "#004a87"
        st.markdown(f"""
            <div class="kpi-container" style="border-left-color: {cor_status};">
                <b>📈 EFICIÊNCIA ({ano_sel})</b>
                <h2>{perc_total:.1f}%</h2>
                <span style="color:gray; font-size:12px;">Aproveitamento da meta</span>
            </div>
        """, unsafe_allow_html=True)

    with kpi4:
        st.markdown(f"""
            <div class="kpi-container" style="border-left-color: #ff9800;">
                <b>👥 TOTAL DE ALUNOS ({ano_sel})</b>
                <h2>{total_alunos:,.0f}</h2>
                <span style="color:gray; font-size:12px;">Alunos alocados no período</span>
            </div>
        """, unsafe_allow_html=True)
  
    # --- BLOCO: COMPARATIVO ENTRE ANOS LETIVOS ---
    st.markdown('<h3 style="color:#004a87;">📊 Comparativo entre Anos Letivos</h3>', unsafe_allow_html=True)
    
    df_comp = df_unidade.groupby([COL_CLINICA, COL_ANO])['TOTAL_REALIZADO_LINHA'].sum().reset_index()
    anos_historico = sorted(df_comp[COL_ANO].unique().tolist())
    
    fig_comp = go.Figure()
    paleta_cores = ['#004a87', '#299947', '#ff9800', '#9c27b0']
    
    for idx, ano in enumerate(anos_historico):
        df_ano_atual = df_comp[df_comp[COL_ANO] == ano]
        fig_comp.add_trace(go.Bar(
            name=f"Realizado {ano}",
            x=df_ano_atual[COL_CLINICA],
            y=df_ano_atual['TOTAL_REALIZADO_LINHA'],
            marker_color=paleta_cores[idx % len(paleta_cores)],
            text=df_ano_atual['TOTAL_REALIZADO_LINHA'],
            textposition='auto'
        ))
        
    fig_comp.update_layout(
        barmode='group',
        height=320,
        margin=dict(t=20, b=20),
        legend=dict(orientation="h", y=1.1, x=0)
    )
    st.plotly_chart(fig_comp, use_container_width=True)
    
    st.markdown("---")

   # --- SEÇÃO DE CORRELAÇÃO ATENDIMENTOS VS ALUNOS (OTIMIZADO) ---
    if COL_ALUNOS in df_filtrado.columns:
        st.markdown('<h3 style="color:#004a87;">🔄 Correlação: Atendimentos vs Quantidade de Alunos</h3>', unsafe_allow_html=True)
        
        df_corr_base = df_filtrado.copy()
        if clinica_sel != "TODAS":
            df_corr_base = df_corr_base[df_corr_base[COL_CLINICA] == clinica_sel]
            
        df_corr = df_corr_base.groupby(COL_CLINICA).agg({
            COL_ALUNOS: 'sum',
            'TOTAL_REALIZADO_LINHA': 'sum'
        }).reset_index()
        
        # Ordenar por volume de atendimentos para deixar o gráfico mais harmônico
        df_corr = df_corr.sort_values(by='TOTAL_REALIZADO_LINHA', ascending=False)
        
        fig_corr = go.Figure()
        
        # 1. Procedimentos Realizados continuam em BARRA (Eixo Y Esquerdo)
        fig_corr.add_trace(go.Bar(
            name="Procedimentos Realizados",
            x=df_corr[COL_CLINICA],
            y=df_corr['TOTAL_REALIZADO_LINHA'],
            marker_color='#004a87',
            text=df_corr['TOTAL_REALIZADO_LINHA'],
            textposition='outside', # Texto fora da barra para não sumir
            cliponaxis=False
        ))
        
        # 2. MELHORIA CRUCIAL: Quantidade de Alunos vira LINHA COM MARCADORES (Eixo Y Direito)
        fig_corr.add_trace(go.Scatter(
            name="Quantidade de Alunos",
            x=df_corr[COL_CLINICA],
            y=df_corr[COL_ALUNOS],
            marker=dict(size=10, color='#ff9800', symbol='circle'),
            line=dict(width=3, color='#ff9800'),
            yaxis='y2',
            text=df_corr[COL_ALUNOS],
            mode='lines+markers+text',
            textposition='top center' # Texto acima do ponto da linha
        ))

        # Ajustes finos de layout para evitar sobreposições
        fig_corr.update_layout(
            height=420,
            margin=dict(t=50, b=20, l=10, r=10),
            legend=dict(orientation="h", y=1.15, x=0),
            hovermode="x unified", # Mostra os dois dados ao passar o mouse verticalmente
            yaxis=dict(
                title=dict(text="Procedimentos Realizados", font=dict(color="#004a87")), 
                tickfont=dict(color="#004a87"),
                gridcolor="#e9ecef" # Linhas de grade suaves ao fundo
            ),
            yaxis2=dict(
                title=dict(text="Quantidade de Alunos", font=dict(color="#ff9800")), 
                tickfont=dict(color="#ff9800"), 
                overlaying='y', 
                side='right',
                showgrid=False # Desativa a segunda grade para não confundir a leitura
            )
        )
        st.plotly_chart(fig_corr, use_container_width=True)
        st.markdown("---")

    # --- SEÇÃO DO ANO ATUAL (GRÁFICOS COMPLEMENTARES) ---
    st.markdown(f'<h3 style="color:#004a87;">📈 Visão Detalhada do Período ({ano_sel})</h3>', unsafe_allow_html=True)
    c_donut, c_bar = st.columns([1, 2])

    with c_donut:
        valores_donut = [total_realizado, falta]
        if sum(valores_donut) == 0:
            valores_donut = [0, 1]
            
        fig_donut = go.Figure(data=[go.Pie(
            labels=['Realizado', 'Restante'],
            values=valores_donut,
            hole=.75,
            marker_colors=['#299947' if perc_total >= 100 else '#004a87', '#f1f3f5'],
            textinfo='none'
        )])
        fig_donut.update_layout(
            annotations=[dict(text=f'Alcançado<br><b>{perc_total:.0f}%</b>', x=0.5, y=0.5, font_size=18, showarrow=False, font_color="#333")],
            showlegend=True, legend=dict(orientation="h", x=0.1, y=-0.1), height=350, margin=dict(t=10, b=10, l=10, r=10)
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with c_bar:
        df_resumo_base = df_filtrado.copy()
        if clinica_sel != "TODAS":
            df_resumo_base = df_resumo_base[df_resumo_base[COL_CLINICA] == clinica_sel]
            
        resumo = df_resumo_base.groupby(COL_CLINICA).agg({
            COL_META: 'sum',
            'TOTAL_REALIZADO_LINHA': 'sum',
            **({COL_ALUNOS: 'sum'} if COL_ALUNOS in df_resumo_base.columns else {})
        }).reset_index().rename(columns={'TOTAL_REALIZADO_LINHA': 'REALIZADO'})
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name='Realizado Atual', x=resumo[COL_CLINICA], y=resumo['REALIZADO'], marker_color='#299947', text=resumo['REALIZADO'], textposition='auto'))
        fig_bar.add_trace(go.Bar(name='Meta do Ano', x=resumo[COL_CLINICA], y=resumo[COL_META], marker_color='#004a87', text=resumo[COL_META], textposition='auto'))
        fig_bar.update_layout(barmode='group', height=350, margin=dict(t=20, b=20), legend=dict(orientation="h", y=1.1, x=0))
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- DETALHAMENTO EM CARDS ---
    st.markdown('<h3 style="color:#004a87; margin-top:30px;">📋 Detalhes Individuais por Curso</h3>', unsafe_allow_html=True)
    cols = st.columns(3)
    
    for i, (_, row) in enumerate(resumo.iterrows()):
        p_ind = (row['REALIZADO'] / row[COL_META] * 100) if row[COL_META] > 0 else 0
        aluno_txt = f"Alunos: <b>{int(row[COL_ALUNOS])}</b>" if COL_ALUNOS in row else ""
        media_atend_aluno = (row['REALIZADO'] / row[COL_ALUNOS]) if COL_ALUNOS in row and row[COL_ALUNOS] > 0 else 0
        
        with cols[i % 3]:
            st.markdown(f"""
            <div class="metric-card">
                <span style="font-size: 16px; font-weight: bold; color: #333;">{row[COL_CLINICA]}</span>
                <hr style="margin: 8px 0; border: 0; border-top: 1px solid #eee;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="color: gray;">Realizado: <b>{int(row['REALIZADO'])}</b></span>
                    <span style="color: gray;">Meta: <b>{int(row[COL_META])}</b></span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 13px;">
                    <span style="color: #ff9800;">{aluno_txt}</span>
                    <span style="color: #004a87;">Média/Aluno: <b>{media_atend_aluno:.1f}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(min(p_ind/100, 1.0))
            st.caption(f"Aproveitamento: {p_ind:.1f}% da meta")
else:
    st.warning("Nenhum dado pôde ser carregado. Certifique-se de que a planilha está aberta para 'Qualquer pessoa com o link'.")
